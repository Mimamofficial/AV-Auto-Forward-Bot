import asyncio
import logging
from SilentXForward import database
from SilentXForward.fsub import check_fsub, send_fsub_message, fsub_verify_callback
from SilentXForward.logger import (
    log_new_user, log_login, log_logout,
    log_source_added, log_source_removed, log_target_removed
)
from pyrogram import Client, filters, enums, ContinuePropagation
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, PeerIdInvalid,
)
import config as cfg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_IMAGE = "https://files.catbox.moe/oht30s.jpg"

START_TEXT = """<b>🎬 Prime Forward Bot — Now Live!

Auto forward videos & files from any private channel to your channel — without "Forwarded From" tag!

🚀 Premium Auto Forwarder Features 🚀

✨ Session Login → Direct Instant Forward
✨ Without Login → Bot Admin Required
✨ Userbot + Bot Dual Support
✨ Unlimited Source & Target Support
✨ Bulk / Album Auto Forward
✨ Auto FloodWait Protection
✨ No Duplicate Messages
✨ Auto Retry + Auto Recovery
✨ Super Fast & Stable Forwarding
✨ Smooth & Professional System
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
🎯 Get Started:
➤ /login (for private access)
➤ /set source target
➤ Sit back & enjoy automation 😎

🔥 Experience Next Level Forwarding
<blockquote>👨‍💻 Maintained by <a href="https://t.me/Dark_of_Danger">𝄟͢🦋⃟≛⃝ 𝐃𝐚𝐫𝐤 𝐨𝐟 𝐃𝐚𝐧𝐠𝐞𝐫 𝄟⃝❤</a></blockquote></b>
"""

HELP_TEXT = """<b>⭐ Auto Forward Bot (Master Edition) ⭐

🔑 Session:
/login | /logout | /cancel | /session

📡 Forwarding:
/on | /off | /resume | /status

⚙️ Settings:
/setdelay [Sec] | /skip

🔍 Filter:
/addfilter [word] | /remfilter [word] | /listfilters

✅ Whitelist (same as Filter):
/whitelist [word] | /remove_whitelist [word]

🚫 Blacklist (in words wale messages skip honge):
/blacklist [word] | /remove_blacklist [word] | /listblacklist

✍️ Footer:
/endtext [Text] | /remendtext | /listendtext

📝 Caption (variables):
/setcaption [Template] | /showcaption | /delcaption

🔁 Replace Words:
/addreplace Old:New | /remreplace Old | /listreplace | /clearreplace

🧹 Remove Words:
/addremoveword Word | /remremoveword Word | /listremovewords | /clearremovewords

💥 Danger Zone:
/reset — Reset EVERYTHING (Caption, Filters, Words, Footer + Channels)

🖲️ Button Menu:
/settings ya /manage — Sab kuch buttons se manage karo (recommended!)

📊 Management:
/set &lt;source&gt; &lt;target&gt; | /remove_target | /remove_source | /list | /clear

📈 Stats:
/count

👑 Admin:
/addadmin | /ban | /unban | /removeuser</b>

<b>Channel: @Mrn_Officialx</b>
"""

ABOUT_TEXT = """<b><blockquote>╭────[ ᴍʏ ᴅᴇᴛᴀɪʟs ]────⍟</blockquote>
<blockquote>├⍟ 🎭 Mʏ Nᴀᴍᴇ : <a href='https://t.me/Prime_Forwards_Bot'>𝗣𝗿𝗶𝗺𝗲 𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝗕𝗼𝘁</a></blockquote>
<blockquote>├⍟ 🇮🇳 Cʀᴇᴀᴛᴏʀ : <a href='https://t.me/mimam_officialx/'>𝄟͢🦋⃟≛⃝ 𝐌𝐮𝐳𝐚𝐟𝐟𝐚𝐫 𝄟⃝❤</a></blockquote>
<blockquote>├⍟ 📚 Lɪʙʀᴀʀʏ : <a href='https://docs.pyrogram.org/'>ᴘʏʀᴏɢʀᴀᴍ</a></blockquote>
<blockquote>├⍟ 🍿 Lᴀɴɢᴜᴀɢᴇ : <a href='https://www.python.org/download/releases/3.0/'>ᴘʏᴛʜᴏɴ 𝟹</a></blockquote>
<blockquote>├⍟ 🐍 DᴀᴛᴀBᴀsᴇ : <a href='https://www.mongodb.com/'>ᴍᴏɴɢᴏ ᴅʙ</a></blockquote>
<blockquote>├⍟ ⚙️ Bᴏᴛ Sᴇʀᴠᴇʀ : <a href='https://heroku.com/'>ʜᴇʀᴏᴋᴜ</a></blockquote>
<blockquote>├⍟ 🥶 Bᴜɪʟᴅ Sᴛᴀᴛᴜs : ᴠ𝟹.𝟶 [ ꜱᴛᴀʙʟᴇ ]</blockquote>
<blockquote>├⍟ Multi-Source to Multi-Target ✅</blockquote>
<blockquote>├⍟ All Media Types ✅</blockquote>
<blockquote>├⍟ Forwarding ON/OFF ✅</blockquote>
<blockquote>├⍟ Custom Delay ✅</blockquote>
<blockquote>├⍟ Keyword Filter ✅</blockquote>
<blockquote>├⍟ Footer Text ✅</blockquote>
<blockquote>├⍟ Admin System ✅</blockquote>
<blockquote>├⍟ Stats & Count ✅</blockquote>
<blockquote>├⍟ Userbot Login ✅</blockquote>
<blockquote>├⍟ Log Channel ✅</blockquote>
<blockquote>╰───────────────⍟</b></blockquote>"""

BUTTONS = InlineKeyboardMarkup([[
    InlineKeyboardButton("📢 Channel", url="https://t.me/Mrn_Officialx"),
    InlineKeyboardButton("🥰 𝄟͢🦋⃟≛⃝ 𝐌𝐮𝐳𝐚𝐟𝐟𝐚𝐫 𝄟⃝❤", url="https://t.me/mimam_officialx")
]])

login_states = {}


# ==================== OWNER CHECK ====================

def owner_only(func):
    """Decorator — sirf OWNER_ID wala user use kar sakta hai."""
    async def wrapper(client, message: Message):
        if cfg.OWNER_ID and message.from_user.id != cfg.OWNER_ID:
            return await message.reply_text(
                "🚫 <b>Access Denied!</b>\n\nYeh command sirf bot owner use kar sakta hai.",
                parse_mode=enums.ParseMode.HTML
            )
        return await func(client, message)
    wrapper.__name__ = func.__name__
    return wrapper


def admin_only(func):
    """Decorator — OWNER_ID ya /addadmin se add kiya gaya admin, dono use kar sakte hain."""
    async def wrapper(client, message: Message):
        user_id  = message.from_user.id
        is_owner = bool(cfg.OWNER_ID) and user_id == cfg.OWNER_ID
        allowed  = is_owner
        if not allowed and cfg.OWNER_ID:
            try:
                allowed = await database.is_admin(cfg.OWNER_ID, user_id)
            except Exception:
                logger.exception("admin_only: is_admin check failed")
                allowed = False
        if not allowed:
            return await message.reply_text(
                "🚫 <b>Access Denied!</b>\n\nYeh command sirf bot owner ya admin use kar sakta hai.",
                parse_mode=enums.ParseMode.HTML
            )
        return await func(client, message)
    wrapper.__name__ = func.__name__
    return wrapper


# ==================== GLOBAL BAN CHECK ====================
# Banned user ka koi bhi private message/command yahin rok diya jaata hai,
# taaki /ban se banaya gaya ban actually kaam kare.

