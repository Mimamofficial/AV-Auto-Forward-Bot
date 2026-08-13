import config
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient(config.MONGO_URI)
db = mongo_client[config.DB_NAME]

channel_mappings = db['channel_mappings']
userbot_sessions = db['userbot_sessions']
user_settings    = db['user_settings']    # delay, on/off, endtext, filters
admins_col       = db['admins']
banned_col       = db['banned_users']
stats_col        = db['forward_stats']
bot_users_col    = db['bot_users']        # ✅ tracks EVERY user who has started the bot (for broadcast)


# ==================== BOT USERS (for broadcast) ====================

async def save_user(user_id: int):
    """Har /start karne wale user ko yahan record karo — broadcast isi list se jaata hai."""
    from datetime import datetime
    await bot_users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "last_seen": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}},
        upsert=True
    )

async def get_all_user_ids() -> list:
    cursor = bot_users_col.find({}, {"user_id": 1})
    docs = await cursor.to_list(length=None)
    return [d["user_id"] for d in docs if d.get("user_id")]


# ==================== CHANNEL MAPPINGS ====================

async def get_user_mappings(user_id):
    cursor = channel_mappings.find({"user_id": user_id})
    return await cursor.to_list(length=None)

async def get_mapping_by_source(user_id, source_id):
    return await channel_mappings.find_one({"user_id": user_id, "source_id": source_id})

async def add_target_to_source(user_id, source_id, target_id, source_title, target_title):
    existing = await channel_mappings.find_one({"user_id": user_id, "source_id": source_id})
    if existing:
        if target_id not in existing.get('target_ids', []):
            await channel_mappings.update_one(
                {"user_id": user_id, "source_id": source_id},
                {"$push": {"target_ids": target_id}, "$set": {"source_title": source_title}}
            )
            return "added"
        return "exists"
    else:
        await channel_mappings.insert_one({
            "user_id": user_id, "source_id": source_id,
            "target_ids": [target_id], "source_title": source_title
        })
        return "created"

async def remove_target_from_source(user_id, source_id, target_id):
    result = await channel_mappings.update_one(
        {"user_id": user_id, "source_id": source_id, "target_ids": {"$exists": True}},
        {"$pull": {"target_ids": target_id}}
    )
    if result.modified_count > 0:
        mapping = await channel_mappings.find_one({"user_id": user_id, "source_id": source_id})
        if not mapping or not mapping.get('target_ids'):
            await channel_mappings.delete_one({"user_id": user_id, "source_id": source_id})
        return "removed"
    return "not_found"

async def remove_source(user_id, source_id):
    result = await channel_mappings.delete_one({"user_id": user_id, "source_id": source_id})
    return result.deleted_count > 0

async def get_all_targets_for_source(source_id):
    cursor = channel_mappings.find({"source_id": source_id})
    mappings = await cursor.to_list(length=None)
    return [{"user_id": m['user_id'], "target_ids": m.get('target_ids', [])} for m in mappings]

async def clear_all_mappings(user_id):
    result = await channel_mappings.delete_many({"user_id": user_id})
    return result.deleted_count

