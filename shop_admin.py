from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import *

class ShopAdminStates(StatesGroup):
    waiting_for_item_type = State()
    waiting_for_item_name = State()
    waiting_for_item_description = State()
    waiting_for_item_price = State()
    waiting_for_item_speed = State()
    waiting_for_item_camera = State()
    waiting_for_item_rooms = State()
    waiting_for_item_area = State()
    waiting_for_item_comfort = State()
    waiting_for_item_photo = State()
    waiting_for_item_quantity = State()

class ShopAdmin:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.admin_id = MAIN_ADMIN_ID
        
        # Хранилище созданных предметов (в реальном проекте нужно сохранять в БД)
        self.custom_items = {
            'cars': [],
            'phones': [],
            'houses': [],
            'accessories': []
        }

    async def check_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        from config import ADMIN_IDS
        return user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID

    async def show_shop_admin_menu(self, message: types.Message):
        """Меню управления магазином для админа"""
        if not await self.check_admin(message.from_user.id):
            await message.reply("❌ У вас нет прав администратора!")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🚗 Создать машину", callback_data="shop_admin_car"),
            InlineKeyboardButton("📱 Создать телефон", callback_data="shop_admin_phone"),
            InlineKeyboardButton("🏠 Создать дом", callback_data="shop_admin_house"),
            InlineKeyboardButton("👕 Создать аксессуар", callback_data="shop_admin_accessory"),
            InlineKeyboardButton("📋 Список предметов", callback_data="shop_admin_list"),
            InlineKeyboardButton("◀️ Назад", callback_data="admin")
        )
        
        await message.reply(
            "🔧 *АДМИН ПАНЕЛЬ УПРАВЛЕНИЯ МАГАЗИНОМ* 🔧\n\n"
            "Здесь вы можете создавать новые предметы для магазина.\n\n"
            "Выберите тип предмета:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # ========== СОЗДАНИЕ МАШИНЫ ==========
    
    async def create_car_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало создания машины"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "🚗 *СОЗДАНИЕ МАШИНЫ*\n\n"
            "Введите название модели:",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='car')
        await ShopAdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ ТЕЛЕФОНА ==========
    
    async def create_phone_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало создания телефона"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "📱 *СОЗДАНИЕ ТЕЛЕФОНА*\n\n"
            "Введите название модели:",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='phone')
        await ShopAdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ ДОМА ==========
    
    async def create_house_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало создания дома"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "🏠 *СОЗДАНИЕ ДОМА*\n\n"
            "Введите название дома:",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='house')
        await ShopAdminStates.waiting_for_item_name.set()

    # ========== СОЗДАНИЕ АКСЕССУАРА ==========
    
    async def create_accessory_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало создания аксессуара"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "👕 *СОЗДАНИЕ АКСЕССУАРА*\n\n"
            "Введите название аксессуара:",
            parse_mode="Markdown"
        )
        await state.update_data(item_type='accessory')
        await ShopAdminStates.waiting_for_item_name.set()

    # ========== ОБЩИЙ ПРОЦЕСС СОЗДАНИЯ ==========
    
    async def process_item_name(self, message: types.Message, state: FSMContext):
        """Обработка названия предмета"""
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_name=message.text)
        
        if item_type == 'car':
            await message.reply("Введите описание машины:")
            await ShopAdminStates.waiting_for_item_description.set()
        elif item_type == 'phone':
            await message.reply("Введите описание телефона:")
            await ShopAdminStates.waiting_for_item_description.set()
        elif item_type == 'house':
            await message.reply("Введите описание дома:")
            await ShopAdminStates.waiting_for_item_description.set()
        elif item_type == 'accessory':
            await message.reply("Введите описание аксессуара:")
            await ShopAdminStates.waiting_for_item_description.set()

    async def process_item_description(self, message: types.Message, state: FSMContext):
        """Обработка описания предмета"""
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_description=message.text)
        
        await message.reply("Введите цену предмета:")
        await ShopAdminStates.waiting_for_item_price.set()

    async def process_item_price(self, message: types.Message, state: FSMContext):
        """Обработка цены предмета"""
        try:
            price = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную цену!")
            return
        
        data = await state.get_data()
        item_type = data['item_type']
        
        await state.update_data(item_price=price)
        
        if item_type == 'car':
            await message.reply("Введите максимальную скорость машины (км/ч):")
            await ShopAdminStates.waiting_for_item_speed.set()
        elif item_type == 'phone':
            await message.reply("Введите количество мегапикселей камеры:")
            await ShopAdminStates.waiting_for_item_camera.set()
        elif item_type == 'house':
            await message.reply("Введите количество комнат:")
            await ShopAdminStates.waiting_for_item_rooms.set()
        elif item_type == 'accessory':
            await message.reply("Введите количество аксессуаров для продажи:")
            await ShopAdminStates.waiting_for_item_quantity.set()

    async def process_item_speed(self, message: types.Message, state: FSMContext):
        """Обработка скорости машины"""
        try:
            speed = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную скорость!")
            return
        
        await state.update_data(item_speed=speed)
        await message.reply("Введите количество машин для продажи:")
        await ShopAdminStates.waiting_for_item_quantity.set()

    async def process_item_camera(self, message: types.Message, state: FSMContext):
        """Обработка камеры телефона"""
        try:
            camera = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное значение!")
            return
        
        await state.update_data(item_camera=camera)
        await message.reply("Введите количество телефонов для продажи:")
        await ShopAdminStates.waiting_for_item_quantity.set()

    async def process_item_rooms(self, message: types.Message, state: FSMContext):
        """Обработка количества комнат в доме"""
        try:
            rooms = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное количество!")
            return
        
        await state.update_data(item_rooms=rooms)
        await message.reply("Введите площадь дома (м²):")
        await ShopAdminStates.waiting_for_item_area.set()

    async def process_item_area(self, message: types.Message, state: FSMContext):
        """Обработка площади дома"""
        try:
            area = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную площадь!")
            return
        
        await state.update_data(item_area=area)
        await message.reply("Введите уровень комфорта (0-100):")
        await ShopAdminStates.waiting_for_item_comfort.set()

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
        await ShopAdminStates.waiting_for_item_quantity.set()

    async def process_item_quantity(self, message: types.Message, state: FSMContext):
        """Обработка количества предметов"""
        try:
            quantity = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное количество!")
            return
        
        data = await state.get_data()
        
        # Сохраняем предмет
        item = {
            'id': len(self.custom_items[data['item_type'] + 's']) + 1,
            'name': data['item_name'],
            'description': data['item_description'],
            'price': data['item_price'],
            'quantity': quantity,
            'created_by': message.from_user.id,
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Добавляем специфические поля
        if data['item_type'] == 'car':
            item['speed'] = data['item_speed']
        elif data['item_type'] == 'phone':
            item['camera'] = data['item_camera']
        elif data['item_type'] == 'house':
            item['rooms'] = data['item_rooms']
            item['area'] = data['item_area']
            item['comfort'] = data['item_comfort']
        
        self.custom_items[data['item_type'] + 's'].append(item)
        
        # Формируем сообщение о создании
        type_names = {
            'car': '🚗 Машина',
            'phone': '📱 Телефон',
            'house': '🏠 Дом',
            'accessory': '👕 Аксессуар'
        }
        
        result_text = f"✅ *{type_names[data['item_type']]} успешно создана!*\n\n"
        result_text += f"📝 Название: {item['name']}\n"
        result_text += f"📋 Описание: {item['description']}\n"
        result_text += f"💰 Цена: {item['price']}{CURR}\n"
        result_text += f"📦 Количество: {quantity}\n"
        
        if data['item_type'] == 'car':
            result_text += f"⚡ Скорость: {item['speed']} км/ч\n"
        elif data['item_type'] == 'phone':
            result_text += f"📷 Камера: {item['camera']} МП\n"
        elif data['item_type'] == 'house':
            result_text += f"🚪 Комнат: {item['rooms']}\n"
            result_text += f"📏 Площадь: {item['area']} м²\n"
            result_text += f"✨ Комфорт: {item['comfort']}%\n"
        
        await message.reply(result_text, parse_mode="Markdown")
        await state.finish()

    async def show_items_list(self, callback_query: types.CallbackQuery):
        """Показать список созданных предметов"""
        if not await self.check_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Нет прав!", show_alert=True)
            return
        
        text = "📋 *СОЗДАННЫЕ ПРЕДМЕТЫ*\n\n"
        
        if self.custom_items['cars']:
            text += "*🚗 Машины:*\n"
            for item in self.custom_items['cars']:
                text += f"  • {item['name']} - {item['price']}{CURR} ({item['quantity']} шт)\n"
            text += "\n"
        
        if self.custom_items['phones']:
            text += "*📱 Телефоны:*\n"
            for item in self.custom_items['phones']:
                text += f"  • {item['name']} - {item['price']}{CURR} ({item['quantity']} шт)\n"
            text += "\n"
        
        if self.custom_items['houses']:
            text += "*🏠 Дома:*\n"
            for item in self.custom_items['houses']:
                text += f"  • {item['name']} - {item['price']}{CURR} ({item['quantity']} шт)\n"
            text += "\n"
        
        if self.custom_items['accessories']:
            text += "*👕 Аксессуары:*\n"
            for item in self.custom_items['accessories']:
                text += f"  • {item['name']} - {item['price']}{CURR} ({item['quantity']} шт)\n"
            text += "\n"
        
        if not any(self.custom_items.values()):
            text += "Пока нет созданных предметов"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="shop_admin"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