@Client.on_message(filters.private, group=-1)
async def global_ban_check(client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if cfg.OWNER_ID and user_id == cfg.OWNER_ID:
        return
    try:
        # ✅ Opportunistically record every interacting user — covers users who
        # started the bot before this fix and never sent /start again.
        await database.save_user(user_id)
    except Exception:
        pass
    try:
        banned = await database.is_banned(cfg.OWNER_ID, user_id)
    except Exception:
        logger.exception("global_ban_check: is_banned lookup failed")
        banned = False
    if banned:
        try:
            await message.reply_text(
                "🚫 <b>You are banned from using this bot.</b>\n\n"
                "Agar lagta hai yeh galti hai to bot owner se contact karo.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
        message.stop_propagation()


# ==================== HELPERS ====================

async def smart_get_chat(client, chat_id, user_id):
    from SilentXForward.forward import active_userbots
    ub = active_userbots.get(user_id)
    if ub and ub.is_connected:
        try:
            return await ub.get_chat(chat_id)
        except PeerIdInvalid:
            logger.info(f"PeerIdInvalid for {chat_id} — trying dialogs...")
            try:
                async for dialog in ub.get_dialogs():
                    if dialog.chat.id == int(chat_id):
                        return dialog.chat
            except Exception as e:
                logger.warning(f"Dialog iteration failed: {e}")
            try:
                return await ub.get_chat(chat_id)
            except Exception as e:
                logger.warning(f"Userbot still can't get {chat_id}: {e}")
        except Exception as e:
            logger.warning(f"Userbot get_chat failed ({chat_id}): {e}")
    return await client.get_chat(chat_id)


# ==================== START / HELP / ABOUT ====================

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        # ── Force Subscribe Check ──
        not_joined = await check_fsub(client, message.from_user.id)
        if not_joined:
            return await send_fsub_message(client, message, not_joined)

        await database.save_user(message.from_user.id)  # ✅ FIX: broadcast list ke liye har user record karo
        await log_new_user(client, message.from_user)
        await message.reply_photo(photo=START_IMAGE, caption=START_TEXT,
                                  parse_mode=enums.ParseMode.HTML, reply_markup=BUTTONS)
    except Exception as e:
        logger.error(f"Start error: {e}")
        try:
            await message.reply(text=START_TEXT, parse_mode=enums.ParseMode.HTML,
                                reply_markup=BUTTONS, disable_web_page_preview=True)
        except Exception:
            pass


# ── Force Subscribe Verify Callback ──────────────────────────────────────────
@Client.on_callback_query(filters.regex("^fsub_verify$"))
async def fsub_verify(client, callback_query):
    await fsub_verify_callback(client, callback_query)

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply(text=HELP_TEXT, parse_mode=enums.ParseMode.HTML,
                        reply_markup=BUTTONS, disable_web_page_preview=True)

@Client.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    await message.reply(text=ABOUT_TEXT, parse_mode=enums.ParseMode.HTML,
                        reply_markup=BUTTONS, disable_web_page_preview=True)


# ==================== FORWARDING ON / OFF / RESUME ====================

@Client.on_message(filters.command("off") & filters.private)
async def cmd_off(client, message: Message):
    await database.set_forwarding(message.from_user.id, False)
    await message.reply_text("⏸️ <b>Forwarding paused!</b>\n\nResume karne ke liye /on ya /resume use karo.",
                             parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command(["on", "resume"]) & filters.private)
async def cmd_on(client, message: Message):
    await database.set_forwarding(message.from_user.id, True)
    await message.reply_text("▶️ <b>Forwarding resumed!</b>\n\nMessages ab forward honge.",
                             parse_mode=enums.ParseMode.HTML)


# ==================== STATUS ====================

async def _build_status_text(user_id: int) -> str:
    settings = await database.get_all_settings(user_id)
    mappings = await database.get_user_mappings(user_id)
    count    = await database.get_forward_count(user_id)
    fwd_on   = settings.get("forwarding_enabled", True)
    delay    = settings.get("delay", 0.1)
    endtext  = settings.get("endtext", "Not set")
    fil_list = settings.get("filters", [])
    cap_tpl  = settings.get("caption_template")
    repl_cnt = len(settings.get("replacements", []))
    rmw_cnt  = len(settings.get("remove_words", []))

    from SilentXForward.forward import active_userbots
    ub = active_userbots.get(user_id)
    session_status = "🟢 Active" if (ub and ub.is_connected) else "🔴 Not logged in"

    return (
        f"<b>📊 Status Dashboard</b>\n\n"
        f"👤 Session: {session_status}\n"
        f"📡 Forwarding: {'▶️ ON' if fwd_on else '⏸️ OFF'}\n"
        f"⏱️ Delay: <code>{delay}s</code>\n"
        f"📊 Total Forwarded: <b>{count}</b>\n"
        f"🗂️ Sources: <b>{len(mappings)}</b>\n"
        f"🔍 Filters: <b>{len(fil_list)}</b> {('— ' + ', '.join(fil_list)) if fil_list else ''}\n"
        f"✍️ Footer: <code>{endtext[:50] if endtext != 'Not set' else 'Not set'}</code>\n"
        f"📝 Caption Template: {'✅ Set' if cap_tpl else '❌ Not set'}\n"
        f"🔁 Replace Rules: <b>{repl_cnt}</b>\n"
        f"🧹 Remove Words: <b>{rmw_cnt}</b>"
    )

@Client.on_message(filters.command("status") & filters.private)
async def cmd_status(client, message: Message):
    text = await _build_status_text(message.from_user.id)
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ==================== SETDELAY ====================

@Client.on_message(filters.command("setdelay") & filters.private)
async def cmd_setdelay(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/setdelay 2</code>\n\nDelay in seconds (0.1 to 60)",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        delay = float(message.command[1])
        if delay < 0 or delay > 60:
            raise ValueError
        await database.set_delay(message.from_user.id, delay)
        await message.reply_text(
            f"⏱️ <b>Delay set to {delay}s!</b>\n\nAb har message ke baad {delay} second wait hoga.",
            parse_mode=enums.ParseMode.HTML
        )
    except ValueError:
        await message.reply_text("<b>❌ Valid number do (0.1 - 60)</b>", parse_mode=enums.ParseMode.HTML)


# ==================== SKIP (manual skip — clears buffer) ====================

@Client.on_message(filters.command("skip") & filters.private)
async def cmd_skip(client, message: Message):
    from SilentXForward.forward import message_buffer, buffer_tasks
    cleared = 0
    for cid in list(message_buffer.keys()):
        message_buffer[cid].clear()
        cleared += 1
        t = buffer_tasks.get(cid)
        if t and not t.done():
            t.cancel()
    await message.reply_text(
        f"⏭️ <b>Skipped!</b> {cleared} pending buffer(s) cleared.",
        parse_mode=enums.ParseMode.HTML
    )


# ==================== FILTERS ====================

@Client.on_message(filters.command("addfilter") & filters.private)
async def cmd_addfilter(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/addfilter word</code>\n\nSirf wahi messages forward honge jisme yeh word ho.",
            parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    added = await database.add_filter(message.from_user.id, word)
    if added:
        await message.reply_text(f"✅ <b>Filter added:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Already exists:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remfilter") & filters.private)
async def cmd_remfilter(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remfilter word</code>", parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    removed = await database.remove_filter(message.from_user.id, word)
    if removed:
        await message.reply_text(f"🗑️ <b>Filter removed:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Not found:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("listfilters") & filters.private)
async def cmd_listfilters(client, message: Message):
    fil_list = await database.get_filters(message.from_user.id)
    if not fil_list:
        return await message.reply_text("🔍 <b>No filters set.</b>\n\nUse /addfilter to add one.",
                                        parse_mode=enums.ParseMode.HTML)
    text = "<b>🔍 Active Filters:</b>\n\n"
    for i, w in enumerate(fil_list, 1):
        text += f"{i}. <code>{w}</code>\n"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ==================== WHITELIST (alias of Filters) ====================
# ✅ NEW: /whitelist == /addfilter — sirf naam alag hai, kaam wahi hai
# (sirf wahi messages forward honge jinme yeh word ho).

@Client.on_message(filters.command("whitelist") & filters.private)
async def cmd_whitelist(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/whitelist word</code>\n\nSirf wahi messages forward honge jisme yeh word ho.",
            parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    added = await database.add_filter(message.from_user.id, word)
    if added:
        await message.reply_text(f"✅ <b>Whitelist word added:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Already exists:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remove_whitelist") & filters.private)
async def cmd_remove_whitelist(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_whitelist word</code>", parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    removed = await database.remove_filter(message.from_user.id, word)
    if removed:
        await message.reply_text(f"🗑️ <b>Whitelist word removed:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Not found:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)


# ==================== BLACKLIST (opposite of Whitelist) ====================
# ✅ NEW: in words wale messages SKIP ho jaayenge (forward nahi honge).

@Client.on_message(filters.command("blacklist") & filters.private)
async def cmd_blacklist(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/blacklist word</code>\n\nYeh word jis message mein hoga, woh forward nahi hoga.",
            parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    added = await database.add_blacklist_word(message.from_user.id, word)
    if added:
        await message.reply_text(f"✅ <b>Blacklist word added:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Already exists:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remove_blacklist") & filters.private)
async def cmd_remove_blacklist(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_blacklist word</code>", parse_mode=enums.ParseMode.HTML
        )
    word = " ".join(message.command[1:]).lower().strip()
    removed = await database.remove_blacklist_word(message.from_user.id, word)
    if removed:
        await message.reply_text(f"🗑️ <b>Blacklist word removed:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(f"⚠️ <b>Not found:</b> <code>{word}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("listblacklist") & filters.private)
async def cmd_listblacklist(client, message: Message):
    bl = await database.get_blacklist(message.from_user.id)
    if not bl:
        return await message.reply_text("🚫 <b>No blacklist words set.</b>\n\nUse /blacklist to add one.",
                                        parse_mode=enums.ParseMode.HTML)
    text = "<b>🚫 Blacklist Words:</b>\n\n"
    for i, w in enumerate(bl, 1):
        text += f"{i}. <code>{w}</code>\n"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ==================== END TEXT / FOOTER ====================

@Client.on_message(filters.command("endtext") & filters.private)
async def cmd_endtext(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/endtext Your footer text here</code>",
            parse_mode=enums.ParseMode.HTML
        )
    text = message.text.split(None, 1)[1]
    await database.set_endtext(message.from_user.id, text)
    await message.reply_text(
        f"✍️ <b>Footer set:</b>\n<code>{text}</code>",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("remendtext") & filters.private)
async def cmd_remendtext(client, message: Message):
    await database.remove_endtext(message.from_user.id)
    await message.reply_text("🗑️ <b>Footer removed!</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("listendtext") & filters.private)
async def cmd_listendtext(client, message: Message):
    endtext = await database.get_endtext(message.from_user.id)
    if not endtext:
        return await message.reply_text("✍️ <b>No footer set.</b>\n\nUse /endtext to add one.",
                                        parse_mode=enums.ParseMode.HTML)
    await message.reply_text(f"✍️ <b>Current Footer:</b>\n\n<code>{endtext}</code>",
                             parse_mode=enums.ParseMode.HTML)


# ==================== CUSTOM CAPTION (variables) ====================

CAPTION_VARS_TEXT = (
    "<b>📝 Caption Settings</b>\n\n"
    "Set your custom caption using variables below.\n\n"
    "<b>📚 Variables:</b>\n"
    "<code>{file_name}</code> - Original filename\n"
    "<code>{default_caption}</code> - Original caption\n"
    "<code>{title}</code> - Title (before Year/Season/Quality)\n"
    "<code>{file_size}</code> - File size\n"
    "<code>{duration}</code> - Video duration\n"
    "<code>{language}</code> - Language from caption\n"
    "<code>{audio}</code> - Audio type (DDP5.1, AAC2.0)\n"
    "<code>{quality}</code> - Quality (HdRip, BluRay)\n"
    "<code>{resolution}</code> - Res (480p, 1080p)\n"
    "<code>{year}</code> - Year from caption\n"
    "<code>{season}</code> - Season (S01, S02)\n"
    "<code>{episode}</code> - Episode (E01, E02)\n"
    "<code>{ott}</code> - OTT (NF, AMZN)\n"
    "<code>{lib}</code> - Codec (x264, x265)\n"
    "<code>{extension}</code> - File ext\n"
    "<code>{fps}</code> - FPS (30FPS, 60FPS)\n"
    "<code>{bitrate}</code> - Audio bitrate\n"
    "<code>{shortsub}</code> - Sub (Msub/Esub)\n"
    "<code>{height}</code> - Video height\n"
    "<code>{width}</code> - Video width\n\n"
    "<b>Usage:</b> <code>/setcaption &lt;b&gt;{title}&lt;/b&gt; [{year}] {resolution}</code>"
)

@Client.on_message(filters.command("setcaption") & filters.private)
async def cmd_setcaption(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(CAPTION_VARS_TEXT, parse_mode=enums.ParseMode.HTML)
    template = message.text.split(None, 1)[1]
    await database.set_caption_template(message.from_user.id, template)
    await message.reply_text(
        f"✅ <b>Caption template set!</b>\n\n<code>{template}</code>\n\n"
        f"Ab is caption ke saath forwarding hogi.",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("showcaption") & filters.private)
async def cmd_showcaption(client, message: Message):
    template = await database.get_caption_template(message.from_user.id)
    if not template:
        return await message.reply_text(
            "📝 <b>No caption template set.</b>\n\nUse /setcaption to add one.",
            parse_mode=enums.ParseMode.HTML
        )
    await message.reply_text(f"📝 <b>Current Caption Template:</b>\n\n<code>{template}</code>",
                             parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("delcaption") & filters.private)
async def cmd_delcaption(client, message: Message):
    await database.remove_caption_template(message.from_user.id)
    await message.reply_text("🗑️ <b>Caption template removed!</b>\n\nDefault caption use hogi ab.",
                             parse_mode=enums.ParseMode.HTML)


# ==================== WORD REPLACE ====================

@Client.on_message(filters.command("addreplace") & filters.private)
async def cmd_addreplace(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🔁 Send Replacements</b>\n\n"
            "<b>Format:</b> <code>Old:New | Old2:New2</code>\n"
            "<b>Example:</b> <code>Day:Night | You:Me</code>\n\n"
            "Use | to add multiple rules.",
            parse_mode=enums.ParseMode.HTML
        )
    raw = message.text.split(None, 1)[1]
    rules = []
    bad = []
    for part in raw.split("|"):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            bad.append(part)
            continue
        old, new = part.split(":", 1)
        rules.append((old.strip(), new.strip()))
    if not rules:
        return await message.reply_text(
            "<b>❌ Valid format do:</b> <code>Old:New | Old2:New2</code>", parse_mode=enums.ParseMode.HTML
        )
    added = await database.add_replacements(message.from_user.id, rules)
    text = f"✅ <b>{len(rules)} replacement rule(s) saved!</b> (<b>{added}</b> naye)"
    if bad:
        text += f"\n\n⚠️ Skipped (no ':'): <code>{' | '.join(bad)}</code>"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remreplace") & filters.private)
async def cmd_remreplace(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remreplace Old | Old2</code>", parse_mode=enums.ParseMode.HTML
        )
    raw = message.text.split(None, 1)[1]
    olds = [w.strip() for w in raw.split("|") if w.strip()]
    removed = await database.remove_replacements(message.from_user.id, olds)
    if removed:
        await message.reply_text(f"🗑️ <b>{removed} rule(s) removed!</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("⚠️ <b>Koi matching rule nahi mila.</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("listreplace") & filters.private)
async def cmd_listreplace(client, message: Message):
    rules = await database.get_replacements(message.from_user.id)
    if not rules:
        return await message.reply_text("🔁 <b>No replacement rules set.</b>\n\nUse /addreplace to add one.",
                                        parse_mode=enums.ParseMode.HTML)
    text = "<b>🔁 Active Replacement Rules:</b>\n\n"
    for i, (old, new) in enumerate(rules, 1):
        text += f"{i}. <code>{old}</code> → <code>{new}</code>\n"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("clearreplace") & filters.private)
async def cmd_clearreplace(client, message: Message):
    await database.clear_replacements(message.from_user.id)
    await message.reply_text("🗑️ <b>All replacement rules cleared!</b>", parse_mode=enums.ParseMode.HTML)


# ==================== WORD REMOVE ====================

@Client.on_message(filters.command("addremoveword") & filters.private)
async def cmd_addremoveword(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Send Words To Remove</b>\n\n"
            "<b>Format:</b> <code>Word1 | Word2 | Word3</code>\n"
            "<b>Example:</b> <code>Hdts | Hdcam | 4k uhd</code>\n\n"
            "Use | to add multiple words.",
            parse_mode=enums.ParseMode.HTML
        )
    raw = message.text.split(None, 1)[1]
    words = [w.strip() for w in raw.split("|") if w.strip()]
    if not words:
        return await message.reply_text("<b>❌ Valid word(s) do.</b>", parse_mode=enums.ParseMode.HTML)
    added = await database.add_remove_words(message.from_user.id, words)
    await message.reply_text(f"✅ <b>{added} word(s) added to remove-list!</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remremoveword") & filters.private)
async def cmd_remremoveword(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remremoveword Word1 | Word2</code>", parse_mode=enums.ParseMode.HTML
        )
    raw = message.text.split(None, 1)[1]
    words = [w.strip() for w in raw.split("|") if w.strip()]
    removed = await database.remove_remove_words(message.from_user.id, words)
    if removed:
        await message.reply_text(f"🗑️ <b>{removed} word(s) removed from list!</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("⚠️ <b>Koi matching word nahi mila.</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("listremovewords") & filters.private)
async def cmd_listremovewords(client, message: Message):
    words = await database.get_remove_words(message.from_user.id)
    if not words:
        return await message.reply_text("🧹 <b>No remove-words set.</b>\n\nUse /addremoveword to add one.",
                                        parse_mode=enums.ParseMode.HTML)
    text = "<b>🧹 Active Remove-Words:</b>\n\n"
    for i, w in enumerate(words, 1):
        text += f"{i}. <code>{w}</code>\n"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("clearremovewords") & filters.private)
async def cmd_clearremovewords(client, message: Message):
    await database.clear_remove_words(message.from_user.id)
    await message.reply_text("🗑️ <b>All remove-words cleared!</b>", parse_mode=enums.ParseMode.HTML)


# ==================== RESET ALL SETTINGS (Danger Zone) ====================
# ✅ NEW: user agar confuse ho jaaye ya kuch galat set ho gaya ho, toh ek hi
# command se saari customization (caption, filters, words, footer) reset
# karke default pe wapas aa sake. Confirmation button ke bina reset nahi
# hoga — galti se data delete na ho isliye.

RESET_WARN_TEXT = (
    "<b>┃💥⚠️ <u>DANGER ZONE</u> ⚠️💥</b>\n\n"
    "<i>Are you sure you want to RESET EVERYTHING?</i>\n\n"
    "This will delete Caption, Filters, Words, Footer/Prefix "
    "<b>AND ALL your Source/Target channel mappings</b> — sab kuch.\n\n"
    "⚠️ Yeh action <b>undo nahi ho sakta.</b>"
)

def _reset_confirm_markup(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_sc("✅ YES, RESET EVERYTHING"), callback_data=f"confirm_reset:{user_id}")],
        [InlineKeyboardButton(_sc("❌ Cancel"), callback_data=f"cancel_reset:{user_id}")],
    ])

@Client.on_message(filters.command("reset") & filters.private)
async def cmd_reset(client, message: Message):
    await message.reply_text(
        RESET_WARN_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=_reset_confirm_markup(message.from_user.id),
    )

@Client.on_callback_query(filters.regex(r"^confirm_reset:(\d+)$"))
async def cb_confirm_reset(client, callback_query):
    target_uid = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != target_uid:
        return await callback_query.answer("🚫 Yeh button aapke liye nahi hai!", show_alert=True)

    await database.reset_all_settings(target_uid)
    await callback_query.answer("✅ Reset ho gaya!")
    await callback_query.message.edit_text(
        "✅ <b>Everything Reset!</b>\n\n"
        "Caption, Filters, Words, Footer aur saare Source/Target channel "
        "mappings — sab delete ho gaye.\n\n"
        "Naya setup shuru karne ke liye /set use karo.",
        parse_mode=enums.ParseMode.HTML,
    )

@Client.on_callback_query(filters.regex(r"^cancel_reset:(\d+)$"))
async def cb_cancel_reset(client, callback_query):
    target_uid = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != target_uid:
        return await callback_query.answer("🚫 Yeh button aapke liye nahi hai!", show_alert=True)

    await callback_query.answer("❌ Reset cancel kar diya.")
    await callback_query.message.edit_text(MENU_HEADER, parse_mode=enums.ParseMode.HTML, reply_markup=_menu_main_markup())


# ==================== STATS ====================

@Client.on_message(filters.command("count") & filters.private)
async def cmd_count(client, message: Message):
    count = await database.get_forward_count(message.from_user.id)
    await message.reply_text(
        f"📊 <b>Forward Stats</b>\n\n"
        f"✅ Total Forwarded: <b>{count}</b> messages\n\n"
        f"Reset karne ke liye /resetcount use karo.",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("resetcount") & filters.private)
async def cmd_resetcount(client, message: Message):
    await database.reset_forward_count(message.from_user.id)
    await message.reply_text("🔄 <b>Count reset!</b>", parse_mode=enums.ParseMode.HTML)


# ==================== ADMIN SYSTEM ====================

@Client.on_message(filters.command("addadmin") & filters.private)
@owner_only
async def cmd_addadmin(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/addadmin user_id</code>", parse_mode=enums.ParseMode.HTML
        )
    try:
        target_id = int(message.command[1])
        await database.add_admin(message.from_user.id, target_id)
        await message.reply_text(
            f"👑 <b>Admin added:</b> <code>{target_id}</code>", parse_mode=enums.ParseMode.HTML
        )
    except ValueError:
        await message.reply_text("<b>❌ Valid user_id do.</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("removeuser") & filters.private)
@owner_only
async def cmd_removeuser(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/removeuser user_id</code>", parse_mode=enums.ParseMode.HTML
        )
    try:
        target_id = int(message.command[1])
        removed = await database.remove_admin(message.from_user.id, target_id)
        if removed:
            await message.reply_text(
                f"✅ <b>Admin removed:</b> <code>{target_id}</code>", parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(f"⚠️ <b>Not found in admins.</b>", parse_mode=enums.ParseMode.HTML)
    except ValueError:
        await message.reply_text("<b>❌ Valid user_id do.</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("ban") & filters.private)
@admin_only
async def cmd_ban(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/ban user_id</code>", parse_mode=enums.ParseMode.HTML
        )
    try:
        target_id = int(message.command[1])
        if cfg.OWNER_ID and target_id == cfg.OWNER_ID:
            return await message.reply_text("<b>❌ Owner ko ban nahi kar sakte.</b>", parse_mode=enums.ParseMode.HTML)
        # ✅ FIX: hamesha cfg.OWNER_ID ke under scope karo (admin ke apne id ke under nahi),
        # warna admin ka ban owner/dusre admins ko dikhega hi nahi.
        await database.ban_user(cfg.OWNER_ID, target_id)
        from SilentXForward.forward import active_userbots
        ub = active_userbots.pop(target_id, None)
        if ub:
            try:
                await ub.stop()
            except Exception:
                pass
        await message.reply_text(
            f"🚫 <b>User banned:</b> <code>{target_id}</code>", parse_mode=enums.ParseMode.HTML
        )
    except ValueError:
        await message.reply_text("<b>❌ Valid user_id do.</b>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("unban") & filters.private)
@admin_only
async def cmd_unban(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/unban user_id</code>", parse_mode=enums.ParseMode.HTML
        )
    try:
        target_id = int(message.command[1])
        unbanned = await database.unban_user(cfg.OWNER_ID, target_id)
        if unbanned:
            await message.reply_text(
                f"✅ <b>User unbanned:</b> <code>{target_id}</code>", parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text("⚠️ <b>User not in ban list.</b>", parse_mode=enums.ParseMode.HTML)
    except ValueError:
        await message.reply_text("<b>❌ Valid user_id do.</b>", parse_mode=enums.ParseMode.HTML)


# ==================== CHANNEL MANAGEMENT ====================

@Client.on_message(filters.command("set") & filters.private)
async def set_channels(client, message: Message):
    user_id = message.from_user.id
    if len(message.command) < 3:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/set &lt;source_id&gt; &lt;target_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    proc_msg = await message.reply_text("⏳ Processing...")
    try:
        source_chat = await smart_get_chat(client, message.command[1], user_id)
        target_chat = await smart_get_chat(client, message.command[2], user_id)
        result = await database.add_target_to_source(
            user_id, source_chat.id, target_chat.id, source_chat.title, target_chat.title
        )
        await proc_msg.delete()
        if result in ("created", "added"):
            action = "New Source Created" if result == "created" else "Target Added"
            await message.reply_text(
                f"<b>✅ {action}:</b>\n\n"
                f"📥 Source: {source_chat.title}\n   <code>{source_chat.id}</code>\n\n"
                f"📤 Target: {target_chat.title}\n   <code>{target_chat.id}</code>\n\n"
                f"🎉 Messages Will Be Forwarded!",
                parse_mode=enums.ParseMode.HTML
            )
            await log_source_added(client, message.from_user,
                                   source_chat.title, source_chat.id,
                                   target_chat.title, target_chat.id)
        else:
            await message.reply_text("<b>⚠️ Already Exists!</b>", parse_mode=enums.ParseMode.HTML)
    except PeerIdInvalid:
        await proc_msg.delete()
        await message.reply_text(
            "<b>❌ PEER_ID_INVALID!</b>\n\n"
            "Apne Telegram se <b>dono channels ek baar kholo</b> phir /set try karo.",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await proc_msg.delete()
        await message.reply_text(
            f"<b>❌ Error:</b> <code>{e}</code>\n\n/session se check karo.",
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("remove_target") & filters.private)
async def remove_target_channel(client, message: Message):
    user_id = message.from_user.id
    if len(message.command) < 3:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_target &lt;source_id&gt; &lt;target_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        source_chat = await smart_get_chat(client, message.command[1], user_id)
        target_chat = await smart_get_chat(client, message.command[2], user_id)
        result = await database.remove_target_from_source(user_id, source_chat.id, target_chat.id)
        if result == "removed":
            await message.reply_text(
                f"✅ <b>Target Removed!</b>\n\n"
                f"📥 {source_chat.title} (<code>{source_chat.id}</code>)\n"
                f"🗑️ {target_chat.title} (<code>{target_chat.id}</code>)",
                parse_mode=enums.ParseMode.HTML
            )
            await log_target_removed(client, message.from_user,
                                     source_chat.title, source_chat.id,
                                     target_chat.title, target_chat.id)
        else:
            await message.reply_text("<b>⚠️ Not Found.</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>❌ Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remove_source") & filters.private)
async def remove_channel(client, message: Message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>❌ Usage:</b> <code>/remove_source &lt;source_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        chat = await smart_get_chat(client, message.command[1], user_id)
        removed = await database.remove_source(user_id, chat.id)
        if removed:
            await message.reply_text(
                f"✅ <b>Removed:</b> {chat.title} (<code>{chat.id}</code>)",
                parse_mode=enums.ParseMode.HTML
            )
            await log_source_removed(client, message.from_user, chat.title, chat.id)
        else:
            await message.reply_text(f"⚠️ Not found.", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>❌ Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("list") & filters.private)
async def list_mappings(client, message: Message):
    user_id  = message.from_user.id
    mappings = await database.get_user_mappings(user_id)
    if not mappings:
        return await message.reply_text(
            "<b>❌ No mappings found!</b>\n\nUse /set to create one.",
            parse_mode=enums.ParseMode.HTML
        )
    text = "<b>📊 Your Channel Mappings:</b>\n\n"
    for idx, mapping in enumerate(mappings, 1):
        source_id  = mapping['source_id']
        target_ids = mapping.get('target_ids', [])
        try:
            sc = await smart_get_chat(client, source_id, user_id)
            text += f"<b>{idx}. 📥 {sc.title}</b>\n   <code>{source_id}</code>\n   ⤵️ Targets ({len(target_ids)}):\n"
            for tid in target_ids:
                try:
                    tc = await smart_get_chat(client, tid, user_id)
                    text += f"   • {tc.title} (<code>{tid}</code>)\n"
                except:
                    text += f"   • <code>{tid}</code>\n"
            text += "\n"
        except:
            text += f"<b>{idx}.</b> <code>{source_id}</code> — {len(target_ids)} target(s)\n\n"
    text += f"<b>Total Sources:</b> {len(mappings)}"
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("clear") & filters.private)
async def clear_all(client, message: Message):
    count = await database.clear_all_mappings(message.from_user.id)
    if count > 0:
        await message.reply_text(f"<b>✅ Cleared {count} source(s)!</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("<b>❌ No mappings to clear!</b>", parse_mode=enums.ParseMode.HTML)


# ==================== BROADCAST ====================

@Client.on_message(filters.command("broadcast") & filters.private)
@admin_only
async def cmd_broadcast(client, message: Message):
    # Message must be a reply OR have text after command
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "<b>📢 Broadcast Usage:</b>\n\n"
            "1. Koi message reply karke: <code>/broadcast</code>\n"
            "2. Ya seedha: <code>/broadcast Hello everyone!</code>\n\n"
            "<i>Sabhi bot users ko message jayega.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    status_msg = await message.reply_text("📢 <b>Broadcasting...</b>", parse_mode=enums.ParseMode.HTML)

    # ✅ FIX: pehle sirf userbot-login wale users ko milta tha, ab SABHI bot users ko jaata hai
    # (jinhone kabhi bhi /start kiya ho), userbot-session users ke saath union karke.
    broadcast_users = set(await database.get_all_user_ids())
    all_sessions     = await database.get_all_userbot_sessions()
    broadcast_users.update(doc["user_id"] for doc in all_sessions if doc.get("user_id"))
    user_ids = list(broadcast_users)

    if not user_ids:
        return await status_msg.edit("<b>⚠️ Koi user nahi mila.</b>", parse_mode=enums.ParseMode.HTML)

    success = 0
    failed  = 0

    for uid in user_ids:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy(uid)
            else:
                text = message.text.split(None, 1)[1]
                await client.send_message(uid, text, parse_mode=enums.ParseMode.HTML)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.3)  # flood protection

    await status_msg.edit(
        f"<b>📢 Broadcast Complete!</b>\n\n"
        f"✅ Sent: <b>{success}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"👥 Total: <b>{len(user_ids)}</b>",
        parse_mode=enums.ParseMode.HTML
    )


# ==================== USERBOT LOGIN ====================

@Client.on_message(filters.command("login") & filters.private)
async def cmd_login(client, message: Message):
    user_id  = message.from_user.id

    # ── Force Subscribe Check ──
    not_joined = await check_fsub(client, user_id)
    if not_joined:
        return await send_fsub_message(client, message, not_joined)

    existing = await database.get_userbot_session(user_id)
    if existing:
        return await message.reply_text(
            f"✅ <b>You're already logged in! 🎉</b>\n\n"
            f"📱 Phone: {existing.get('phone','N/A')}\n"
            f"🕐 Login: {existing.get('created_at','N/A')}\n\n"
            f"To switch accounts, first use /logout | /session",
            parse_mode=enums.ParseMode.HTML
        )
    login_states[user_id] = {"step": "phone"}
    await message.reply_text(
        "👋 <b>Hey! Let's log you in smoothly 🌟</b>\n\n"
        "<i>Progress: 🟢 Phone Number → 🔵 Code → 🔵 Password</i>\n\n"
        "📞 Please send your <b>Telegram Phone Number</b> with country code.\n\n"
        "<blockquote>Example: <code>+919876543210</code></blockquote>\n\n"
        "💡 <i>Your number is used only for verification and is kept secure. 🔒</i>\n\n"
        "❌ Tap the <b>Cancel</b> button or send /cancel to stop.",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("logout") & filters.private)
async def cmd_logout(client, message: Message):
    user_id = message.from_user.id
    from SilentXForward.forward import active_userbots
    ub = active_userbots.get(user_id)
    if ub:
        try:
            await ub.stop()
        except Exception:
            pass
        active_userbots.pop(user_id, None)
    deleted = await database.delete_userbot_session(user_id)
    if deleted:
        await log_logout(client, message.from_user)
        await message.reply_text(
            "🚪 <b>Logout Successful! 👋</b>\n\n"
            "<i>Your session has been cleared. You can log in again anytime! 🔄</i>",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            "⚠️ <b>No Active Session!</b>\n\n"
            "<i>You are not logged in. Use /login to connect your account.</i>",
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("session") & filters.private)
async def cmd_session(client, message: Message):
    user_id = message.from_user.id
    session = await database.get_userbot_session(user_id)
    if not session:
        return await message.reply_text(
            "❌ <b>No Active Session!</b>\n\n"
            "<i>You are not logged in yet. Use /login to connect your Telegram account.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    from SilentXForward.forward import active_userbots
    ub     = active_userbots.get(user_id)
    status = "🟢 Active" if (ub and ub.is_connected) else "🔴 Inactive (restart bot)"
    await message.reply_text(
        f"📋 <b>Session Info</b>\n\n"
        f"👤 Status: {status}\n"
        f"📱 Phone: {session.get('phone','N/A')}\n"
        f"🕐 Login: {session.get('created_at','N/A')}\n\n"
        f"To switch accounts, first use /logout | /session",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(client, message: Message):
    user_id = message.from_user.id
    if user_id in login_states:
        tc = login_states[user_id].get("temp_client")
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        del login_states[user_id]
        await message.reply_text("<b>❌ Login cancelled.</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("<b>⚠️ No active login.</b>", parse_mode=enums.ParseMode.HTML)


# ==================== LOGIN STEP HANDLER ====================

@Client.on_message(
    filters.private & filters.text &
    ~filters.command(["login","logout","session","cancel","start","help","about",
                      "set","remove_target","remove_source","list","clear",
                      "on","off","resume","status","setdelay","skip",
                      "addfilter","remfilter","listfilters",
                      "endtext","remendtext","listendtext",
                      "setcaption","showcaption","delcaption",
                      "addreplace","remreplace","listreplace","clearreplace",
                      "addremoveword","remremoveword","listremovewords","clearremovewords",
                      "count","resetcount","addadmin","removeuser","ban","unban",
                      "broadcast","reset","settings","manage",
                      "whitelist","remove_whitelist","blacklist","remove_blacklist","listblacklist"])  # ✅ FIX: naye commands add kiye — warna yeh handler unhe pehle hi "swallow" kar leta tha
)
async def login_step_handler(client, message: Message):
    user_id = message.from_user.id
    if user_id not in login_states:
        # ✅ FIX: sirf 'return' karne se Pyrogram is group ke aage kisi
        # aur handler (jaise /settings, /manage, /reset) ko chance hi nahi
        # deta tha — ContinuePropagation se aage ke handlers ko turant
        # mauka mil jaata hai, chahe woh command upar wali exclusion list
        # mein add karna bhool jaaye.
        raise ContinuePropagation

    state = login_states[user_id]
    step  = state.get("step")

    # ── Phone ──────────────────────────────────────────────────────────────
    if step == "phone":
        phone = message.text.strip()
        msg   = await message.reply_text("🔄 <b>Connecting •••</b>", parse_mode=enums.ParseMode.HTML)

        # ✅ Animated connecting effect
        frames = [
            "🔄 <b>Connecting •••</b>",
            "🔄 <b>Connecting ••○</b>",
            "🔄 <b>Connecting •○○</b>",
            "🔄 <b>Connecting ○○○</b>",
            "🔄 <b>Connecting ○○•</b>",
            "🔄 <b>Connecting ○••</b>",
            "🔄 <b>Connecting •••</b>",
        ]
        for frame in frames:
            try:
                await msg.edit(frame, parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(0.3)
            except Exception:
                pass

        import config as cfg
        temp_client = Client(f"temp_{user_id}", api_id=cfg.API_ID, api_hash=cfg.API_HASH, in_memory=True)
        try:
            await temp_client.connect()
            sent = await temp_client.send_code(phone)
            state.update({"step":"otp","phone":phone,
                          "phone_code_hash":sent.phone_code_hash,"temp_client":temp_client})
            login_states[user_id] = state
            await msg.edit(
                "📩 <b>OTP Sent to your app! 📱</b>\n\n"
                "<i>Progress: ✅ Phone Number → 🟢 Code → 🔵 Password</i>\n\n"
                "Please open your Telegram app and copy the verification code.\n\n"
                "<b>Send it like this:</b> 12 345 or 1 2 3 4 5 6\n\n"
                "<blockquote>Adding spaces helps prevent Telegram from deleting the message automatically. 💡</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneNumberInvalid:
            await temp_client.disconnect()
            del login_states[user_id]
            await msg.edit(
                "❌ <b>Invalid Phone Number!</b>\n\n"
                "<i>Progress: 🔴 Phone Number → 🔵 Code → 🔵 Password</i>\n\n"
                "Please send a valid number with country code.\n"
                "<blockquote>Example: <code>+919876543210</code></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            await temp_client.disconnect()
            del login_states[user_id]
            await msg.edit(f"<b>❌ Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

    # ── OTP ────────────────────────────────────────────────────────────────
    elif step == "otp":
        otp = message.text.strip().replace(" ","")
        temp_client = state.get("temp_client")
        try:
            await temp_client.sign_in(state["phone"], state["phone_code_hash"], otp)
            ss = await temp_client.export_session_string()
            await temp_client.disconnect()
            await database.save_userbot_session(user_id, ss, state["phone"])
            del login_states[user_id]
            from SilentXForward.forward import start_single_userbot
            await start_single_userbot(user_id, ss)
            await log_login(client, message.from_user, state["phone"])
            await message.reply_text(
                "🎉 <b>Login Successful! 🌟</b>\n\n"
                "<i>Progress: ✅ Phone Number → ✅ Code → ✅ Password</i>\n\n"
                "Your session has been saved securely. 🔒\n\n"
                "You can now use all features! 🚀\n\n"
                "<b>⚠️ Important:</b> Apne account se <b>source/target channels ek baar kholo</b> phir /set karo.\n\n"
                "📋 /session | 🚪 /logout",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneCodeInvalid:
            await message.reply_text(
                "❌ <b>Wrong OTP!</b>\n\n"
                "<i>Progress: ✅ Phone Number → 🔴 Code → 🔵 Password</i>\n\n"
                "Please check the code and try again.",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneCodeExpired:
            await temp_client.disconnect()
            del login_states[user_id]
            await message.reply_text(
                "⏰ <b>OTP Expired!</b>\n\n"
                "<i>Progress: ✅ Phone Number → 🔴 Code → 🔵 Password</i>\n\n"
                "Please start again with /login.",
                parse_mode=enums.ParseMode.HTML
            )
        except SessionPasswordNeeded:
            state["step"] = "password"
            login_states[user_id] = state
            await message.reply_text(
                "🔒 <b>Two-Step Verification Detected 🔒</b>\n\n"
                "<i>Progress: ✅ Phone Number → ✅ Code → 🟢 Password</i>\n\n"
                "Please enter your account <b>password</b>.\n\n"
                "<i>Take your time — it's secure! 🛡️</i>",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            del login_states[user_id]
            await message.reply_text(f"<b>❌ Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)

    # ── 2FA ────────────────────────────────────────────────────────────────
    elif step == "password":
        temp_client = state.get("temp_client")
        try:
            await temp_client.check_password(message.text.strip())
            ss = await temp_client.export_session_string()
            await temp_client.disconnect()
            await database.save_userbot_session(user_id, ss, state["phone"])
            del login_states[user_id]
            from SilentXForward.forward import start_single_userbot
            await start_single_userbot(user_id, ss)
            await log_login(client, message.from_user, state["phone"])
            await message.reply_text(
                "🎉 <b>Login Successful! 🌟</b>\n\n"
                "<i>Progress: ✅ Phone Number → ✅ Code → ✅ Password</i>\n\n"
                "Your session has been saved securely. 🔒\n\n"
                "You can now use all features! 🚀\n\n"
                "<b>⚠️ Important:</b> Apne account se <b>source/target channels ek baar kholo</b> phir /set karo.\n\n"
                "📋 /session | 🚪 /logout",
                parse_mode=enums.ParseMode.HTML
            )
        except PasswordHashInvalid:
            await message.reply_text(
                "❌ <b>Wrong Password!</b>\n\n"
                "<i>Progress: ✅ Phone Number → ✅ Code → 🔴 Password</i>\n\n"
                "Please enter the correct password.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
            del login_states[user_id]
            await message.reply_text(f"<b>❌ Error:</b> <code>{e}</code>", parse_mode=enums.ParseMode.HTML)


# ============================================================================
# ==================== INTERACTIVE BUTTON SETTINGS MENU ====================
# ============================================================================
# ✅ NEW: /settings ya /manage command se saari settings ab buttons se hi
# manage ho sakti hain — text commands yaad rakhne ki zaroorat nahi.
# Jahan text input zaroori hai (word, delay value, channel id waghera),
# wahan bot prompt karke reply ka wait karta hai (settings_states dict).

settings_states: dict[int, dict] = {}   # user_id -> {"action": ..., "back": ...}

MENU_HEADER = "<u><b><blockquote>⚙️ ᴍᴀɴᴀɢᴇ ᴄʜᴀɴɴᴇʟ sᴇᴛᴛɪɴɢs\n\n👇🏼 sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ:</b></blockquote></u>"
# ✅ NEW: button labels ko sᴍᴀʟʟ ᴄᴀᴘꜱ unicode style mein dikhane ke liye —
# sirf English letters convert hote hain, emoji/space/symbols waise hi rehte hain.
_SMALLCAPS_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
)

def _sc(text: str) -> str:
    """Button label ko small-caps style mein convert karo."""
    return text.translate(_SMALLCAPS_MAP)

# action-key -> submenu jahan wapas jaana hai jab input mil jaaye ya cancel ho
_INPUT_BACK_MENU = {
    "delay": "delay",
    "filter_add": "filters", "filter_rem": "filters",
    "blacklist_add": "filters", "blacklist_rem": "filters",
    "footer_set": "footer",
    "caption_set": "caption",
    "replace_add": "replace", "replace_rem": "replace",
    "remword_add": "removewords", "remword_rem": "removewords",
    "mapping_set": "manage", "mapping_remtarget": "manage", "mapping_remsource": "manage",
    "admin_add": "admin", "admin_ban": "admin", "admin_unban": "admin",
}

INPUT_PROMPTS = {
    "delay":              "✏️ <b>Naya delay (seconds) bhejo:</b>\n\n<i>Example: 0.3</i>",
    "filter_add":         "➕ <b>Whitelist word bhejo</b> jo add karna hai:",
    "filter_rem":         "🗑️ <b>Whitelist word bhejo</b> jo remove karna hai:",
    "blacklist_add":      "➕ <b>Blacklist word bhejo</b> jo add karna hai:",
    "blacklist_rem":      "🗑️ <b>Blacklist word bhejo</b> jo remove karna hai:",
    "footer_set":         "✏️ <b>Naya footer/prefix text bhejo:</b>",
    "caption_set":        CAPTION_VARS_TEXT + "\n\n✏️ <b>Ab apna template bhejo:</b>",
    "replace_add":        "➕ <b>Replace rule bhejo</b> — format: <code>Old:New</code>\n(multiple ke liye <code>|</code> se separate karo)",
    "replace_rem":        "🗑️ <b>'Old' word bhejo</b> jiska rule remove karna hai:",
    "remword_add":        "➕ <b>Word(s) bhejo</b> jo remove-list mein add karne hain (<code>|</code> se separate):",
    "remword_rem":        "🗑️ <b>Word(s) bhejo</b> jo remove-list se hatane hain:",
    "mapping_set":        "➕ <b>Source aur Target channel ID/username bhejo</b>, space se separate:\n\n<i>Example: -1001234567890 -1009876543210</i>",
    "mapping_remtarget":  "🗑️ <b>Source aur Target ID bhejo</b> (space se separate) jise mapping se hatana hai:",
    "mapping_remsource":  "🗑️ <b>Source channel ID bhejo</b> jise poori tarah remove karna hai:",
    "admin_add":          "➕ <b>User ID bhejo</b> jise admin banana hai:",
    "admin_ban":          "🚫 <b>User ID bhejo</b> jise ban karna hai:",
    "admin_unban":        "✅ <b>User ID bhejo</b> jise unban karna hai:",
}


def _menu_main_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_sc("⏱️ Delay"), callback_data="menu:delay"),
         InlineKeyboardButton(_sc("🔍 Filters"), callback_data="menu:filters")],
        [InlineKeyboardButton(_sc("✍️ Footer"), callback_data="menu:footer"),
         InlineKeyboardButton(_sc("📝 Caption"), callback_data="menu:caption")],
        [InlineKeyboardButton(_sc("🔁 Replace Words"), callback_data="menu:replace"),
         InlineKeyboardButton(_sc("🧹 Remove Words"), callback_data="menu:removewords")],
        [InlineKeyboardButton(_sc("📊 Manage Channels"), callback_data="menu:manage"),
         InlineKeyboardButton(_sc("📈 Stats"), callback_data="menu:stats")],
        [InlineKeyboardButton(_sc("🔑 Login / Session"), callback_data="menu:login"),
         InlineKeyboardButton(_sc("👑 Admin"), callback_data="menu:admin")],
        [InlineKeyboardButton(_sc("ℹ️ Status"), callback_data="menu:status"),
         InlineKeyboardButton(_sc("⏯️ Toggle Forward"), callback_data="menu:toggle")],
        [InlineKeyboardButton(_sc("🧨 RESET ALL SETTINGS"), callback_data="menu:reset")],
        [InlineKeyboardButton(_sc("🔙 Back"), callback_data="menu:back"),
         InlineKeyboardButton(_sc("❌ Close"), callback_data="menu:close")],
    ])

def _back_menu_button(target: str = "main") -> list:
    return [InlineKeyboardButton(_sc("🔙 Back to Menu"), callback_data=f"menu:{target}")]


# ── Submenu renderers: har ek (text, markup) return karta hai ──────────────

async def _render_delay(user_id):
    delay = await database.get_delay(user_id)
    text = f"⏱️ <b>Message Delay</b>\n\nCurrent: <code>{delay}s</code>\n\nPreset choose karo ya custom bhejo:"
    kb = [
        [InlineKeyboardButton(_sc("0.1s"), callback_data="delay:0.1"), InlineKeyboardButton(_sc("0.5s"), callback_data="delay:0.5")],
        [InlineKeyboardButton(_sc("1s"), callback_data="delay:1"), InlineKeyboardButton(_sc("2s"), callback_data="delay:2")],
        [InlineKeyboardButton(_sc("✏️ Custom"), callback_data="input:delay")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_filters(user_id):
    words = await database.get_filters(user_id)
    bl = await database.get_blacklist(user_id)
    text = "🔍 <b>Whitelist Words</b> <i>(sirf yeh wale forward honge)</i>\n\n"
    text += "\n".join(f"• <code>{w}</code>" for w in words) if words else "<i>Empty — sab messages forward honge.</i>"
    text += "\n\n🚫 <b>Blacklist Words</b> <i>(yeh wale skip honge)</i>\n\n"
    text += "\n".join(f"• <code>{w}</code>" for w in bl) if bl else "<i>Empty.</i>"
    kb = [
        [InlineKeyboardButton(_sc("➕ Add Whitelist"), callback_data="input:filter_add"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="input:filter_rem")],
        [InlineKeyboardButton(_sc("➕ Add Blacklist"), callback_data="input:blacklist_add"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="input:blacklist_rem")],
        [InlineKeyboardButton(_sc("🧹 Clear Whitelist"), callback_data="action:filter_clear"),
         InlineKeyboardButton(_sc("🧹 Clear Blacklist"), callback_data="action:blacklist_clear")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_footer(user_id):
    footer = await database.get_endtext(user_id)
    text = "✍️ <b>Footer / Prefix Text</b>\n\n"
    text += f"<code>{footer}</code>" if footer else "<i>No footer set.</i>"
    kb = [
        [InlineKeyboardButton(_sc("✏️ Set"), callback_data="input:footer_set"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="action:footer_rem")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_caption(user_id):
    tmpl = await database.get_caption_template(user_id)
    text = "📝 <b>Custom Caption Template</b>\n\n"
    text += f"<code>{tmpl}</code>" if tmpl else "<i>No caption template set — default caption use hogi.</i>"
    kb = [
        [InlineKeyboardButton(_sc("✏️ Set"), callback_data="input:caption_set"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="action:caption_rem")],
        [InlineKeyboardButton(_sc("📚 Variables List"), callback_data="action:caption_vars")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_replace(user_id):
    rules = await database.get_replacements(user_id)
    text = "🔁 <b>Replace Words</b>\n\n"
    text += "\n".join(f"{i}. <code>{o}</code> → <code>{n}</code>" for i, (o, n) in enumerate(rules, 1)) if rules else "<i>No rules set.</i>"
    kb = [
        [InlineKeyboardButton(_sc("➕ Add"), callback_data="input:replace_add"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="input:replace_rem")],
        [InlineKeyboardButton(_sc("🧹 Clear All"), callback_data="action:replace_clear")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_removewords(user_id):
    words = await database.get_remove_words(user_id)
    text = "🧹 <b>Remove Words</b>\n\n"
    text += "\n".join(f"• <code>{w}</code>" for w in words) if words else "<i>No remove-words set.</i>"
    kb = [
        [InlineKeyboardButton(_sc("➕ Add"), callback_data="input:remword_add"),
         InlineKeyboardButton(_sc("🗑️ Remove"), callback_data="input:remword_rem")],
        [InlineKeyboardButton(_sc("🧹 Clear All"), callback_data="action:remword_clear")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_manage(user_id):
    mappings = await database.get_user_mappings(user_id)
    text = "📊 <b>Manage Source/Target Channels</b>\n\n"
    if mappings:
        for m in mappings:
            text += f"📥 <code>{m['source_id']}</code> → {len(m.get('target_ids', []))} target(s)\n"
    else:
        text += "<i>No mappings yet.</i>"
    kb = [
        [InlineKeyboardButton(_sc("➕ Set New"), callback_data="input:mapping_set")],
        [InlineKeyboardButton(_sc("🗑️ Remove Target"), callback_data="input:mapping_remtarget"),
         InlineKeyboardButton(_sc("🗑️ Remove Source"), callback_data="input:mapping_remsource")],
        [InlineKeyboardButton(_sc("🧨 Clear All Channels"), callback_data="action:mapping_clear")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_stats(user_id):
    count = await database.get_forward_count(user_id)
    text = f"📈 <b>Forward Stats</b>\n\n✅ Total Forwarded: <b>{count}</b> messages"
    kb = [
        [InlineKeyboardButton(_sc("🔄 Reset Count"), callback_data="action:count_reset")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

async def _render_login(user_id):
    session = await database.get_userbot_session(user_id)
    if session:
        from SilentXForward.forward import active_userbots
        ub = active_userbots.get(user_id)
        status = "🟢 Active" if (ub and ub.is_connected) else "🔴 Inactive (restart bot)"
        text = (f"🔑 <b>Session Info</b>\n\n👤 Status: {status}\n"
                f"📱 Phone: {session.get('phone','N/A')}\n🕐 Login: {session.get('created_at','N/A')}")
        kb = [[InlineKeyboardButton(_sc("🚪 Logout"), callback_data="action:logout")], _back_menu_button()]
    else:
        text = "🔑 <b>Userbot Login</b>\n\nAap logged in nahi ho.\n\n<i>Login karne ke liye /login command use karo (security ke liye phone/OTP button se nahi liya jaata).</i>"
        kb = [_back_menu_button()]
    return text, InlineKeyboardMarkup(kb)

async def _render_admin(user_id):
    text = "👑 <b>Admin Tools</b>\n\nAdmin add/remove aur ban/unban yahan se karo."
    kb = [
        [InlineKeyboardButton(_sc("➕ Add Admin"), callback_data="input:admin_add")],
        [InlineKeyboardButton(_sc("🚫 Ban User"), callback_data="input:admin_ban"),
         InlineKeyboardButton(_sc("✅ Unban User"), callback_data="input:admin_unban")],
        _back_menu_button(),
    ]
    return text, InlineKeyboardMarkup(kb)

_MENU_RENDERERS = {
    "delay": _render_delay, "filters": _render_filters, "footer": _render_footer,
    "caption": _render_caption, "replace": _render_replace, "removewords": _render_removewords,
    "manage": _render_manage, "stats": _render_stats, "login": _render_login, "admin": _render_admin,
}


@Client.on_message(filters.command(["settings", "manage"]) & filters.private)
async def cmd_settings_menu(client, message: Message):
    await message.reply_text(MENU_HEADER, parse_mode=enums.ParseMode.HTML, reply_markup=_menu_main_markup())


@Client.on_callback_query(filters.regex(r"^menu:(.+)$"))
async def cb_menu_router(client, callback_query):
    user_id = callback_query.from_user.id
    key = callback_query.matches[0].group(1)

    if key == "main":
        await callback_query.answer()
        return await callback_query.message.edit_text(MENU_HEADER, parse_mode=enums.ParseMode.HTML, reply_markup=_menu_main_markup())

    if key == "back":
        await callback_query.answer()
        return await callback_query.message.edit_text(START_TEXT, parse_mode=enums.ParseMode.HTML, reply_markup=BUTTONS)

    if key == "close":
        await callback_query.answer()
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        return

    if key == "toggle":
        enabled = await database.is_forwarding_enabled(user_id)
        await database.set_forwarding(user_id, not enabled)
        await callback_query.answer("▶️ Forwarding Resumed!" if not enabled else "⏸️ Forwarding Paused!")
        return await callback_query.message.edit_text(MENU_HEADER, parse_mode=enums.ParseMode.HTML, reply_markup=_menu_main_markup())

    if key == "reset":
        await callback_query.answer()
        return await callback_query.message.edit_text(
            RESET_WARN_TEXT, parse_mode=enums.ParseMode.HTML, reply_markup=_reset_confirm_markup(user_id)
        )

    if key == "status":
        await callback_query.answer()
        text = await _build_status_text(user_id)
        kb = InlineKeyboardMarkup([_back_menu_button()])
        return await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)

    fn = _MENU_RENDERERS.get(key)
    if fn:
        await callback_query.answer()
        text, kb = await fn(user_id)
        return await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)

    await callback_query.answer()


@Client.on_callback_query(filters.regex(r"^delay:(.+)$"))
async def cb_delay_preset(client, callback_query):
    user_id = callback_query.from_user.id
    value = float(callback_query.matches[0].group(1))
    await database.set_delay(user_id, value)
    await callback_query.answer(f"✅ Delay set to {value}s")
    text, kb = await _render_delay(user_id)
    await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)


@Client.on_callback_query(filters.regex(r"^action:(.+)$"))
async def cb_menu_action(client, callback_query):
    user_id = callback_query.from_user.id
    action  = callback_query.matches[0].group(1)
    msg = ""

    if action == "filter_clear":
        await database.clear_filters(user_id)
        msg = "🧹 All whitelist words cleared!"
        text, kb = await _render_filters(user_id)
    elif action == "blacklist_clear":
        await database.clear_blacklist(user_id)
        msg = "🧹 All blacklist words cleared!"
        text, kb = await _render_filters(user_id)
    elif action == "footer_rem":
        await database.remove_endtext(user_id)
        msg = "🗑️ Footer removed!"
        text, kb = await _render_footer(user_id)
    elif action == "caption_rem":
        await database.remove_caption_template(user_id)
        msg = "🗑️ Caption removed!"
        text, kb = await _render_caption(user_id)
    elif action == "caption_vars":
        await callback_query.answer()
        kb = InlineKeyboardMarkup([_back_menu_button("caption")])
        return await callback_query.message.edit_text(CAPTION_VARS_TEXT, parse_mode=enums.ParseMode.HTML, reply_markup=kb)
    elif action == "replace_clear":
        await database.clear_replacements(user_id)
        msg = "🧹 All replace rules cleared!"
        text, kb = await _render_replace(user_id)
    elif action == "remword_clear":
        await database.clear_remove_words(user_id)
        msg = "🧹 All remove-words cleared!"
        text, kb = await _render_removewords(user_id)
    elif action == "mapping_clear":
        n = await database.clear_all_mappings(user_id)
        msg = f"🧨 {n} mapping(s) cleared!"
        text, kb = await _render_manage(user_id)
    elif action == "count_reset":
        await database.reset_forward_count(user_id)
        msg = "🔄 Count reset!"
        text, kb = await _render_stats(user_id)
    elif action == "logout":
        from SilentXForward.forward import active_userbots
        ub = active_userbots.get(user_id)
        if ub:
            try:
                await ub.stop()
            except Exception:
                pass
            active_userbots.pop(user_id, None)
        await database.delete_userbot_session(user_id)
        msg = "🚪 Logged out!"
        text, kb = await _render_login(user_id)
    else:
        return await callback_query.answer()

    await callback_query.answer(msg)
    await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)


@Client.on_callback_query(filters.regex(r"^input:(.+)$"))
async def cb_menu_input_prompt(client, callback_query):
    user_id = callback_query.from_user.id
    key = callback_query.matches[0].group(1)
    prompt = INPUT_PROMPTS.get(key)
    if not prompt:
        return await callback_query.answer()

    settings_states[user_id] = {"action": key, "back": _INPUT_BACK_MENU.get(key, "main")}
    await callback_query.answer()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(_sc("❌ Cancel"), callback_data="input_cancel")]])
    await callback_query.message.edit_text(
        f"{prompt}\n\n<i>Cancel karne ke liye neeche button dabao.</i>",
        parse_mode=enums.ParseMode.HTML, reply_markup=kb
    )


@Client.on_callback_query(filters.regex(r"^input_cancel$"))
async def cb_menu_input_cancel(client, callback_query):
    user_id = callback_query.from_user.id
    state = settings_states.pop(user_id, None)
    back_key = state.get("back", "main") if state else "main"
    await callback_query.answer("❌ Cancelled")

    if back_key == "main" or back_key not in _MENU_RENDERERS:
        return await callback_query.message.edit_text(MENU_HEADER, parse_mode=enums.ParseMode.HTML, reply_markup=_menu_main_markup())
    text, kb = await _MENU_RENDERERS[back_key](user_id)
    await callback_query.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)


# ── Text-input capture (group=2 taaki group-0 ke login handler se conflict na ho) ──
@Client.on_message(
    filters.private & filters.text & filters.create(lambda _, __, m: m.from_user.id in settings_states),
    group=2,
)
async def settings_menu_input_handler(client, message: Message):
    user_id = message.from_user.id
    state = settings_states.pop(user_id, None)
    if not state:
        return

    action   = state["action"]
    back_key = state.get("back", "main")
    raw = message.text.strip()
    msg = ""

    try:
        if action == "delay":
            val = float(raw)
            await database.set_delay(user_id, val)
            msg = f"✅ Delay set to {val}s"

        elif action == "filter_add":
            added = await database.add_filter(user_id, raw)
            msg = "✅ Whitelist word added!" if added else "⚠️ Yeh word already hai."

        elif action == "filter_rem":
            removed = await database.remove_filter(user_id, raw)
            msg = "🗑️ Whitelist word removed!" if removed else "⚠️ Yeh word mila nahi."

        elif action == "blacklist_add":
            added = await database.add_blacklist_word(user_id, raw)
            msg = "✅ Blacklist word added!" if added else "⚠️ Yeh word already hai."

        elif action == "blacklist_rem":
            removed = await database.remove_blacklist_word(user_id, raw)
            msg = "🗑️ Blacklist word removed!" if removed else "⚠️ Yeh word mila nahi."

        elif action == "footer_set":
            await database.set_endtext(user_id, raw)
            msg = "✅ Footer set!"

        elif action == "caption_set":
            await database.set_caption_template(user_id, raw)
            msg = "✅ Caption template set!"

        elif action == "replace_add":
            rules = []
            for part in raw.split("|"):
                part = part.strip()
                if ":" in part:
                    o, n = part.split(":", 1)
                    rules.append((o.strip(), n.strip()))
            added = await database.add_replacements(user_id, rules) if rules else 0
            msg = f"✅ {added} rule(s) saved!" if rules else "❌ Format galat tha. <code>Old:New</code> use karo."

        elif action == "replace_rem":
            olds = [w.strip() for w in raw.split("|") if w.strip()]
            removed = await database.remove_replacements(user_id, olds)
            msg = f"🗑️ {removed} rule(s) removed!" if removed else "⚠️ Koi matching rule nahi mila."

        elif action == "remword_add":
            words = [w.strip() for w in raw.split("|") if w.strip()]
            added = await database.add_remove_words(user_id, words)
            msg = f"✅ {added} word(s) added!"

        elif action == "remword_rem":
            words = [w.strip() for w in raw.split("|") if w.strip()]
            removed = await database.remove_remove_words(user_id, words)
            msg = f"🗑️ {removed} word(s) removed!" if removed else "⚠️ Koi matching word nahi mila."

        elif action == "mapping_set":
            parts = raw.split()
            if len(parts) != 2:
                msg = "❌ Format galat. Example: <code>-1001234567890 -1009876543210</code>"
            else:
                src_chat = await smart_get_chat(client, parts[0], user_id)
                tgt_chat = await smart_get_chat(client, parts[1], user_id)
                result = await database.add_target_to_source(
                    user_id, src_chat.id, tgt_chat.id, src_chat.title, tgt_chat.title
                )
                msg = "✅ Mapping set!" if result in ("created", "added") else "⚠️ Already exists!"

        elif action == "mapping_remtarget":
            parts = raw.split()
            if len(parts) != 2:
                msg = "❌ Format galat. Example: <code>-1001234567890 -1009876543210</code>"
            else:
                src_chat = await smart_get_chat(client, parts[0], user_id)
                tgt_chat = await smart_get_chat(client, parts[1], user_id)
                result = await database.remove_target_from_source(user_id, src_chat.id, tgt_chat.id)
                msg = "🗑️ Target removed!" if result == "removed" else "⚠️ Not found."

        elif action == "mapping_remsource":
            src_chat = await smart_get_chat(client, raw, user_id)
            removed = await database.remove_source(user_id, src_chat.id)
            msg = "🗑️ Source removed!" if removed else "⚠️ Not found."

        elif action == "admin_add":
            if cfg.OWNER_ID and user_id != cfg.OWNER_ID:
                msg = "🚫 Yeh sirf bot owner kar sakta hai."
            else:
                target = int(raw)
                await database.add_admin(user_id, target)
                msg = f"👑 Admin added: {target}"

        elif action in ("admin_ban", "admin_unban"):
            is_owner = bool(cfg.OWNER_ID) and user_id == cfg.OWNER_ID
            allowed = is_owner or (cfg.OWNER_ID and await database.is_admin(cfg.OWNER_ID, user_id))
            if not allowed:
                msg = "🚫 Yeh sirf owner ya admin kar sakta hai."
            else:
                target = int(raw)
                if action == "admin_ban":
                    if cfg.OWNER_ID and target == cfg.OWNER_ID:
                        msg = "❌ Owner ko ban nahi kar sakte."
                    else:
                        await database.ban_user(cfg.OWNER_ID, target)
                        from SilentXForward.forward import active_userbots
                        ub = active_userbots.pop(target, None)
                        if ub:
                            try:
                                await ub.stop()
                            except Exception:
                                pass
                        msg = f"🚫 User banned: {target}"
                else:
                    unbanned = await database.unban_user(cfg.OWNER_ID, target)
                    msg = f"✅ User unbanned: {target}" if unbanned else "⚠️ User ban list mein nahi hai."

    except ValueError:
        msg = "❌ Galat format — sahi value bhejo."
    except Exception as e:
        logger.exception("settings_menu_input_handler error")
        msg = f"❌ Error: <code>{e}</code>"

    if back_key in _MENU_RENDERERS:
        text, kb = await _MENU_RENDERERS[back_key](user_id)
        text = f"{msg}\n\n{text}" if msg else text
    else:
        text, kb = MENU_HEADER, _menu_main_markup()

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=kb)
