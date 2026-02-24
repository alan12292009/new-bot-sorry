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
            "🏠 *СОЗДАНИЕ ДОМА*\n\n"
            "Введите название дома (например: Особняк в горах):",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='house')
        await AdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ АКСЕССУАРА ==========

    async def create_accessory_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "👕 *СОЗДАНИЕ АКСЕССУАРА*\n\n"
            "Введите название аксессуара (например: Rolex Submariner):",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='accessory')
        await AdminStates.waiting_for_item_name.set()

    # ========== ОБЩИЕ ШАГИ СОЗДАНИЯ ==========

    async def process_item_name(self, message: types.Message, state: FSMContext):
        """Обработка названия предмета"""
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_name=message.text)
        
        await message.reply("Введите описание предмета:")
        await AdminStates.waiting_for_item_description.set()

    async def process_item_description(self, message: types.Message, state: FSMContext):
        """Обработка описания предмета"""
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_description=message.text)
        
        await message.reply("Введите цену предмета:")
        await AdminStates.waiting_for_item_price.set()

    async def process_item_price(self, message: types.Message, state: FSMContext):
        """Обработка цены"""
        try:
            price = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную цену!")
            return
        
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_price=price)
        
        if item_type == 'car':
            await message.reply("Введите максимальную скорость (км/ч):")
            await AdminStates.waiting_for_item_speed.set()
        elif item_type == 'phone':
            await message.reply("Введите количество мегапикселей камеры:")
            await AdminStates.waiting_for_item_camera.set()
        elif item_type == 'house':
            await message.reply("Введите количество комнат:")
            await AdminStates.waiting_for_item_rooms.set()
        elif item_type == 'accessory':
            await message.reply("Введите категорию (очки/часы/обувь/одежда/украшения):")
            await AdminStates.waiting_for_item_category.set()

    async def process_item_speed(self, message: types.Message, state: FSMContext):
        """Обработка скорости машины"""
        try:
            speed = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную скорость!")
            return
        
        await state.update_data(item_speed=speed)
        await message.reply("Введите количество машин для продажи:")
        await AdminStates.waiting_for_item_quantity.set()

    async def process_item_camera(self, message: types.Message, state: FSMContext):
        """Обработка камеры телефона"""
        try:
            camera = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное значение!")
            return
        
        await state.update_data(item_camera=camera)
        await message.reply("Введите количество телефонов для продажи:")
        await AdminStates.waiting_for_item_quantity.set()

    async def process_item_rooms(self, message: types.Message, state: FSMContext):
        """Обработка комнат дома"""
        try:
            rooms = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное количество!")
            return
        
        await state.update_data(item_rooms=rooms)
        await message.reply("Введите площадь дома (м²):")
        await AdminStates.waiting_for_item_area.set()

    async def process_item_area(self, message: types.Message, state: FSMContext):
        """Обработка площади дома"""
        try:
            area = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную площадь!")
            return
        
        await state.update_data(item_area=area)
        await message.reply("Введите уровень комфорта (0-100):")
        await AdminStates.waiting_for_item_comfort.set()

    async def process_item_comfort(self, message: types.Message, state: FSMContext):
        """Обработка комфорта дома"""
        try:
            comfort = int(message.text)
            if comfort < 0 or comfort > 100:
                raise ValueError
        except ValueError:
            await message.reply("❌ Введите число от 0 до 100!")
            return
        
        await state.update_data(item_comfort=comfort)
        await message.reply("Введите количество домов для продажи:")
        await AdminStates.waiting_for_item_quantity.set()

    async def process_item_category(self, message: types.Message, state: FSMContext):
        """Обработка категории аксессуара"""
        category = message.text.lower()
        valid_categories = ['очки', 'часы', 'обувь', 'одежда', 'украшения', 'головные уборы']
        
        if category not in valid_categories:
            await message.reply(f"❌ Выберите из: {', '.join(valid_categories)}")
            return
        
        await state.update_data(item_category=category)
        await message.reply("Введите уровень стиля (0-100):")
        await AdminStates.waiting_for_item_style.set()

    async def process_item_style(self, message: types.Message, state: FSMContext):
        """Обработка стиля аксессуара"""
        try:
            style = int(message.text)
            if style < 0 or style > 100:
                raise ValueError
        except ValueError:
            await message.reply("❌ Введите число от 0 до 100!")
            return
        
        await state.update_data(item_style=style)
        await message.reply("Введите количество аксессуаров для продажи:")
        await AdminStates.waiting_for_item_quantity.set()

    async def process_item_quantity(self, message: types.Message, state: FSMContext):
        """Финальный шаг - создание предмета"""
        try:
            quantity = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное количество!")
            return
        
        data = await state.get_data()
        item_type = data['item_type']
        
        # Создаем предмет в зависимости от типа
        if item_type == 'car':
            for i in range(quantity):
                await self.db.add_car(
                    user_id=0,  # 0 означает что машина в магазине, а не у пользователя
                    brand=data['item_name'].split()[0] if ' ' in data['item_name'] else data['item_name'],
                    model=data['item_name'],
                    price=data['item_price'],
                    speed=data['item_speed'],
                    description=data['item_description'],
                    is_custom=True,
                    created_by=message.from_user.id
                )
            result_text = f"✅ Создано {quantity} машин '{data['item_name']}'"
            
        elif item_type == 'phone':
            for i in range(quantity):
                await self.db.add_phone(
                    user_id=0,
                    brand=data['item_name'].split()[0] if ' ' in data['item_name'] else data['item_name'],
                    model=data['item_name'],
                    price=data['item_price'],
                    camera=data['item_camera'],
                    description=data['item_description'],
                    is_custom=True,
                    created_by=message.from_user.id
                )
            result_text = f"✅ Создано {quantity} телефонов '{data['item_name']}'"
            
        elif item_type == 'house':
            house_data = {
                'id': random.randint(1000, 9999),
                'name': data['item_name'],
                'description': data['item_description'],
                'price': data['item_price'],
                'rooms': data['item_rooms'],
                'area': data['item_area'],
                'comfort': data['item_comfort'],
                'is_custom': True,
                'created_by': message.from_user.id
            }
            for i in range(quantity):
                await self.db.add_house(0, house_data)
            result_text = f"✅ Создано {quantity} домов '{data['item_name']}'"
            
        elif item_type == 'accessory':
            accessory_data = {
                'id': random.randint(1000, 9999),
                'name': data['item_name'],
                'description': data['item_description'],
                'price': data['item_price'],
                'category': data['item_category'],
                'style': data['item_style'],
                'is_custom': True,
                'created_by': message.from_user.id
            }
            for i in range(quantity):
                await self.db.add_accessory(0, accessory_data)
            result_text = f"✅ Создано {quantity} аксессуаров '{data['item_name']}'"
        
        await message.reply(result_text)
        await state.finish()

    # ========== ПРОСМОТР ПРЕДМЕТОВ ==========

    async def view_items(self, callback_query: types.CallbackQuery):
        """Просмотр всех предметов в магазине"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        cars = await self.db.get_all_cars()
        
        text = "📦 *ВСЕ ПРЕДМЕТЫ В МАГАЗИНЕ*\n\n"
        
        if cars:
            text += "*🚗 Машины:*\n"
            for car in cars[:5]:
                text += f"  • {car['model']} - {car['price']}{CURR}"
                if car['user_id'] == 0:
                    text += " [В МАГАЗИНЕ]"
                text += "\n"
            text += "\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_shop_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    # ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========

    async def give_money_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback_query.message.edit_text("Введите ID пользователя:")
        await state.update_data(action='give')
        await AdminStates.waiting_for_user_id.set()

    async def process_user_id(self, message: types.Message, state: FSMContext):
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
        reason = None if message.text == '-' else message.text
        data = await state.get_data()
        
        async with self.db.pool.acquire() as conn:
            await conn.execute('UPDATE users SET is_banned = TRUE, ban_reason = $1 WHERE user_id = $2', reason, data['target_id'])
        
        await message.reply(f"✅ Пользователь @{data['target_username']} забанен!")
        await state.finish()

    async def show_banlist(self, callback_query: types.CallbackQuery):
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
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_stats(self, callback_query: types.CallbackQuery):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        async with self.db.pool.acquire() as conn:
            total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
            total_balance = await conn.fetchval('SELECT COALESCE(SUM(balance), 0) FROM users')
            total_cars = await conn.fetchval('SELECT COUNT(*) FROM cars')
            total_phones = await conn.fetchval('SELECT COUNT(*) FROM phones')
            total_houses = await conn.fetchval('SELECT COUNT(*) FROM houses')
            total_accessories = await conn.fetchval('SELECT COUNT(*) FROM accessories')
            total_clans = await conn.fetchval('SELECT COUNT(*) FROM clans')
        
        admin_balance = await self.payments.get_admin_balance()
        
        text = f"📊 *СТАТИСТИКА* 📊\n\n"
        text += f"👥 Пользователей: {total_users}\n"
        text += f"💰 Общий баланс: {total_balance:,}{CURR}\n"
        text += f"💰 Баланс админа: {admin_balance:,}{CURR}\n"
        text += f"🚗 Машин: {total_cars}\n"
        text += f"📱 Телефонов: {total_phones}\n"
        text += f"🏠 Домов: {total_houses}\n"
        text += f"👕 Аксессуаров: {total_accessories}\n"
        text += f"🏰 Кланов: {total_clans}"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def broadcast_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        await callback_query.message.edit_text("Введите текст для рассылки:")
        await AdminStates.waiting_for_broadcast.set()

    async def process_broadcast(self, message: types.Message, state: FSMContext):
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
