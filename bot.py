import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

# Функция для закрытия старых сессий
def close_old_sessions():
    """Принудительно закрываем старые сессии бота"""
    try:
        from config import BOT_TOKEN
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.post(url, json={"offset": -1, "timeout": 0})
        if response.status_code == 200:
            logging.info("✅ Старые сессии бота закрыты")
    except Exception as e:
        logging.error(f"❌ Ошибка при закрытии сессий: {e}")

# Вызываем функцию перед запуском
close_old_sessions()

from config import *
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from government import Government
from clans import Clans, ClanStates
from admin import AdminPanel, AdminStates
from cars import CarShop, CarStates
from phones import PhoneShop, PhoneStates
from crypto import CryptoMarket, CryptoStates
from trading import Trading, TradingStates
from weekly_top import WeeklyTop
from houses import HouseShop, HouseStates
from casino import Casino, CasinoStates
from accessories import AccessoryShop, AccessoryStates

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
car_shop = CarShop(bot, db, confirmations)
phone_shop = PhoneShop(bot, db, confirmations)
crypto = CryptoMarket(bot, db, payments, confirmations)
trading = Trading(bot, db, payments, confirmations)
weekly_top = WeeklyTop(bot, db)
house_shop = HouseShop(bot, db, payments, confirmations)
casino = Casino(bot, db, payments, confirmations)
accessory_shop = AccessoryShop(bot, db, payments, confirmations)

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    args = message.get_args()
    referrer_id = None
    
    if args and args.isdigit():
        referrer_id = int(args)
        if referrer_id == message.from_user.id:
            referrer_id = None
    
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

