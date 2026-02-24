from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from config import *
import asyncio

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
    waiting_for_ban_reason = State()
    waiting_for_broadcast = State()
    waiting_for_item_type = State()
    waiting_for_item_name = State()
    waiting_for_item_description = State()
    waiting_for_item_price = State()
    waiting_for_item_speed = State()
    waiting_for_item_camera = State()
    waiting_for_item_rooms = State()
    waiting_for_item_area = State()
    waiting_for_item_comfort = State()
    waiting_for_item_category = State()
    waiting_for_item_style = State()
    waiting_for_item_quantity = State()

class AdminPanel:
    def __init__(self, bot, db: Database, payments: PaymentSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.admin_id = MAIN_ADMIN_ID

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
            InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users"),
            InlineKeyboardButton("💰 Управление балансом", callback_data="admin_balance"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔨 Бан-лист", callback_data="admin_banlist"),
            InlineKeyboardButton("🏪 Управление магазином", callback_data="admin_shop_menu"),
            InlineKeyboardButton("🎰 Управление казино", callback_data="admin_casino"),
            InlineKeyboardButton("📦 Просмотр предметов", callback_data="admin_view_items"),
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

    # ========== УПРАВЛЕНИЕ МАГАЗИНОМ ==========

    async def show_shop_menu(self, callback_query: types.CallbackQuery):
        """Меню управления магазином"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🚗 Создать машину", callback_data="admin_create_car"),
            InlineKeyboardButton("📱 Создать телефон", callback_data="admin_create_phone"),
            InlineKeyboardButton("🏠 Создать дом", callback_data="admin_create_house"),
            InlineKeyboardButton("👕 Создать аксессуар", callback_data="admin_create_accessory"),
            InlineKeyboardButton("📋 Список предметов", callback_data="admin_items_list"),
            InlineKeyboardButton("◀️ Назад", callback_data="admin")
        )
        
        await callback_query.message.edit_text(
            "🏪 *УПРАВЛЕНИЕ МАГАЗИНОМ* 🏪\n\n"
            "Здесь вы можете создавать новые предметы для продажи.\n\n"
            "Выберите тип предмета:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # ========== СОЗДАНИЕ МАШИНЫ ==========

    async def create_car_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "🚗 *СОЗДАНИЕ МАШИНЫ*\n\n"
            "Введите название модели (например: Ferrari F8):",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='car')
        await AdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ ТЕЛЕФОНА ==========

    async def create_phone_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "📱 *СОЗДАНИЕ ТЕЛЕФОНА*\n\n"
            "Введите название модели (например: iPhone 15 Pro):",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='phone')
        await AdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ ДОМА ==========

    async def create_house_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "🏠 *
