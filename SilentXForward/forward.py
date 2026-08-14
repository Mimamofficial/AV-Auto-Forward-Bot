import asyncio
import logging
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError, ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid
from SilentXForward import database
from SilentXForward import caption as caption_engine
import config as cfg

# ================= CONFIG =================
BUFFER_DELAY    = 3      # Wait 3s after LAST message before forwarding
QUEUE_WORKERS   = 3
TARGET_CONCURRENCY = 3
MSG_DELAY       = 0.1
TARGET_DELAY    = 0.15
MAX_RETRIES     = 3
# ==========================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

message_queue  = asyncio.Queue()
message_buffer = defaultdict(list)
buffer_tasks   = {}
buffer_timers  = {}   # ✅ NEW: tracks last message time per chat

# Dedup tracker
seen_message_ids: dict[int, set] = defaultdict(set)

# ✅ FIX: ek hi glitch pe mapping delete nahi hogi ab — sirf itni baar
# LAGATAAR real failure hone ke baad hi target DB se remove hoga.
_invalid_target_strikes: dict[int, int] = defaultdict(int)
STRIKE_LIMIT = 5

# ✅ FIX: (writer_id, chat_id) pairs jinka peer already resolve ho chuka hai —
# taaki har message pe dobara resolve na karna pade.
_resolved_peers: set[tuple[int, int]] = set()

_bot_client = None

# ==================== USERBOT REGISTRY ====================
active_userbots: dict[int, Client] = {}


def _is_duplicate(chat_id: int, message_id: int) -> bool:
    if message_id in seen_message_ids[chat_id]:
        return True
    seen_message_ids[chat_id].add(message_id)
    if len(seen_message_ids[chat_id]) > 500:
        seen_message_ids[chat_id] = set(list(seen_message_ids[chat_id])[-500:])
    return False


async def start_single_userbot(user_id: int, session_string: str) -> Client:
    old = active_userbots.get(user_id)
    if old:
        try:
            await old.stop()
        except Exception:
            pass

    ub = Client(
        name=f"ub_{user_id}",
        api_id=cfg.API_ID,
        api_hash=cfg.API_HASH,
        session_string=session_string,
        in_memory=True,
        no_updates=False,
    )
    await ub.start()
    active_userbots[user_id] = ub
    _register_userbot_handler(ub, user_id)

    me = await ub.get_me()
    logger.info(f"✅ Userbot started: user_id={user_id} → @{me.username} ({me.first_name})")

    # ✅ FIX: session in_memory=True hai, isliye restart/redeploy pe Pyrogram ka
    # peer cache (access_hash waghera) khaali ho jaata hai. Agar forwarding
    # turant shuru ho gayi (target ka peer resolve hone se pehle), Pyrogram
    # false ChannelInvalid/PeerIdInvalid de deta tha aur mapping galti se DB
    # se delete ho jaati thi. Start hote hi dialogs load karke cache warm karo.
    try:
        async for _ in ub.get_dialogs():
            pass
        logger.info(f"✅ Peer cache warmed for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Dialog warm-up failed for user_id={user_id}: {e}")

    return ub


def _register_userbot_handler(ub: Client, user_id: int):
    @ub.on_message(
        filters.channel &
        (filters.video | filters.document | filters.photo |
         filters.audio | filters.animation | filters.text |
         filters.sticker | filters.voice | filters.video_note |
         filters.poll | filters.location | filters.contact)
    )
    async def userbot_forward_content(client, message):
        try:
            cid = message.chat.id
            if _is_duplicate(cid, message.id):
                return

            # ✅ FIX: bot-side handler jaisa hi _handle_incoming_message use karo,
            # taaki buffer_timers bhi update ho (pehle yeh missing tha — isliye
            # userbot se aane wale bulk/album forwards debounce wait ke bina
            # jaldi cut ho jaate the aur messages skip ho sakte the).
            _handle_incoming_message(cid, message, source_client=client)
        except Exception:
            logger.exception(f"Userbot handler error for user {user_id}")

    logger.info(f"✅ Userbot handler registered for user_id={user_id}")


async def restore_all_userbots():
    sessions = await database.get_all_userbot_sessions()
    logger.info(f"Restoring {len(sessions)} userbot session(s)...")
    for doc in sessions:
        uid = doc.get("user_id")
        ss  = doc.get("session_string")
        if not uid or not ss:
            continue
        try:
            await start_single_userbot(uid, ss)
        except Exception as e:
            logger.error(f"Failed to restore userbot for user {uid}: {e}")
    logger.info(f"✅ Userbots restored: {len(active_userbots)}")


