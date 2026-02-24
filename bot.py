import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from government import Government
from clans import Clans, ClanStates
from admin import AdminPanel, AdminStates

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# База данных
db = Database(DATABASE_URL)

# Системы
payments = PaymentSystem(bot, db)
confirmations = ConfirmationSystem(bot)
government = Government(bot, db, payments, confirmations)
clans = Clans(bot, db, confirmations)
admin_panel = AdminPanel(bot, db, payments)

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    user = await db.get_user(message.from_user.id)
    if user and user['is_banned']:
        await message.reply("❌ Вы забанены!")
        return
    
    await show_main_menu(message)

async def show_main_menu(message: types.Message):
    """Главное меню"""
    user = await db.get_user(message.from_user.id)
    greeting = db.get_greeting(message.from_user.first_name or "Игрок")
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🏛️ Государство", callback_data="gov_menu"),
        InlineKeyboardButton("🏰 Кланы", callback_data="clans_menu"),
        InlineKeyboardButton("💰 Баланс", callback_data="balance")
    )
    
    if user['is_admin']:
        keyboard.add(InlineKeyboardButton("🔧 Админ панель", callback_data="admin"))
    
    keyboard.add(InlineKeyboardButton("🆘 Помощь", callback_data="help"))
    
    await message.reply(
        f"{greeting}\n\n"
        f"🎲 *{BOT_NAME} v{BOT_VERSION}* 🎲\n"
        f"💰 Баланс: *{user['balance']:,}{CURR}*\n\n"
        f"Выберите раздел:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# Обработчик callback
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    user = await db.get_user(user_id)
    if user and user['is_banned']:
        await callback_query.answer("❌ Вы забанены!", show_alert=True)
        return
    
    data = callback_query.data
    
    # Главное меню
    if data == "menu":
        await callback_query.message.delete()
        await show_main_menu(callback_query.message)
    
    # Государство
    elif data == "gov_menu":
        await government.show_government_menu(callback_query.message)
    elif data == "gov_sell_car":
        await government.show_sell_cars(callback_query)
    elif data.startswith("gov_sell_car_"):
        await government.confirm_sell_car(callback_query, state)
    elif data == "gov_sell_phone":
        await government.show_sell_phones(callback_query)
    elif data.startswith("gov_sell_phone_"):
        await government.confirm_sell_phone(callback_query, state)
    elif data == "gov_info":
        await government.show_info(callback_query)
    
    # Кланы
    elif data == "clans_menu":
        await clans.show_clans_menu(callback_query.message)
    elif data == "clan_create":
        await clans.create_clan_start(callback_query, state)
    elif data.startswith("clan_list_"):
        page = int(data.replace('clan_list_', ''))
        await clans.clan_list(callback_query, page)
    elif data.startswith("clan_view_"):
        await clans.view_clan(callback_query)
    elif data.startswith("clan_apply_"):
        await clans.apply_to_clan(callback_query, state)
    elif data.startswith("clan_join_"):
        await clans.join_open_clan(callback_query)
    
    # Баланс
    elif data == "balance":
        await show_balance(callback_query)
    
    # Админ панель
    elif data == "admin":
        await admin_panel.admin_menu(callback_query.message)
    elif data == "admin_give":
        await admin_panel.give_money_start(callback_query, state)
    
    # Помощь
    elif data == "help":
        await show_help(callback_query)
    
    # Подтверждения
    elif data.startswith("confirm_"):
        await confirmations.process_confirmation(callback_query, state)
    elif data.startswith("cancel_"):
        await confirmations.process_confirmation(callback_query, state)

async def show_balance(callback_query: types.CallbackQuery):
    """Показать баланс"""
    user = await db.get_user(callback_query.from_user.id)
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(
        f"💰 *ТВОЙ БАЛАНС* 💰\n\n"
        f"💵 Наличные: *{user['balance']:,}{CURR}*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def show_help(callback_query: types.CallbackQuery):
    """Показать помощь"""
    text = f"🆘 *ПОМОЩЬ* 🆘\n\n"
    text += f"👑 Админ: @{MAIN_ADMIN_USERNAME}\n\n"
    text += f"🏛️ *Государство* - продажа предметов (20% комиссия)\n"
    text += f"🏰 *Кланы* - создание и вступление в кланы\n"
    text += f"💰 *Баланс* - просмотр текущего баланса\n\n"
    text += f"Все комиссии идут на развитие проекта!"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Обработчики состояний
@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def admin_user_id(message: types.Message, state: FSMContext):
    await admin_panel.process_user_id(message, state)

@dp.message_handler(state=AdminStates.waiting_for_amount)
async def admin_amount(message: types.Message, state: FSMContext):
    await admin_panel.process_amount(message, state)

@dp.message_handler(state=AdminStates.waiting_for_ban_reason)
async def admin_ban_reason(message: types.Message, state: FSMContext):
    await admin_panel.process_ban(message, state)

@dp.message_handler(state=ClanStates.waiting_for_clan_name)
async def clan_name(message: types.Message, state: FSMContext):
    await clans.process_clan_name(message, state)

@dp.message_handler(state=ClanStates.waiting_for_clan_tag)
async def clan_tag(message: types.Message, state: FSMContext):
    await clans.process_clan_tag(message, state)

@dp.message_handler(state=ClanStates.waiting_for_clan_description)
async def clan_description(message: types.Message, state: FSMContext):
    await clans.process_clan_description(message, state)

@dp.message_handler(state=ClanStates.waiting_for_application_text)
async def clan_application(message: types.Message, state: FSMContext):
    await clans.process_application(message, state)

# Специальные обработчики для подтверждений
@dp.callback_query_handler(lambda c: c.data == 'CREATE_CLAN_CONFIRM', state='*')
async def create_clan_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await clans.execute_create_clan(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_CAR_CONFIRM', state='*')
async def sell_car_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await government.execute_sell_car(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_PHONE_CONFIRM', state='*')
async def sell_phone_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await government.execute_sell_phone(callback_query, state)

# Запуск
async def on_startup(dp):
    await db.connect()
    await db.create_tables()
    
    me = await bot.me
    logger.info(f"✅ Бот {BOT_NAME} v{BOT_VERSION} запущен!")
    logger.info(f"👤 Username: @{me.username}")
    logger.info(f"👑 Админ: @{MAIN_ADMIN_USERNAME}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)