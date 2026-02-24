from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from config import *
from typing import Dict, Optional

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
    waiting_for_ban_reason = State()
    waiting_for_broadcast = State()

class AdminPanel:
    def __init__(self, bot, db: Database, payments: PaymentSystem):
        self.bot = bot
        self.db = db
        self.payments = payments

    async def check_admin(self, user_id: int) -> bool:
        return user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID

    async def admin_menu(self, message: types.Message):
        """Главное меню админ панели"""
        if not await self.check_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав!")
            return
        
        admin_balance = await self.payments.get_admin_balance()
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👥 Управление", callback_data="admin_users"),
            InlineKeyboardButton("💰 Баланс", callback_data="admin_balance"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔨 Бан-лист", callback_data="admin_banlist"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            f"🔧 *АДМИН ПАНЕЛЬ* 🔧\n\n"
            f"👑 Админ: @{MAIN_ADMIN_USERNAME}\n"
            f"💰 Баланс админа: *{admin_balance:,}{CURR}*\n\n"
            f"Выберите действие:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def give_money_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало выдачи денег"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback_query.message.edit_text("Введите ID пользователя:")
        await state.update_data(action='give')
        await AdminStates.waiting_for_user_id.set()

    async def process_user_id(self, message: types.Message, state: FSMContext):
        """Обработка ID пользователя"""
        try:
            target_id = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректный ID!")
            return
        
        user = await self.db.get_user(target_id)
        if not user:
            await message.reply("❌ Пользователь не найден!")
            await state.finish()
            return
        
        data = await state.get_data()
        await state.update_data(target_id=target_id, target_username=user['username'])
        
        if data['action'] == 'give':
            await message.reply(f"Введите сумму для выдачи:\nБаланс: {user['balance']}{CURR}")
            await AdminStates.waiting_for_amount.set()
        elif data['action'] == 'take':
            await message.reply(f"Введите сумму для списания:\nБаланс: {user['balance']}{CURR}")
            await AdminStates.waiting_for_amount.set()
        elif data['action'] == 'ban':
            await message.reply("Введите причину бана (или '-'):")
            await AdminStates.waiting_for_ban_reason.set()

    async def process_amount(self, message: types.Message, state: FSMContext):
        """Обработка суммы"""
        try:
            amount = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную сумму!")
            return
        
        data = await state.get_data()
        
        if data['action'] == 'give':
            await self.db.update_balance(data['target_id'], amount)
            await message.reply(f"✅ Выдано {amount}{CURR} пользователю @{data['target_username']}!")
        elif data['action'] == 'take':
            await self.db.update_balance(data['target_id'], -amount)
            await message.reply(f"✅ Списано {amount}{CURR} у пользователя @{data['target_username']}!")
        
        await state.finish()

    async def process_ban(self, message: types.Message, state: FSMContext):
        """Бан пользователя"""
        reason = None if message.text == '-' else message.text
        data = await state.get_data()
        
        async with self.db.pool.acquire() as conn:
            await conn.execute('UPDATE users SET is_banned = TRUE, ban_reason = $1 WHERE user_id = $2', reason, data['target_id'])
        
        await message.reply(f"✅ Пользователь @{data['target_username']} забанен!")
        await state.finish()

    async def show_banlist(self, callback_query: types.CallbackQuery):
        """Показать список забаненных"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        async with self.db.pool.acquire() as conn:
            banned = await conn.fetch('''
                SELECT user_id, username, first_name, ban_reason 
                FROM users WHERE is_banned = TRUE LIMIT 20
            ''')
        
        if not banned:
            text = "🔨 *БАН-ЛИСТ*\n\nСписок пуст"
        else:
            text = "🔨 *БАН-ЛИСТ*\n\n"
            for user in banned:
                name = user['username'] or user['first_name'] or f"ID{user['user_id']}"
                reason = user['ban_reason'] or "Без причины"
                text += f"• @{name} - {reason}\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_stats(self, callback_query: types.CallbackQuery):
        """Показать статистику"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        async with self.db.pool.acquire() as conn:
            total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
            total_balance = await conn.fetchval('SELECT COALESCE(SUM(balance), 0) FROM users')
            total_cars = await conn.fetchval('SELECT COUNT(*) FROM cars')
            total_phones = await conn.fetchval('SELECT COUNT(*) FROM phones')
            total_clans = await conn.fetchval('SELECT COUNT(*) FROM clans')
        
        admin_balance = await self.payments.get_admin_balance()
        
        text = f"📊 *СТАТИСТИКА* 📊\n\n"
        text += f"👥 Пользователей: {total_users}\n"
        text += f"💰 Общий баланс: {total_balance:,}{CURR}\n"
        text += f"💰 Баланс админа: {admin_balance:,}{CURR}\n"
        text += f"🚗 Машин: {total_cars}\n"
        text += f"📱 Телефонов: {total_phones}\n"
        text += f"🏰 Кланов: {total_clans}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def broadcast_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало рассылки"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback_query.message.edit_text("Введите текст для рассылки:")
        await AdminStates.waiting_for_broadcast.set()

    async def process_broadcast(self, message: types.Message, state: FSMContext):
        """Отправка рассылки"""
        if not await self.check_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав!")
            await state.finish()
            return
        
        text = message.text
        await message.reply("🔄 Начинаю рассылку...")
        
        async with self.db.pool.acquire() as conn:
            users = await conn.fetch('SELECT user_id FROM users WHERE is_banned = FALSE')
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await self.bot.send_message(
                    user['user_id'],
                    f"📢 *ОБЪЯВЛЕНИЕ*\n\n{text}",
                    parse_mode="Markdown"
                )
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await message.reply(f"✅ Рассылка завершена!\n📨 Отправлено: {success}\n❌ Не доставлено: {failed}")
        await state.finish()
