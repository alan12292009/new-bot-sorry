from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import *
import datetime
import asyncio

class ClubStates(StatesGroup):
    waiting_for_nickname = State()

class AFKClub:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.active_members = {}  # Активные участники клуба
        self.hourly_rate = 200  # 200$ в час
        self.min_hours_after_registration = 2  # Минимум 2 часа после регистрации

    async def show_club_menu(self, message: types.Message):
        """Показать меню клуба"""
        user_id = message.from_user.id
        user = await self.db.get_user(user_id)
        
        # Проверяем, прошло ли 2 часа после регистрации
        now = datetime.datetime.now()
        reg_time = user['created_at']
        hours_passed = (now - reg_time).total_seconds() / 3600
        
        if hours_passed < self.min_hours_after_registration:
            hours_left = self.min_hours_after_registration - hours_passed
            await message.reply(
                f"⏳ *КЛУБ ЕЩЕ НЕ ДОСТУПЕН*\n\n"
                f"Клуб откроется через *{hours_left:.1f}* часов после регистрации.\n"
                f"Осталось подождать: *{int(hours_left)}* ч {int((hours_left % 1) * 60)} мин",
                parse_mode="Markdown"
            )
            return
        
        # Проверяем, активен ли уже в клубе
        is_active = user_id in self.active_members
        
        status_text = "✅ *В КЛУБЕ* (получаешь 200$/час)" if is_active else "❌ *НЕ В КЛУБЕ*"
        time_in_club = ""
        if is_active:
            joined_at = self.active_members[user_id]['joined_at']
            time_in_club_seconds = (now - joined_at).total_seconds()
            hours = int(time_in_club_seconds // 3600)
            minutes = int((time_in_club_seconds % 3600) // 60)
            time_in_club = f"⏱ В клубе: *{hours}* ч *{minutes}* мин"
        
        text = f"🎮 *AFK ZONE - КЛУБ*\n\n"
        text += f"{status_text}\n"
        text += f"{time_in_club}\n\n"
        text += f"💰 Каждый час в клубе: *+{self.hourly_rate}{CURR}*\n"
        text += f"⏳ Минимальное время после регистрации: *{self.min_hours_after_registration}* часа\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if not is_active:
            keyboard.add(InlineKeyboardButton("✅ Войти в клуб", callback_data="club_enter"))
        else:
            keyboard.add(InlineKeyboardButton("❌ Выйти из клуба", callback_data="club_leave"))
            keyboard.add(InlineKeyboardButton("💰 Забрать накопленное", callback_data="club_claim"))
        
        keyboard.add(InlineKeyboardButton("📊 Моя статистика", callback_data="club_stats"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="menu"))
        
        await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)

    async def enter_club(self, callback_query: types.CallbackQuery):
        """Вход в клуб"""
        user_id = callback_query.from_user.id
        
        if user_id in self.active_members:
            await callback_query.answer("❌ Вы уже в клубе!", show_alert=True)
            return
        
        self.active_members[user_id] = {
            'joined_at': datetime.datetime.now(),
            'last_claim': datetime.datetime.now(),
            'earned': 0
        }
        
        await callback_query.message.edit_text(
            f"✅ *ВЫ ВОШЛИ В КЛУБ\\!*\n\n"
            f"Теперь вы будете получать *{self.hourly_rate}{CURR}* каждый час\\!\n"
            f"Не забывайте заходить и забирать накопленное\\!",
            parse_mode="MarkdownV2"
        )
        
        # Запускаем таймер для начисления
        asyncio.create_task(self.hourly_income(user_id))

    async def leave_club(self, callback_query: types.CallbackQuery):
        """Выход из клуба"""
        user_id = callback_query.from_user.id
        
        if user_id not in self.active_members:
            await callback_query.answer("❌ Вы не в клубе!", show_alert=True)
            return
        
        # Забираем последнее накопленное перед выходом
        await self.claim_earnings(user_id)
        
        del self.active_members[user_id]
        
        await callback_query.message.edit_text(
            "❌ *ВЫ ВЫШЛИ ИЗ КЛУБА*\n\n"
            "Приходите еще!",
            parse_mode="Markdown"
        )

    async def claim_earnings(self, callback_query: types.CallbackQuery = None, user_id: int = None):
        """Забрать накопленные деньги"""
        if callback_query:
            user_id = callback_query.from_user.id
        
        if user_id not in self.active_members:
            if callback_query:
                await callback_query.answer("❌ Вы не в клубе!", show_alert=True)
            return 0
        
        member = self.active_members[user_id]
        now = datetime.datetime.now()
        time_passed = (now - member['last_claim']).total_seconds() / 3600
        hours_passed = int(time_passed)
        
        if hours_passed < 1:
            if callback_query:
                next_claim_minutes = 60 - int((time_passed % 1) * 60)
                await callback_query.answer(
                    f"⏳ Следующее получение через {next_claim_minutes} мин",
                    show_alert=True
                )
            return 0
        
        earnings = hours_passed * self.hourly_rate
        member['earned'] += earnings
        member['last_claim'] = now
        
        # Начисляем деньги
        await self.db.update_balance(user_id, earnings)
        
        if callback_query:
            await callback_query.answer(
                f"✅ Вы получили {earnings}{CURR} за {hours_passed} час(ов)!",
                show_alert=True
            )
        
        return earnings

    async def hourly_income(self, user_id: int):
        """Автоматическое начисление каждый час"""
        while user_id in self.active_members:
            await asyncio.sleep(3600)  # 1 час
            if user_id in self.active_members:
                await self.claim_earnings(user_id=user_id)
                
                # Уведомление пользователю
                try:
                    await self.bot.send_message(
                        user_id,
                        f"⏰ *НАЧИСЛЕНИЕ В КЛУБЕ*\n\n"
                        f"Вы получили *{self.hourly_rate}{CURR}* за час в клубе!",
                        parse_mode="Markdown"
                    )
                except:
                    pass

    async def show_stats(self, callback_query: types.CallbackQuery):
        """Показать статистику в клубе"""
        user_id = callback_query.from_user.id
        
        if user_id not in self.active_members:
            await callback_query.answer("❌ Вы не в клубе!", show_alert=True)
            return
        
        member = self.active_members[user_id]
        now = datetime.datetime.now()
        
        total_time = (now - member['joined_at']).total_seconds() / 3600
        hours = int(total_time)
        minutes = int((total_time % 1) * 60)
        
        time_since_last = (now - member['last_claim']).total_seconds() / 3600
        next_claim_minutes = 60 - int((time_since_last % 1) * 60)
        
        text = f"📊 *СТАТИСТИКА В КЛУБЕ*\n\n"
        text += f"⏱ Всего в клубе: *{hours}* ч *{minutes}* мин\n"
        text += f"💰 Всего заработано: *{member['earned']}{CURR}*\n"
        text += f"⏳ До следующего получения: *{next_claim_minutes}* мин\n"
        text += f"💵 В час: *{self.hourly_rate}{CURR}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="club_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
