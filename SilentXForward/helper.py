import logging
from SilentXForward import database
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_TEXT = """<b>👋ʜᴇʟʟᴏ! ɪ ᴀᴍ ᴀᴠ_ғᴏʀᴡᴀʀᴅ_ʙᴏᴛ.\n\nɪ ᴄᴀɴ ғᴏʀᴡᴀʀᴅ ᴠɪᴅᴇᴏs ᴀɴᴅ ᴅᴏᴄᴜᴍᴇɴᴛs ғʀᴏᴍ ᴍᴜʟᴛɪᴘʟᴇ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴍᴜʟᴛɪᴘʟᴇ ᴏᴛʜᴇʀ ᴄʜᴀɴɴᴇʟs, ғɪʟᴛᴇʀɪɴɢ ᴏᴜᴛ ᴜɴᴡᴀɴᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ.!! 😍\n<blockquote>🌿 ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ : <a href="https://t.me/AV_MOVIES_WORLD">AV_MOVIES_WORLD</a></blockquote></b>"""

HELP_TEXT = """<b>ℹ️ Help Menu

I Am An Auto-Forward Bot. I Forward Files From Source Channels To Target Channels.</b>

<b>Commands:
/start - Check If I Am Alive.
/help - Show This Help Message.
/about - Show Information About Me.
/set &lt;source_id&gt; &lt;target_id&gt; - Add Target To Source
/remove_target &lt;source_id&gt; &lt;target_id&gt; - Remove A Target From Source
/remove_source &lt;source_id&gt; - Remove Source
/list - View All Set Channels 
/clear - Clear All Mappings</b>

<b>How to use:
1. Add Me To Source Channels And Target Channels As Admin.
2. Use /set command to link source to target channels.
3. I Will Automatically Forward Videos And Documents!</b>

<b>Channel: @AV_MOVIES_WORLD</b>
"""