async def stop_all_userbots():
    for uid, ub in list(active_userbots.items()):
        try:
            await ub.stop()
        except Exception as e:
            logger.warning(f"Error stopping userbot {uid}: {e}")
    active_userbots.clear()


# ================= FLOOD HANDLER =================
async def handle_flood(func, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            return await func(**kwargs)
        except FloodWait as e:
            logger.warning(f"FloodWait: sleeping {e.value}s")
            await asyncio.sleep(e.value + 1)
        except (ChannelInvalid, ChannelPrivate, ChatAdminRequired):
            # ✅ Retry se koi fayda nahi — seedha raise karo
            raise
        except RPCError as e:
            logger.error(f"RPCError: {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.exception(f"Unexpected error in RPC call: {e}")
            await asyncio.sleep(2 ** attempt)
    raise Exception("Max retries exceeded in handle_flood")


def _content_type_allowed(msg, content_filters: dict) -> bool:
    """
    ✅ NEW: 'Custom Filters' — content-type ke hisaab se allow/block.
    Jo type disabled hai (toggle OFF), uska message forward nahi hoga.
    Jin types ka koi toggle nahi hai (poll, location, contact, voice,
    video_note, animation) — woh hamesha allowed rahenge.
    """
    if getattr(msg, "sticker", None):
        return content_filters.get("sticker", True)
    if getattr(msg, "document", None):
        return content_filters.get("document", True)
    if getattr(msg, "video", None):
        return content_filters.get("video", True)
    if getattr(msg, "photo", None):
        return content_filters.get("photo", True)
    if getattr(msg, "audio", None):
        return content_filters.get("audio", True)
    if getattr(msg, "text", None):
        return content_filters.get("text", True)
    return True


async def _ensure_peer_resolved(writer, chat_id: int) -> bool:
    """
    ✅ FIX: copy_message se pehle target ka peer resolve/cache karo. Isse
    false ChannelInvalid/PeerIdInvalid errors rukte hain jo sirf isliye aate
    hain kyunki userbot ne abhi tak us chat ko "dekha" nahi (khaaskar
    restart ke turant baad, kyunki session in_memory hai).
    """
    key = (id(writer), chat_id)
    if key in _resolved_peers:
        return True
    try:
        await writer.get_chat(chat_id)
        _resolved_peers.add(key)
        return True
    except PeerIdInvalid:
        try:
            async for dialog in writer.get_dialogs():
                if dialog.chat.id == chat_id:
                    _resolved_peers.add(key)
                    return True
        except Exception as e:
            logger.warning(f"Dialog scan failed while resolving {chat_id}: {e}")
        return False
    except Exception as e:
        logger.warning(f"get_chat failed while resolving {chat_id}: {e}")
        return False


# ================= SINGLE FORWARD =================
async def forward_single_message(client, message, chat_id, sender_client=None, caption_settings: dict = None):
    writer = sender_client if sender_client else client
    try:
        # ✅ FIX: forward karne se pehle peer resolve karo
        await _ensure_peer_resolved(writer, chat_id)

        cs = caption_settings or {}

        # ✅ NEW: "Forward tag" ON hai toh asli forward karo ("Forwarded From"
        # tag ke saath) — is mode mein caption customization possible nahi
        # hai (Telegram forward_messages caption change allow nahi karta),
        # isliye seedha original message forward ho jaata hai.
        if cs.get("forward_tag"):
            await handle_flood(
                writer.forward_messages,
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_ids=message.id,
            )
            _invalid_target_strikes.pop(chat_id, None)
            return True

        has_customization = bool(
            cs.get("caption_template") or cs.get("endtext") or
            cs.get("replace_rules") or cs.get("remove_words")
        )

        final_caption = None
        if has_customization:
            try:
                final_caption = caption_engine.build_final_caption(
                    message,
                    caption_template=cs.get("caption_template", ""),
                    endtext=cs.get("endtext", ""),
                    replace_rules=cs.get("replace_rules"),
                    remove_words=cs.get("remove_words"),
                )
            except Exception:
                logger.exception("Caption engine failed, falling back to original caption")
                final_caption = None

        if final_caption:
            await handle_flood(
                writer.copy_message,
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=final_caption,
            )
        else:
            await handle_flood(
                writer.copy_message,
                chat_id=chat_id,
                from_chat_id=message.chat.id,
                message_id=message.id,
            )
        _invalid_target_strikes.pop(chat_id, None)
        return True

    except PeerIdInvalid as e:
        # ✅ FIX: yeh zyadatar TRANSIENT hota hai (peer cache miss, khaaskar
        # restart ke baad) — mapping delete NAHI karna, bas is baar skip karo,
        # agli baar peer resolve ho jaayega aur forward chalne lagega.
        logger.warning(f"PeerIdInvalid for {chat_id} (transient, mapping safe): {e}")
        return False

    except (ChannelInvalid, ChannelPrivate) as e:
        # ✅ FIX: ek hi baar fail hone pe turant delete nahi karte — pehle bot
        # client se fallback try karo, phir strike count badhao. Sirf
        # STRIKE_LIMIT baar LAGATAAR real failure hone ke baad hi target DB
        # se remove hoga — isse ek transient glitch pe mapping gayab nahi hogi.
        logger.warning(f"Channel invalid/private for {chat_id}: {e}")
        if sender_client and sender_client != client:
            try:
                await handle_flood(
                    client.copy_message,
                    chat_id=chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                )
                _invalid_target_strikes.pop(chat_id, None)
                return True
            except Exception:
                pass

        _invalid_target_strikes[chat_id] += 1
        if _invalid_target_strikes[chat_id] >= STRIKE_LIMIT:
            logger.warning(f"{chat_id} failed {STRIKE_LIMIT}x lagataar — ab DB se remove kar rahe hain.")
            try:
                await database.remove_invalid_target(chat_id)
            except Exception as db_err:
                logger.error(f"DB cleanup failed for {chat_id}: {db_err}")
            _invalid_target_strikes.pop(chat_id, None)
        return False

    except ChatAdminRequired as e:
        # Bot admin nahi — log karo, retry mat karo
        logger.warning(f"Bot not admin in {chat_id}: {e}")
        return False

    except Exception:
        logger.exception(f"Forward failed msg_id={getattr(message, 'id', None)} -> {chat_id}")
        if sender_client and sender_client != client:
            try:
                await handle_flood(
                    client.copy_message,
                    chat_id=chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                )
                return True
            except Exception:
                logger.exception(f"Bot fallback also failed -> {chat_id}")
        return False


# ================= BUFFER FORWARD =================
async def forward_buffered_messages(client, messages, chat_id, sender_client=None,
                                     msg_delay: float = MSG_DELAY, caption_settings: dict = None):
    success = 0
    for msg in sorted(messages, key=lambda m: m.id):
        try:
            ok = await forward_single_message(client, msg, chat_id,
                                              sender_client=sender_client,
                                              caption_settings=caption_settings)
            if ok:
                success += 1
        except Exception:
            logger.exception(f"Error forwarding buffered msg -> {chat_id}")
        await asyncio.sleep(msg_delay)
    return success


# ================= QUEUE WORKER =================
async def process_queue(client):
    from SilentXForward.logger import log_forward_success, log_forward_failed

    sem = asyncio.Semaphore(TARGET_CONCURRENCY)

    async def forward_target(chat_id, payload, ftype, sender_client, msg_delay, caption_settings):
        async with sem:
            if ftype == "buffered":
                return await forward_buffered_messages(
                    client, payload, chat_id,
                    sender_client=sender_client,
                    msg_delay=msg_delay,
                    caption_settings=caption_settings
                )
            return await forward_single_message(
                client, payload, chat_id,
                sender_client=sender_client,
                caption_settings=caption_settings
            )

    while True:
        try:
            payload, targets, ftype, retry_count, sender_client, source_info = await message_queue.get()

            user_id          = source_info.get("user_id")
            msg_delay        = source_info.get("delay", MSG_DELAY)
            caption_settings = {
                "endtext": source_info.get("endtext", "") or "",
                "caption_template": source_info.get("caption_template", "") or "",
                "replace_rules": source_info.get("replace_rules") or [],
                "remove_words": source_info.get("remove_words") or [],
                "forward_tag": source_info.get("forward_tag", False),
            }
            failed        = []
            succeeded     = []

            tasks = [
                forward_target(tid, payload, ftype, sender_client, msg_delay, caption_settings)
                for tid in targets
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            msg_count    = len(payload) if isinstance(payload, list) else 1
            source_id    = source_info.get("id", 0)
            source_title = source_info.get("title", str(source_id))

            for tid, res in zip(targets, results):
                if isinstance(res, Exception):
                    logger.error(f"Exception forwarding to {tid}: {res}")
                    failed.append((tid, str(res)))
                elif res is False or res == 0:
                    # False = channel invalid ya already handled — retry nahi
                    pass
                else:
                    succeeded.append(tid)

            if succeeded and user_id:
                try:
                    await database.increment_forward_count(user_id, len(succeeded) * msg_count)
                except Exception:
                    pass

            for tid in succeeded:
                try:
                    await log_forward_success(client, source_title, source_id, tid, msg_count)
                except Exception:
                    pass

            if failed:
                failed_tids = [f[0] for f in failed]
                if retry_count < MAX_RETRIES:
                    await message_queue.put((payload, failed_tids, ftype, retry_count + 1,
                                            sender_client, source_info))
                else:
                    for tid, err in failed:
                        try:
                            await log_forward_failed(client, source_id, tid, msg_count, err)
                        except Exception:
                            pass

            message_queue.task_done()
            await asyncio.sleep(TARGET_DELAY)

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected error in queue worker — continuing")
            await asyncio.sleep(1)


# ================= WATCHDOG =================
async def worker_watchdog(client):
    while True:
        try:
            await asyncio.sleep(10)
            tasks = getattr(client, "_queue_tasks", {})
            for key, t in list(tasks.items()):
                if t.done():
                    exc = t.exception() if not t.cancelled() else None
                    logger.warning(f"Worker {key} died (exc={exc}), restarting...")
                    tasks[key] = asyncio.create_task(process_queue(client))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Watchdog error")


# ================= START / STOP =================
async def start_processor(client):
    tasks = {}
    for i in range(QUEUE_WORKERS):
        tasks[f"worker_{i}"] = asyncio.create_task(process_queue(client))
    tasks["watchdog"] = asyncio.create_task(worker_watchdog(client))
    logger.info(f"{QUEUE_WORKERS} queue workers + watchdog started")
    return tasks

async def start_forwarder(client):
    global _bot_client
    _bot_client = client
    if getattr(client, "_queue_tasks", None):
        return
    await restore_all_userbots()
    client._queue_tasks = await start_processor(client)

async def stop_forwarder(client, timeout: float = 5.0):
    tasks = getattr(client, "_queue_tasks", {}) or {}
    for t in tasks.values():
        t.cancel()
    try:
        await asyncio.wait_for(message_queue.join(), timeout=timeout)
    except Exception:
        pass
    await stop_all_userbots()
    client._queue_tasks = {}


# ================= BUFFER PROCESSOR =================
async def process_buffered_messages(source_chat_id, source_client=None):
    """
    ✅ DEBOUNCE FIX:
    Jab tak naye messages aa rahe hain — wait karo.
    Jab BUFFER_DELAY seconds tak koi naya message na aaye
    tabhi saare collected messages forward karo.
    Isse bulk messages mein koi bhi skip nahi hoga.
    """
    try:
        while True:
            await asyncio.sleep(BUFFER_DELAY)
            # Check: last message kitne time pehle aaya?
            last_time = buffer_timers.get(source_chat_id, 0)
            now = asyncio.get_event_loop().time()
            if now - last_time < BUFFER_DELAY:
                # Abhi bhi messages aa rahe hain — aur wait karo
                continue
            # Kaafi der se koi message nahi aaya — ab forward karo
            break

        messages = message_buffer.pop(source_chat_id, None)
        buffer_timers.pop(source_chat_id, None)

        if not messages:
            return

        # Deduplicate by message ID
        seen = set()
        unique_messages = []
        for m in messages:
            if m.id not in seen:
                seen.add(m.id)
                unique_messages.append(m)
        messages = unique_messages

        logger.info(f"Processing {len(messages)} buffered msgs from {source_chat_id}")

        source_title = str(source_chat_id)
        try:
            if source_client:
                chat = await source_client.get_chat(source_chat_id)
                source_title = chat.title or source_title
        except Exception:
            pass

        mappings = await database.get_all_targets_for_source(source_chat_id)
        for mapping in mappings:
            targets = mapping.get("target_ids", [])
            user_id = mapping.get("user_id")
            if not targets:
                continue

            if user_id and not await database.is_forwarding_enabled(user_id):
                logger.info(f"Forwarding OFF for user {user_id}, skipping")
                continue

            user_filters = await database.get_filters(user_id) if user_id else []
            if user_filters:
                filtered_messages = []
                for msg in messages:
                    text = (msg.text or msg.caption or "").lower()
                    if any(w in text for w in user_filters):
                        filtered_messages.append(msg)
                if not filtered_messages:
                    logger.info(f"All messages filtered out for user {user_id}")
                    continue
                messages_to_send = filtered_messages
            else:
                messages_to_send = messages

            # ✅ NEW: Blacklist — in words wale messages skip ho jaayenge
            user_blacklist = await database.get_blacklist(user_id) if user_id else []
            if user_blacklist:
                messages_to_send = [
                    msg for msg in messages_to_send
                    if not any(w in (msg.text or msg.caption or "").lower() for w in user_blacklist)
                ]
                if not messages_to_send:
                    logger.info(f"All messages blacklisted for user {user_id}")
                    continue

            # ✅ NEW: Custom Filters — content-type ke hisaab se allow/block
            content_filters = await database.get_content_filters(user_id) if user_id else database.DEFAULT_CONTENT_FILTERS
            messages_to_send = [msg for msg in messages_to_send if _content_type_allowed(msg, content_filters)]
            if not messages_to_send:
                logger.info(f"All messages blocked by content-type filter for user {user_id}")
                continue

            msg_delay        = await database.get_delay(user_id) if user_id else MSG_DELAY
            endtext          = await database.get_endtext(user_id) if user_id else None
            caption_template = await database.get_caption_template(user_id) if user_id else None
            replace_rules    = await database.get_replacements(user_id) if user_id else []
            remove_words     = await database.get_remove_words(user_id) if user_id else []

            sender = source_client
            if user_id and user_id in active_userbots:
                ub = active_userbots[user_id]
                if ub.is_connected:
                    sender = ub

            source_info = {
                "id": source_chat_id,
                "title": source_title,
                "user_id": user_id,
                "delay": msg_delay,
                "endtext": endtext or "",
                "caption_template": caption_template or "",
                "replace_rules": replace_rules,
                "remove_words": remove_words,
                "forward_tag": content_filters.get("forward_tag", False),
            }

            await message_queue.put((messages_to_send.copy(), targets, "buffered", 0, sender, source_info))
            logger.info(f"Queued {len(messages_to_send)} msgs from {source_chat_id} -> {len(targets)} targets")

    except asyncio.CancelledError:
        # Messages buffer mein safe hain — lost nahi honge
        logger.debug(f"Buffer task cancelled for {source_chat_id}")
        raise
    except Exception:
        logger.exception("Unexpected error in buffer processor")
        message_buffer.pop(source_chat_id, None)
        buffer_timers.pop(source_chat_id, None)
    finally:
        buffer_tasks.pop(source_chat_id, None)


def _handle_incoming_message(cid: int, message, source_client):
    """
    ✅ DEBOUNCE HELPER:
    Har naye message pe:
    1. Buffer mein add karo
    2. Timer update karo (last message time)
    3. Agar task already chal raha hai — rehne do (cancel mat karo!)
    4. Agar task nahi hai ya khatam ho gaya — naya banao
    """
    message_buffer[cid].append(message)
    # Timer update — last message time record karo
    buffer_timers[cid] = asyncio.get_event_loop().time()

    existing_task = buffer_tasks.get(cid)
    if existing_task and not existing_task.done():
        # Task chal raha hai — woh khud debounce loop mein wait karega
        return

    # Naya task banao
    buffer_tasks[cid] = asyncio.create_task(
        process_buffered_messages(cid, source_client=source_client)
    )


# ================= BOT MESSAGE LISTENER =================
@Client.on_message(
    filters.channel &
    (filters.video | filters.document | filters.photo |
     filters.audio | filters.animation | filters.text |
     filters.sticker | filters.voice | filters.video_note |
     filters.poll | filters.location | filters.contact)
)
async def forward_content(client, message):
    try:
        cid = message.chat.id
        if _is_duplicate(cid, message.id):
            return
        _handle_incoming_message(cid, message, source_client=client)
    except Exception:
        logger.exception("Bot handler error")
