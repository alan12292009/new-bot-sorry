from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import MAIN_ADMIN_USERNAME

class WeeklyTop:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db

    async def show_weekly_tops(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💰 Топ по балансу", callback_data="weekly_balance"),
            InlineKeyboardButton("👥 Топ по рефералам", callback_data="weekly_referrals"),
            InlineKeyboardButton("🏰 Топ кланов", callback_data="weekly_clans"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🏆 *ЕЖЕНЕДЕЛЬНЫЕ ТОПЫ* 🏆\n\n"
            "Каждую неделю победители получают призы!\n"
            "Выберите категорию:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def show_weekly_balance(self, callback_query: types.CallbackQuery):
        top = await self.db.get_weekly_top_balance()
        
        if not top:
            await callback_query.answer("Топ еще не сформирован!", show_alert=True)
            return
        
        text = "💰 *ТОП ПО БАЛАНСУ ЗА НЕДЕЛЮ* 💰\n\n"
        
        for item in top:
            medal = "🥇" if item['rank'] == 1 else "🥈" if item['rank'] == 2 else "🥉" if item['rank'] == 3 else "🔹"
            name = item['username'] or f"ID{item['user_id']}"
            text += f"{medal} {item['rank']}. @{name} — {item['balance']}{CURR}\n"
        
        text += f"\n🏆 Победитель получает приз!\n"
        text += f"📅 Неделя: {top[0]['week_start']} - {top[0]['week_end']}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="weekly_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_weekly_referrals(self, callback_query: types.CallbackQuery):
        top = await self.db.get_weekly_top_referrals()
        
        if not top:
            await callback_query.answer("Топ еще не сформирован!", show_alert=True)
            return
        
        text = "👥 *ТОП ПО РЕФЕРАЛАМ ЗА НЕДЕЛЮ* 👥\n\n"
        
        for item in top:
            medal = "🥇" if item['rank'] == 1 else "🥈" if item['rank'] == 2 else "🥉" if item['rank'] == 3 else "🔹"
            name = item['username'] or f"ID{item['user_id']}"
            text += f"{medal} {item['rank']}. @{name} — {item['referral_count']} рефералов\n"
        
        text += f"\n🏆 Победитель получает приз!\n"
        text += f"📅 Неделя: {top[0]['week_start']} - {top[0]['week_end']}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="weekly_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_weekly_clans(self, callback_query: types.CallbackQuery):
        top = await self.db.get_weekly_top_clans()
        
        if not top:
            await callback_query.answer("Топ еще не сформирован!", show_alert=True)
            return
        
        text = "🏰 *ТОП КЛАНОВ ЗА НЕДЕЛЮ* 🏰\n\n"
        
        for item in top:
            medal = "🥇" if item['rank'] == 1 else "🥈" if item['rank'] == 2 else "🥉" if item['rank'] == 3 else "🔹"
            text += f"{medal} {item['rank']}. {item['clan_name']} [{item['clan_tag']}] — {item['total_balance']}{CURR}\n"
        
        text += f"\n🏆 Клан-победитель получает приз!\n"
        text += f"📅 Неделя: {top[0]['week_start']} - {top[0]['week_end']}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="weekly_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