ABOUT_TEXT = """<b><blockquote>╭────[ ᴍʏ ᴅᴇᴛᴀɪʟs ]────⍟</blockquote>
<blockquote>├⍟ 🎭 Mʏ Nᴀᴍᴇ : <a href='https://t.me/AV_Forwardz_Robot'>ᴀᴠ ғᴏʀᴡᴀʀᴅ ʙᴏᴛ</a></blockquote>
<blockquote>├⍟ 🇮🇳 Cʀᴇᴀᴛᴏʀ : <a href='https://t.me/AV_King1'>ཧᜰ꙰ꦿ➢𝐀𝐛𝔥𝕚ŞℍＥҜ༒</a></blockquote>
<blockquote>├⍟ 📚 Lɪʙʀᴀʀʏ : <a href='https://docs.pyrogram.org/'>ᴘʏʀᴏɢʀᴀᴍ</a></blockquote>
<blockquote>├⍟ 🍿 Lᴀɴɢᴜᴀɢᴇ : <a href='https://www.python.org/download/releases/3.0/'>ᴘʏᴛʜᴏɴ 𝟹</a></blockquote>
<blockquote>├⍟ 🐍 DᴀᴛᴀBᴀsᴇ : <a href='https://www.mongodb.com/'>ᴍᴏɴɢᴏ ᴅʙ</a></blockquote>
<blockquote>├⍟ ⚙️ Bᴏᴛ Sᴇʀᴠᴇʀ : <a href='https://heroku.com/'>ʜᴇʀᴏᴋᴜ</a></blockquote>
<blockquote>├⍟ 🥶 Bᴜɪʟᴅ Sᴛᴀᴛᴜs : ᴠ𝟸.𝟶 [ ꜱᴛᴀʙʟᴇ ]</blockquote>
<blockquote>├⍟ Features:</blockquote>
<blockquote>├⍟ Multi-Source to Multi-Target</blockquote>
<blockquote>├⍟ Video & Document Filter</blockquote>
<blockquote>├⍟ FloodWait Handling</blockquote>
<blockquote>├⍟ MongoDB Database</blockquote>
<blockquote>├⍟ Queue System</blockquote>
<blockquote>╰───────────────⍟</b></blockquote>"""

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/AV_MOVIES_WORLD"),
            InlineKeyboardButton("🥰 ཧᜰ꙰ꦿ➢𝐀𝐛𝔥𝕚ŞℍＥҜ༒", url="https://t.me/AV_King1")
        ]
    ]
)

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        await message.reply(
            text=START_TEXT,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=BUTTONS,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error In Start Function: {e}")

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    try:
        await message.reply(
            text=HELP_TEXT,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=BUTTONS,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error In Help Function: {e}")

@Client.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    try:
        await message.reply(
            text=ABOUT_TEXT,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=BUTTONS,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error In About Function: {e}")

@Client.on_message(filters.command("set") & filters.private)
async def set_channels(client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 3:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/set &lt;source_id&gt; &lt;target_id&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/set -1001234567890 -1009876543210</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    source = message.command[1]
    target = message.command[2]
    
    try:
        source_chat = await client.get_chat(source)
        target_chat = await client.get_chat(target)
        
        source_id = source_chat.id
        target_id = target_chat.id
        
        result = await database.add_target_to_source(
            user_id, 
            source_id, 
            target_id, 
            source_chat.title, 
            target_chat.title
        )
        
        if result == "created":
            await message.reply_text(
                f"<b>✅ New Source Created:</b>\n\n"
                f"<b>📥 Source:</b> {source_chat.title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>📤 Target:</b> {target_chat.title}\n"
                f"   <code>{target_id}</code>\n\n"
                f"🎉 Messages Will Be Forwarded!",
                parse_mode=enums.ParseMode.HTML
            )
        elif result == "added":
            await message.reply_text(
                f"<b>✅ Target Added:</b>\n\n"
                f"<b>📥 Source:</b> {source_chat.title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>📤 New Target:</b> {target_chat.title}\n"
                f"   <code>{target_id}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Already Exists:</b>\n\n"
                f"This Target Is Already Set For This Source!",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}\n\n"
            "Make sure:\n"
            "• Bot is admin in both channels\n"
            "• Channel IDs are correct",
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("remove_target") & filters.private)
async def remove_target_channel(client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 3:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/rem &lt;source_id&gt; &lt;target_id&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/rem -1001234567890 -1009876543210</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    source_input = message.command[1]
    target_input = message.command[2]
    
    try:
        source_chat = await client.get_chat(source_input)
        source_id = source_chat.id
        source_title = source_chat.title

        target_chat = await client.get_chat(target_input)
        target_id = target_chat.id
        target_title = target_chat.title
        
        result = await database.remove_target_from_source(user_id, source_id, target_id)
        
        if result == "removed":
            await message.reply_text(
                f"<b>✅ Target Removed Successfully!</b>\n\n"
                f"<b>📥 Source:</b> {source_title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"<b>🗑️ Target:</b> {target_title}\n"
                f"   <code>{target_id}</code>\n\n"
                f"Target Channel Has Been Removed From This Source Mapping.",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Not Found:</b>\n\n"
                f"<b>📥 Source:</b> {source_title}\n"
                f"<b>🗑️ Target:</b> {target_title}\n\n"
                f"No Mapping Exists For This Source-target Pair.\n\n"
                f"Use <code>/list</code> To See Your Current Mappings.",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}\n\n"
            f"Make sure both channel IDs are valid and accessible.",
            parse_mode=enums.ParseMode.HTML
        )
        
@Client.on_message(filters.command("remove_source") & filters.private)
async def remove_channel(client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        await message.reply_text(
            "<b>❌ Usage:</b> <code>/rem &lt;source_id&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/rem -1001234567890</code>",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    source = message.command[1]
    
    try:
        chat = await client.get_chat(source)
        source_id = chat.id
        
        removed = await database.remove_source(user_id, source_id)
        
        if removed:
            await message.reply_text(
                f"<b>✅ Removed:</b>\n\n"
                f"<b>📥 Source:</b> {chat.title}\n"
                f"   <code>{source_id}</code>\n\n"
                f"All Targets For This Source Have Been Removed.",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<b>⚠️ Not Found:</b>\n\n"
                f"No Targets Exists For <b>{chat.title}</b>\n\n"
                f"Use /list To See Your Mappings.",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error:</b> {e}",
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("list") & filters.private)
async def list_mappings(client, message: Message):
    user_id = message.from_user.id
    
    mappings = await database.get_user_mappings(user_id)
    
    if not mappings:
        await message.reply_text(
            "<b>❌ No mappings found!</b>\n\n"
            "Use <code>/set &lt;source_id&gt; &lt;target_id&gt;</code> to create one.",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    text = "<b>📊 Your Channel Mappings:</b>\n\n"
    
    for idx, mapping in enumerate(mappings, 1):
        source_id = mapping['source_id']
        target_ids = mapping.get('target_ids', [])
        
        try:
            source_chat = await client.get_chat(source_id)
            text += f"<b>{idx}. 📥 {source_chat.title}</b>\n"
            text += f"   <code>{source_id}</code>\n"
            text += f"   ⤵️ <b>Targets ({len(target_ids)}):</b>\n"
            
            for target_id in target_ids:
                try:
                    target_chat = await client.get_chat(target_id)
                    text += f"   • {target_chat.title} (<code>{target_id}</code>)\n"
                except:
                    text += f"   • <code>{target_id}</code> (Unable to fetch)\n"
            
            text += "\n"
        except:
            text += f"<b>{idx}.</b> <code>{source_id}</code> (Unable to fetch)\n"
            text += f"   Targets: {len(target_ids)}\n\n"
    
    text += f"<b>Total Sources:</b> {len(mappings)}"
    
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("clear") & filters.private)
async def clear_all(client, message: Message):
    user_id = message.from_user.id
    
    count = await database.clear_all_mappings(user_id)
    
    if count > 0:
        await message.reply_text(
            f"<b>✅ Cleared {count} source(s)!</b>\n\n"
            f"All Your Mappings Have Been Removed.",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<b>❌ You Don't Have Any Mappings To Clear!</b>",
            parse_mode=enums.ParseMode.HTML
        )