async def remove_invalid_target(target_id: int):
    """
    Jab CHANNEL_INVALID error aaye — us target_id ko
    saare users ke mappings se automatically remove karo.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Saare mappings se yeh target_id pull karo
        result = await channel_mappings.update_many(
            {"target_ids": target_id},
            {"$pull": {"target_ids": target_id}}
        )
        # Agar kisi mapping mein ab koi target nahi bachaa toh woh mapping bhi delete karo
        await channel_mappings.delete_many({"target_ids": {"$size": 0}})
        logger.warning(f"Auto-removed invalid target {target_id} from {result.modified_count} mapping(s)")
    except Exception as e:
        logger.error(f"Failed to remove invalid target {target_id}: {e}")


# ==================== USERBOT SESSIONS ====================

async def save_userbot_session(user_id: int, session_string: str, phone: str):
    from datetime import datetime
    await userbot_sessions.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "session_string": session_string,
                  "phone": phone, "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}},
        upsert=True
    )

async def get_userbot_session(user_id: int):
    return await userbot_sessions.find_one({"user_id": user_id})

async def delete_userbot_session(user_id: int) -> bool:
    result = await userbot_sessions.delete_one({"user_id": user_id})
    return result.deleted_count > 0

async def get_all_userbot_sessions():
    cursor = userbot_sessions.find({})
    return await cursor.to_list(length=None)


# ==================== USER SETTINGS ====================

async def _get_settings(user_id: int) -> dict:
    doc = await user_settings.find_one({"user_id": user_id})
    return doc or {}

async def _update_settings(user_id: int, data: dict):
    await user_settings.update_one({"user_id": user_id}, {"$set": data}, upsert=True)

# ── Forwarding ON/OFF ──
async def set_forwarding(user_id: int, enabled: bool):
    await _update_settings(user_id, {"forwarding_enabled": enabled})

async def is_forwarding_enabled(user_id: int) -> bool:
    doc = await _get_settings(user_id)
    return doc.get("forwarding_enabled", True)  # default ON

# ── Delay ──
async def set_delay(user_id: int, seconds: float):
    await _update_settings(user_id, {"delay": seconds})

async def get_delay(user_id: int) -> float:
    doc = await _get_settings(user_id)
    return doc.get("delay", 0.1)  # default 0.1s

# ── Keyword Filters ──
async def add_filter(user_id: int, word: str) -> bool:
    doc = await _get_settings(user_id)
    filters_list = doc.get("filters", [])
    word = word.lower().strip()
    if word in filters_list:
        return False
    filters_list.append(word)
    await _update_settings(user_id, {"filters": filters_list})
    return True

async def remove_filter(user_id: int, word: str) -> bool:
    doc = await _get_settings(user_id)
    filters_list = doc.get("filters", [])
    word = word.lower().strip()
    if word not in filters_list:
        return False
    filters_list.remove(word)
    await _update_settings(user_id, {"filters": filters_list})
    return True

async def get_filters(user_id: int) -> list:
    doc = await _get_settings(user_id)
    return doc.get("filters", [])

async def clear_filters(user_id: int):
    """✅ NEW: interactive settings menu ke 'Clear All' button ke liye."""
    await _update_settings(user_id, {"filters": []})

# ── Blacklist Words (jin words wale messages SKIP honge) ──
async def add_blacklist_word(user_id: int, word: str) -> bool:
    doc = await _get_settings(user_id)
    bl = doc.get("blacklist", [])
    word = word.lower().strip()
    if word in bl:
        return False
    bl.append(word)
    await _update_settings(user_id, {"blacklist": bl})
    return True

async def remove_blacklist_word(user_id: int, word: str) -> bool:
    doc = await _get_settings(user_id)
    bl = doc.get("blacklist", [])
    word = word.lower().strip()
    if word not in bl:
        return False
    bl.remove(word)
    await _update_settings(user_id, {"blacklist": bl})
    return True

async def get_blacklist(user_id: int) -> list:
    doc = await _get_settings(user_id)
    return doc.get("blacklist", [])

async def clear_blacklist(user_id: int):
    await _update_settings(user_id, {"blacklist": []})

# ── End Text (Footer) ──
async def set_endtext(user_id: int, text: str):
    await _update_settings(user_id, {"endtext": text})

async def remove_endtext(user_id: int):
    await user_settings.update_one({"user_id": user_id}, {"$unset": {"endtext": ""}}, upsert=True)

async def get_endtext(user_id: int) -> str | None:
    doc = await _get_settings(user_id)
    return doc.get("endtext", None)

# ── All settings for a user (used in /status) ──
async def get_all_settings(user_id: int) -> dict:
    return await _get_settings(user_id)

# ── Caption Style ──
# Styles: "normal", "bold", "italic", "underline", "bold_italic", "mono"
async def set_caption_style(user_id: int, style: str):
    await _update_settings(user_id, {"caption_style": style})

async def get_caption_style(user_id: int) -> str:
    doc = await _get_settings(user_id)
    return doc.get("caption_style", "normal")  # default = normal


# ==================== CUSTOM CAPTION TEMPLATE ====================

async def set_caption_template(user_id: int, template: str):
    await _update_settings(user_id, {"caption_template": template})

async def get_caption_template(user_id: int) -> str | None:
    doc = await _get_settings(user_id)
    return doc.get("caption_template", None)

async def remove_caption_template(user_id: int):
    await user_settings.update_one({"user_id": user_id}, {"$unset": {"caption_template": ""}}, upsert=True)


# ==================== WORD REPLACE (Old:New rules) ====================

async def add_replacements(user_id: int, rules: list) -> int:
    """rules = list of (old, new) tuples. Same 'old' (case-insensitive) gets updated."""
    doc = await _get_settings(user_id)
    existing = doc.get("replacements", [])  # list of [old, new]
    lower_keys = {r[0].lower(): i for i, r in enumerate(existing)}
    added = 0
    for old, new in rules:
        old = old.strip()
        new = new.strip()
        if not old:
            continue
        key = old.lower()
        if key in lower_keys:
            existing[lower_keys[key]] = [old, new]
        else:
            existing.append([old, new])
            lower_keys[key] = len(existing) - 1
            added += 1
    await _update_settings(user_id, {"replacements": existing})
    return added

async def remove_replacements(user_id: int, olds: list) -> int:
    doc = await _get_settings(user_id)
    existing = doc.get("replacements", [])
    lower_targets = {o.strip().lower() for o in olds if o.strip()}
    new_list = [r for r in existing if r[0].lower() not in lower_targets]
    removed = len(existing) - len(new_list)
    await _update_settings(user_id, {"replacements": new_list})
    return removed

async def get_replacements(user_id: int) -> list:
    doc = await _get_settings(user_id)
    return [tuple(r) for r in doc.get("replacements", [])]

async def clear_replacements(user_id: int):
    await _update_settings(user_id, {"replacements": []})


# ==================== WORD REMOVE (caption cleanup) ====================

async def add_remove_words(user_id: int, words: list) -> int:
    doc = await _get_settings(user_id)
    existing = doc.get("remove_words", [])
    lower_existing = {w.lower() for w in existing}
    added = 0
    for w in words:
        w = w.strip()
        if w and w.lower() not in lower_existing:
            existing.append(w)
            lower_existing.add(w.lower())
            added += 1
    await _update_settings(user_id, {"remove_words": existing})
    return added

async def remove_remove_words(user_id: int, words: list) -> int:
    doc = await _get_settings(user_id)
    existing = doc.get("remove_words", [])
    lower_targets = {w.strip().lower() for w in words if w.strip()}
    new_list = [w for w in existing if w.lower() not in lower_targets]
    removed = len(existing) - len(new_list)
    await _update_settings(user_id, {"remove_words": new_list})
    return removed

async def get_remove_words(user_id: int) -> list:
    doc = await _get_settings(user_id)
    return doc.get("remove_words", [])

async def clear_remove_words(user_id: int):
    await _update_settings(user_id, {"remove_words": []})


# ==================== RESET ALL SETTINGS ====================

async def reset_all_settings(user_id: int):
    """
    ✅ NEW: /reset command ke liye — SAB KUCH default pe wapas: caption
    template, footer/prefix (endtext), filters, replace-rules, remove-words
    AUR source/target channel mappings — sab delete ho jaayenge.
    """
    await user_settings.update_one(
        {"user_id": user_id},
        {
            "$unset": {"caption_template": "", "endtext": ""},
            "$set": {"filters": [], "replacements": [], "remove_words": [], "blacklist": []},
        },
        upsert=True,
    )
    await clear_all_mappings(user_id)


# ==================== ADMIN SYSTEM ====================

async def add_admin(owner_id: int, target_user_id: int):
    await admins_col.update_one(
        {"owner_id": owner_id, "admin_id": target_user_id},
        {"$set": {"owner_id": owner_id, "admin_id": target_user_id}},
        upsert=True
    )

async def remove_admin(owner_id: int, target_user_id: int) -> bool:
    result = await admins_col.delete_one({"owner_id": owner_id, "admin_id": target_user_id})
    return result.deleted_count > 0

async def get_admins(owner_id: int) -> list:
    cursor = admins_col.find({"owner_id": owner_id})
    docs = await cursor.to_list(length=None)
    return [d["admin_id"] for d in docs]

async def is_admin(owner_id: int, user_id: int) -> bool:
    if owner_id == user_id:
        return True
    doc = await admins_col.find_one({"owner_id": owner_id, "admin_id": user_id})
    return doc is not None

# ── Ban System ──
async def ban_user(owner_id: int, target_user_id: int):
    await banned_col.update_one(
        {"owner_id": owner_id, "banned_id": target_user_id},
        {"$set": {"owner_id": owner_id, "banned_id": target_user_id}},
        upsert=True
    )

async def unban_user(owner_id: int, target_user_id: int) -> bool:
    result = await banned_col.delete_one({"owner_id": owner_id, "banned_id": target_user_id})
    return result.deleted_count > 0

async def is_banned(owner_id: int, user_id: int) -> bool:
    doc = await banned_col.find_one({"owner_id": owner_id, "banned_id": user_id})
    return doc is not None


# ==================== STATS ====================

async def increment_forward_count(user_id: int, count: int = 1):
    await stats_col.update_one(
        {"user_id": user_id},
        {"$inc": {"total_forwarded": count}},
        upsert=True
    )

async def get_forward_count(user_id: int) -> int:
    doc = await stats_col.find_one({"user_id": user_id})
    return doc.get("total_forwarded", 0) if doc else 0

async def reset_forward_count(user_id: int):
    await stats_col.update_one({"user_id": user_id}, {"$set": {"total_forwarded": 0}}, upsert=True)