# ГЛАВНОЕ МЕНЮ СО ВСЕМИ КНОПКАМИ
async def show_main_menu(message: types.Message):
    """Главное меню со всеми кнопками"""
    user = await db.get_user(message.from_user.id)
    greeting = db.get_greeting(message.from_user.first_name or "Игрок")
    
    # СОЗДАЕМ КЛАВИАТУРУ СО ВСЕМИ КНОПКАМИ
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # ОСНОВНЫЕ РАЗДЕЛЫ
    keyboard.add(
        InlineKeyboardButton("🎰 Казино", callback_data="casino_menu"),
        InlineKeyboardButton("🏛️ Государство", callback_data="gov_menu"),
        InlineKeyboardButton("🏰 Кланы", callback_data="clans_menu"),
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("👥 Рефералы", callback_data="referrals")
    )
    
    # МАГАЗИНЫ И ПОКУПКИ
    keyboard.add(
        InlineKeyboardButton("🚗 Купить машину", callback_data="car_shop"),
        InlineKeyboardButton("📱 Купить телефон", callback_data="phone_shop"),
        InlineKeyboardButton("👕 Аксессуары", callback_data="accessories_menu"),
        InlineKeyboardButton("🏠 Купить дом", callback_data="houses_menu"),
        InlineKeyboardButton("💎 Крипто-биржа", callback_data="crypto_menu"),
        InlineKeyboardButton("📊 Крипто-портфель", callback_data="crypto_wallet")
    )
    
    # ТОРГОВЛЯ И ОБМЕН
    keyboard.add(
        InlineKeyboardButton("💱 Перевод денег", callback_data="transfer_money"),
        InlineKeyboardButton("🤝 Обмен предметами", callback_data="trade_items"),
        InlineKeyboardButton("📦 Инвентарь", callback_data="inventory"),
        InlineKeyboardButton("🏠 Мои дома", callback_data="my_houses"),
        InlineKeyboardButton("👕 Мои аксессуары", callback_data="my_accessories")
    )
    
    # СТАТИСТИКА И ТОПЫ
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        InlineKeyboardButton("🏆 Топ игроков", callback_data="top"),
        InlineKeyboardButton("📈 Еженедельные топы", callback_data="weekly_menu")
    )
    
    # АДМИН ПАНЕЛЬ (только для админов)
    if user['is_admin']:
        keyboard.add(InlineKeyboardButton("🔧 Админ панель", callback_data="admin"))
    
    # ПОМОЩЬ
    keyboard.add(InlineKeyboardButton("🆘 Помощь", callback_data="help"))
    
    await message.reply(
        f"{greeting}\n\n"
        f"🎲 *{BOT_NAME} v{BOT_VERSION}* 🎲\n"
        f"💰 Баланс: *{user['balance']:,}{CURR}*\n\n"
        f"Выберите раздел:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# Обработчик всех callback
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    
    user = await db.get_user(user_id)
    if user and user['is_banned']:
        await callback_query.answer("❌ Вы забанены!", show_alert=True)
        return
    
    data = callback_query.data
    
    # ========== ГЛАВНОЕ МЕНЮ ==========
    if data == "menu":
        await callback_query.message.delete()
        await show_main_menu(callback_query.message)
    
    # ========== БАЛАНС ==========
    elif data == "balance":
        await show_balance(callback_query)
    
    elif data == "referrals":
        await show_referrals(callback_query)
    
    # ========== КАЗИНО ==========
    elif data == "casino_menu":
        await casino.show_casino_menu(callback_query.message)
    elif data == "casino_dice":
        await casino.play_dice(callback_query)
    elif data == "casino_roulette":
        await casino.play_roulette(callback_query)
    elif data.startswith("roulette_"):
        await casino.roulette_bet_start(callback_query, state)
    elif data == "casino_duel":
        await casino.duel_start(callback_query, state)
    elif data == "casino_jackpot":
        await casino.show_jackpot(callback_query)
    elif data == "casino_stats":
        await casino.show_casino_stats(callback_query)
    elif data == "casino_top":
        await casino.show_casino_top(callback_query)
    elif data.startswith("duel_accept_"):
        await casino.process_duel_response(callback_query, state)
    elif data.startswith("duel_reject_"):
        await casino.process_duel_response(callback_query, state)
    elif data.startswith("duel_roll_"):
        await casino.process_duel_roll(callback_query)
    
    # ========== ГОСУДАРСТВО ==========
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
    
    # ========== КЛАНЫ ==========
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
    
    # ========== МАШИНЫ ==========
    elif data == "car_shop":
        await car_shop.show_car_shop(callback_query.message)
    elif data.startswith("car_buy_"):
        await car_shop.select_car_brand(callback_query, state)
    elif data == "my_cars":
        await car_shop.show_my_cars(callback_query)
    
    # ========== ТЕЛЕФОНЫ ==========
    elif data == "phone_shop":
        await phone_shop.show_phone_shop(callback_query.message)
    elif data.startswith("phone_buy_"):
        await phone_shop.select_phone_brand(callback_query, state)
    elif data == "my_phones":
        await phone_shop.show_my_phones(callback_query)
    
    # ========== АКСЕССУАРЫ ==========
    elif data == "accessories_menu":
        await accessory_shop.show_accessories_menu(callback_query.message)
    elif data == "acc_all":
        await accessory_shop.show_all(callback_query)
    elif data.startswith("acc_category_"):
        category = data.replace('acc_category_', '')
        await accessory_shop.show_by_category(callback_query, category)
    elif data.startswith("acc_view_"):
        await accessory_shop.view_accessory(callback_query, state)
    elif data.startswith("acc_buy_"):
        await accessory_shop.confirm_buy(callback_query, state)
    elif data == "my_accessories":
        await accessory_shop.show_my_accessories(callback_query)
    
    # ========== ДОМА ==========
    elif data == "houses_menu":
        await house_shop.show_houses_menu(callback_query.message)
    elif data == "houses_all":
        await house_shop.show_houses_by_category(callback_query, 'all')
    elif data == "houses_econom":
        await house_shop.show_houses_by_category(callback_query, 'econom')
    elif data == "houses_business":
        await house_shop.show_houses_by_category(callback_query, 'business')
    elif data == "houses_elite":
        await house_shop.show_houses_by_category(callback_query, 'elite')
    elif data.startswith("house_view_"):
        await house_shop.view_house(callback_query, state)
    elif data.startswith("house_buy_"):
        await house_shop.confirm_buy_house(callback_query, state)
    elif data == "my_houses":
        await house_shop.show_my_houses(callback_query)
    elif data == "sell_house_menu":
        await house_shop.sell_house_menu(callback_query)
    elif data.startswith("sell_house_"):
        await house_shop.confirm_sell_house(callback_query, state)
    
    # ========== КРИПТОВАЛЮТА ==========
    elif data == "crypto_menu":
        await crypto.show_crypto_market(callback_query.message)
    elif data == "crypto_wallet":
        await crypto.show_wallet(callback_query)
    elif data.startswith("crypto_select_"):
        await crypto.select_crypto(callback_query, state)
    elif data == "crypto_buy":
        await crypto.buy_crypto_start(callback_query, state)
    elif data == "crypto_sell":
        await crypto.sell_crypto_start(callback_query, state)
    
    # ========== ТОРГОВЛЯ ==========
    elif data == "transfer_money":
        await trading.transfer_money_start(callback_query, state)
    elif data == "trade_items":
        await trading.trade_items_start(callback_query, state)
    elif data.startswith("trade_"):
        await trading.process_trade_item(callback_query, state)
    
    # ========== ИНВЕНТАРЬ ==========
    elif data == "inventory":
        await show_inventory(callback_query)
    
    # ========== СТАТИСТИКА ==========
    elif data == "stats":
        await show_stats(callback_query)
    elif data == "top":
        await show_top(callback_query)
    
    # ========== ЕЖЕНЕДЕЛЬНЫЕ ТОПЫ ==========
    elif data == "weekly_menu":
        await weekly_top.show_weekly_tops(callback_query.message)
    elif data == "weekly_balance":
        await weekly_top.show_weekly_balance(callback_query)
    elif data == "weekly_referrals":
        await weekly_top.show_weekly_referrals(callback_query)
    elif data == "weekly_clans":
        await weekly_top.show_weekly_clans(callback_query)
    
    # ========== АДМИН ПАНЕЛЬ ==========
    elif data == "admin":
        await admin_panel.admin_menu(callback_query.message)
    elif data == "admin_shop_menu":
        await admin_panel.show_shop_menu(callback_query)
    elif data == "admin_create_car":
        await admin_panel.create_car_start(callback_query, state)
    elif data == "admin_create_phone":
        await admin_panel.create_phone_start(callback_query, state)
    elif data == "admin_create_house":
        await admin_panel.create_house_start(callback_query, state)
    elif data == "admin_create_accessory":
        await admin_panel.create_accessory_start(callback_query, state)
    elif data == "admin_items_list":
        await admin_panel.view_items(callback_query)
    elif data == "admin_give":
        await admin_panel.give_money_start(callback_query, state)
    elif data == "admin_banlist":
        await admin_panel.show_banlist(callback_query)
    elif data == "admin_stats":
        await admin_panel.show_stats(callback_query)
    
    # ========== ПОМОЩЬ ==========
    elif data == "help":
        await show_help(callback_query)
    
    # ========== ПОДТВЕРЖДЕНИЯ ==========
    elif data.startswith("confirm_"):
        await confirmations.process_confirmation(callback_query, state)
    elif data.startswith("cancel_"):
        await confirmations.process_confirmation(callback_query, state)

# Функция показа баланса
async def show_balance(callback_query: types.CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    
    # Получаем крипто-портфель
    crypto_wallet = await db.get_user_crypto_wallet(callback_query.from_user.id)
    crypto_value = 0
    for item in crypto_wallet:
        crypto_value += float(item['amount']) * float(item['price'])
    
    # Получаем машины и телефоны
    cars = await db.get_user_cars(callback_query.from_user.id)
    phones = await db.get_user_phones(callback_query.from_user.id)
    
    # Получаем дома
    async with db.pool.acquire() as conn:
        houses = await conn.fetch('SELECT * FROM houses WHERE user_id = $1', callback_query.from_user.id)
    
    # Получаем аксессуары
    accessories = await db.get_user_accessories(callback_query.from_user.id)
    
    cars_value = sum(car['price'] for car in cars)
    phones_value = sum(phone['price'] for phone in phones)
    houses_value = sum(house['price'] for house in houses)
    accessories_value = sum(acc['price'] for acc in accessories)
    
    text = f"💰 *ТВОЙ БАЛАНС* 💰\n\n"
    text += f"💵 Наличные: *{user['balance']:,}{CURR}*\n"
    text += f"💎 Криптовалюта: *{crypto_value:,.2f}{CURR}*\n"
    text += f"🚗 Машины: *{cars_value:,}{CURR}*\n"
    text += f"📱 Телефоны: *{phones_value:,}{CURR}*\n"
    text += f"🏠 Дома: *{houses_value:,}{CURR}*\n"
    text += f"👕 Аксессуары: *{accessories_value:,}{CURR}*\n"
    text += f"💎 Общий капитал: *{user['balance'] + crypto_value + cars_value + phones_value + houses_value + accessories_value:,.2f}{CURR}*"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Функция показа рефералов
async def show_referrals(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user = await db.get_user(user_id)
    
    bot_username = (await bot.me).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    text = f"👥 *РЕФЕРАЛЬНАЯ СИСТЕМА* 👥\n\n"
    text += f"🔗 Твоя ссылка:\n`{referral_link}`\n\n"
    text += f"💰 Заработано: *{user['referral_earnings']:,}{CURR}*\n"
    text += f"👥 Приглашено: *{user['referral_count']}*\n\n"
    text += f"*Бонусы:*\n"
    text += f"• За друга: 2000{CURR}\n"
    text += f"• За друга друга: 1000{CURR}\n"
    text += f"• 10% от выигрыша рефералов"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Функция показа инвентаря
async def show_inventory(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    cars = await db.get_user_cars(user_id)
    phones = await db.get_user_phones(user_id)
    crypto = await db.get_user_crypto_wallet(user_id)
    accessories = await db.get_user_accessories(user_id)
    
    async with db.pool.acquire() as conn:
        houses = await conn.fetch('SELECT * FROM houses WHERE user_id = $1', user_id)
    
    text = "📦 *ТВОЙ ИНВЕНТАРЬ* 📦\n\n"
    
    if cars:
        text += "*🚗 Машины:*\n"
        for car in cars:
            text += f"• {car['model']} - {car['price']:,}{CURR}\n"
        text += "\n"
    
    if phones:
        text += "*📱 Телефоны:*\n"
        for phone in phones:
            text += f"• {phone['model']} - {phone['price']:,}{CURR}\n"
        text += "\n"
    
    if houses:
        text += "*🏠 Дома:*\n"
        for house in houses:
            text += f"• {house['house_name']} - {house['price']:,}{CURR}\n"
        text += "\n"
    
    if accessories:
        text += "*👕 Аксессуары:*\n"
        for acc in accessories:
            text += f"• {acc['accessory_name']} - {acc['price']:,}{CURR}\n"
        text += "\n"
    
    if crypto:
        text += "*💎 Криптовалюта:*\n"
        for item in crypto:
            value = float(item['amount']) * float(item['price'])
            text += f"• {item['symbol']}: {float(item['amount']):.8f} ({value:,.2f}{CURR})\n"
        text += "\n"
    
    if not cars and not phones and not houses and not crypto and not accessories:
        text += "У тебя пока нет предметов!"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Функция показа статистики
async def show_stats(callback_query: types.CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    
    # Получаем количество предметов
    cars = await db.get_user_cars(callback_query.from_user.id)
    phones = await db.get_user_phones(callback_query.from_user.id)
    accessories = await db.get_user_accessories(callback_query.from_user.id)
    
    async with db.pool.acquire() as conn:
        houses = await conn.fetch('SELECT COUNT(*) as count FROM houses WHERE user_id = $1', callback_query.from_user.id)
        house_count = houses[0]['count'] if houses else 0
    
    text = f"📊 *ТВОЯ СТАТИСТИКА* 📊\n\n"
    text += f"📅 В боте с: *{user['created_at'].strftime('%d.%m.%Y')}*\n"
    text += f"💰 Баланс: *{user['balance']:,}{CURR}*\n"
    text += f"👥 Рефералов: *{user['referral_count']}*\n"
    text += f"💎 Заработано с рефералов: *{user['referral_earnings']:,}{CURR}*\n"
    text += f"🚗 Машин: *{len(cars)}*\n"
    text += f"📱 Телефонов: *{len(phones)}*\n"
    text += f"🏠 Домов: *{house_count}*\n"
    text += f"👕 Аксессуаров: *{len(accessories)}*"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Функция показа топа игроков
async def show_top(callback_query: types.CallbackQuery):
    async with db.pool.acquire() as conn:
        top = await conn.fetch('''
            SELECT username, first_name, balance 
            FROM users 
            WHERE is_banned = FALSE 
            ORDER BY balance DESC 
            LIMIT 10
        ''')
    
    text = "🏆 *ТОП ИГРОКОВ* 🏆\n\n"
    
    for i, player in enumerate(top, 1):
        name = player['username'] or player['first_name'] or f"Игрок {i}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{name} - {player['balance']:,}{CURR}\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# Функция показа помощи
async def show_help(callback_query: types.CallbackQuery):
    text = f"🆘 *ПОМОЩЬ* 🆘\n\n"
    text += f"👑 Админ: @{MAIN_ADMIN_USERNAME}\n\n"
    text += f"🎰 *Казино* - игры, дуэли, джекпот\n"
    text += f"🏛️ *Государство* - продажа предметов (20% комиссия)\n"
    text += f"🏰 *Кланы* - создание и вступление в кланы\n"
    text += f"🚗 *Машины* - покупка автомобилей\n"
    text += f"📱 *Телефоны* - покупка телефонов\n"
    text += f"🏠 *Дома* - покупка недвижимости\n"
    text += f"👕 *Аксессуары* - стильные вещи\n"
    text += f"💎 *Криптовалюта* - торговля криптой\n"
    text += f"💱 *Переводы* - перевод денег друзьям\n"
    text += f"🤝 *Обмен* - обмен предметами\n"
    text += f"📦 *Инвентарь* - все ваши предметы\n"
    text += f"👥 *Рефералы* - приглашай друзей и зарабатывай\n\n"
    text += f"Все комиссии идут на развитие проекта!"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
    
    await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ========== ОБРАБОТЧИКИ СОСТОЯНИЙ ==========

@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def admin_user_id(message: types.Message, state: FSMContext):
    await admin_panel.process_user_id(message, state)

@dp.message_handler(state=AdminStates.waiting_for_amount)
async def admin_amount(message: types.Message, state: FSMContext):
    await admin_panel.process_amount(message, state)

@dp.message_handler(state=AdminStates.waiting_for_ban_reason)
async def admin_ban_reason(message: types.Message, state: FSMContext):
    await admin_panel.process_ban(message, state)

@dp.message_handler(state=AdminStates.waiting_for_broadcast)
async def admin_broadcast(message: types.Message, state: FSMContext):
    await admin_panel.process_broadcast(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_name)
async def admin_item_name(message: types.Message, state: FSMContext):
    await admin_panel.process_item_name(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_description)
async def admin_item_description(message: types.Message, state: FSMContext):
    await admin_panel.process_item_description(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_price)
async def admin_item_price(message: types.Message, state: FSMContext):
    await admin_panel.process_item_price(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_speed)
async def admin_item_speed(message: types.Message, state: FSMContext):
    await admin_panel.process_item_speed(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_camera)
async def admin_item_camera(message: types.Message, state: FSMContext):
    await admin_panel.process_item_camera(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_rooms)
async def admin_item_rooms(message: types.Message, state: FSMContext):
    await admin_panel.process_item_rooms(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_area)
async def admin_item_area(message: types.Message, state: FSMContext):
    await admin_panel.process_item_area(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_comfort)
async def admin_item_comfort(message: types.Message, state: FSMContext):
    await admin_panel.process_item_comfort(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_category)
async def admin_item_category(message: types.Message, state: FSMContext):
    await admin_panel.process_item_category(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_style)
async def admin_item_style(message: types.Message, state: FSMContext):
    await admin_panel.process_item_style(message, state)

@dp.message_handler(state=AdminStates.waiting_for_item_quantity)
async def admin_item_quantity(message: types.Message, state: FSMContext):
    await admin_panel.process_item_quantity(message, state)

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

@dp.message_handler(state=CarStates.waiting_for_car_brand)
async def car_brand(message: types.Message, state: FSMContext):
    await car_shop.process_car_brand(message, state)

@dp.message_handler(state=PhoneStates.waiting_for_phone_brand)
async def phone_brand(message: types.Message, state: FSMContext):
    await phone_shop.process_phone_brand(message, state)

@dp.message_handler(state=CryptoStates.waiting_for_buy_amount)
async def crypto_buy_amount(message: types.Message, state: FSMContext):
    await crypto.process_buy_amount(message, state)

@dp.message_handler(state=CryptoStates.waiting_for_sell_amount)
async def crypto_sell_amount(message: types.Message, state: FSMContext):
    await crypto.process_sell_amount(message, state)

@dp.message_handler(state=TradingStates.waiting_for_username)
async def trading_username(message: types.Message, state: FSMContext):
    await trading.process_username(message, state)

@dp.message_handler(state=TradingStates.waiting_for_amount)
async def trading_amount(message: types.Message, state: FSMContext):
    await trading.process_amount(message, state)

@dp.message_handler(state=HouseStates.waiting_for_house_confirm)
async def house_confirm(message: types.Message, state: FSMContext):
    await house_shop.process_house_confirm(message, state)

@dp.message_handler(state=CasinoStates.waiting_for_dice_bet)
async def casino_dice_bet(message: types.Message, state: FSMContext):
    await casino.process_dice_bet(message, state)

@dp.message_handler(state=CasinoStates.waiting_for_roulette_bet)
async def casino_roulette_bet(message: types.Message, state: FSMContext):
    await casino.process_roulette_bet(message, state)

@dp.message_handler(state=CasinoStates.waiting_for_roulette_number)
async def casino_roulette_number(message: types.Message, state: FSMContext):
    await casino.process_roulette_number(message, state)

@dp.message_handler(state=CasinoStates.waiting_for_duel_username)
async def casino_duel_username(message: types.Message, state: FSMContext):
    await casino.process_duel_username(message, state)

@dp.message_handler(state=CasinoStates.waiting_for_duel_bet)
async def casino_duel_bet(message: types.Message, state: FSMContext):
    await casino.process_duel_bet(message, state)

@dp.message_handler(state=AccessoryStates.waiting_for_accessory_confirm)
async def accessory_confirm(message: types.Message, state: FSMContext):
    await accessory_shop.process_confirm(message, state)

# ========== ОБРАБОТЧИКИ ПОДТВЕРЖДЕНИЙ ==========

@dp.callback_query_handler(lambda c: c.data == 'CREATE_CLAN_CONFIRM', state='*')
async def create_clan_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await clans.execute_create_clan(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_CAR_CONFIRM', state='*')
async def sell_car_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await government.execute_sell_car(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_PHONE_CONFIRM', state='*')
async def sell_phone_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await government.execute_sell_phone(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'BUY_CAR_CONFIRM', state='*')
async def buy_car_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await car_shop.execute_buy_car(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'BUY_PHONE_CONFIRM', state='*')
async def buy_phone_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await phone_shop.execute_buy_phone(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'BUY_CRYPTO_CONFIRM', state='*')
async def buy_crypto_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await crypto.execute_buy_crypto(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_CRYPTO_CONFIRM', state='*')
async def sell_crypto_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await crypto.execute_sell_crypto(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'TRANSFER_CONFIRM', state='*')
async def transfer_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await trading.execute_transfer(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'TRADE_ITEM_CONFIRM', state='*')
async def trade_item_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await trading.execute_trade(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'BUY_HOUSE_CONFIRM', state='*')
async def buy_house_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await house_shop.execute_buy_house(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'SELL_HOUSE_CONFIRM', state='*')
async def sell_house_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await house_shop.execute_sell_house(callback_query, state)

@dp.callback_query_handler(lambda c: c.data == 'BUY_ACCESSORY_CONFIRM', state='*')
async def buy_accessory_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    await accessory_shop.execute_buy(callback_query, state)

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
