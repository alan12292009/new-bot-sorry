from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *
import random

class AccessoryStates(StatesGroup):
    waiting_for_accessory_confirm = State()

class AccessoryShop:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations
        
        # Стандартные аксессуары
        self.default_accessories = [
            {
                'id': 1,
                'name': '👓 Солнцезащитные очки',
                'description': 'Стильные очки от Gucci',
                'price': 50000,
                'category': 'очки',
                'style': 50
            },
            {
                'id': 2,
                'name': '⌚ Rolex Submariner',
                'description': 'Элитные швейцарские часы',
                'price': 500000,
                'category': 'часы',
                'style': 90
            },
            {
                'id': 3,
                'name': '👞 Туфли Gucci',
                'description': 'Итальянская обувь ручной работы',
                'price': 150000,
                'category': 'обувь',
                'style': 70
            },
            {
                'id': 4,
                'name': '🧥 Кожаная куртка',
                'description': 'Натуральная кожа, ручная работа',
                'price': 200000,
                'category': 'одежда',
                'style': 80
            },
            {
                'id': 5,
                'name': '💍 Золотая цепочка',
                'description': '18 карат, итальянское золото',
                'price': 300000,
                'category': 'украшения',
                'style': 85
            },
            {
                'id': 6,
                'name': '🧢 Бейсболка Supreme',
                'description': 'Лимитированная коллекция',
                'price': 30000,
                'category': 'головные уборы',
                'style': 60
            },
            {
                'id': 7,
                'name': '👝 Сумка Louis Vuitton',
                'description': 'Лимитированная серия',
                'price': 450000,
                'category': 'аксессуары',
                'style': 95
            },
            {
                'id': 8,
                'name': '💎 Бриллиантовые серьги',
                'description': '2 карата, чистота IF',
                'price': 800000,
                'category': 'украшения',
                'style': 98
            }
        ]
        
        # Здесь будут храниться кастомные аксессуары от админа
        self.custom_accessories = []

    def get_all_accessories(self):
        """Получить все аксессуары (стандартные + кастомные)"""
        return self.default_accessories + self.custom_accessories

    async def show_accessories_menu(self, message: types.Message):
        """Главное меню магазина аксессуаров"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👓 Очки", callback_data="acc_category_glasses"),
            InlineKeyboardButton("⌚ Часы", callback_data="acc_category_watches"),
            InlineKeyboardButton("👞 Обувь", callback_data="acc_category_shoes"),
            InlineKeyboardButton("🧥 Одежда", callback_data="acc_category_clothes"),
            InlineKeyboardButton("💍 Украшения", callback_data="acc_category_jewelry"),
            InlineKeyboardButton("🧢 Головные уборы", callback_data="acc_category_hats"),
            InlineKeyboardButton("📋 Все аксессуары", callback_data="acc_all"),
            InlineKeyboardButton("👤 Мои аксессуары", callback_data="my_accessories"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "👕 *МАГАЗИН АКСЕССУАРОВ* 👕\n\n"
            "Выберите категорию:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def show_by_category(self, callback_query: types.CallbackQuery, category: str):
        """Показать аксессуары по категории"""
        category_map = {
            'glasses': 'очки',
            'watches': 'часы',
            'shoes': 'обувь',
            'clothes': 'одежда',
            'jewelry': 'украшения',
            'hats': 'головные уборы'
        }
        
        cat_name = category_map.get(category, category)
        all_items = self.get_all_accessories()
        items = [i for i in all_items if i.get('category') == cat_name]
        
        if not items:
            await callback_query.answer("❌ В этой категории пока нет товаров!", show_alert=True)
            return
        
        text = f"👕 *{cat_name.upper()}*\n\n"
        
        for item in items:
            text += f"{item['name']}\n"
            text += f"   📝 {item['description']}\n"
            text += f"   💰 {item['price']:,}{CURR}\n"
            text += f"   ✨ Стиль: {item['style']}%\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for item in items:
            keyboard.add(InlineKeyboardButton(
                f"{item['name']} - {item['price']:,}{CURR}",
                callback_data=f"acc_view_{item['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="accessories_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_all(self, callback_query: types.CallbackQuery):
        """Показать все аксессуары"""
        items = self.get_all_accessories()
        
        text = "👕 *ВСЕ АКСЕССУАРЫ*\n\n"
        
        for item in items:
            text += f"{item['name']}\n"
            text += f"   📝 {item['description']}\n"
            text += f"   💰 {item['price']:,}{CURR}\n"
            text += f"   ✨ Стиль: {item['style']}%\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for item in items:
            keyboard.add(InlineKeyboardButton(
                f"{item['name']} - {item['price']:,}{CURR}",
                callback_data=f"acc_view_{item['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="accessories_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def view_accessory(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Просмотр конкретного аксессуара"""
        item_id = int(callback_query.data.replace('acc_view_', ''))
        
        all_items = self.get_all_accessories()
        item = next((i for i in all_items if i['id'] == item_id), None)
        
        if not item:
            await callback_query.answer("❌ Товар не найден!", show_alert=True)
            return
        
        user = await self.db.get_user(callback_query.from_user.id)
        
        text = f"{item['name']}\n\n"
        text += f"📝 {item['description']}\n\n"
        text += f"💰 Цена: {item['price']:,}{CURR}\n"
        text += f"✨ Стиль: {item['style']}%\n\n"
        text += f"💳 Ваш баланс: {user['balance']:,}{CURR}\n"
        
        can_afford = user['balance'] >= item['price']
        status = "✅ Доступно для покупки" if can_afford else "❌ Недостаточно средств"
        text += status
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        if can_afford:
            keyboard.add(InlineKeyboardButton("✅ Купить", callback_data=f"acc_buy_{item['id']}"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="acc_all"))
        
        await state.update_data(accessory=item)
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def confirm_buy(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждение покупки"""
        item_id = int(callback_query.data.replace('acc_buy_', ''))
        
        all_items = self.get_all_accessories()
        item = next((i for i in all_items if i['id'] == item_id), None)
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'buy_accessory',
            {
                'text': f"Покупка аксессуара:\n\n"
                        f"{item['name']}\n"
                        f"💰 Цена: {item['price']:,}{CURR}\n\n"
                        f"Подтверждаете покупку?",
                'user_id': callback_query.from_user.id,
                'item': item
            },
            'BUY_ACCESSORY_CONFIRM',
            'CANCEL'
        )

    async def execute_buy(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение покупки"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        item = confirmed['item']
        
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', confirmed['user_id'])
                if user['balance'] < item['price']:
                    await callback_query.message.edit_text("❌ Недостаточно средств!")
                    await state.finish()
                    return
                
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', 
                                  item['price'], confirmed['user_id'])
                
                # Сохраняем аксессуар в отдельную таблицу (нужно создать)
                await conn.execute('''
                    INSERT INTO accessories (user_id, accessory_id, accessory_name, price, category, style)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', confirmed['user_id'], item['id'], item['name'], item['price'], 
                    item['category'], item['style'])
        
        await callback_query.message.edit_text(
            f"✅ Вы купили {item['name']} за {item['price']:,}{CURR}!"
        )
        await state.finish()

    async def show_my_accessories(self, callback_query: types.CallbackQuery):
        """Показать мои аксессуары"""
        user_id = callback_query.from_user.id
        
        async with self.db.pool.acquire() as conn:
            accessories = await conn.fetch('SELECT * FROM accessories WHERE user_id = $1', user_id)
        
        if not accessories:
            await callback_query.answer("❌ У вас нет аксессуаров!", show_alert=True)
            return
        
        text = "👕 *МОИ АКСЕССУАРЫ* 👕\n\n"
        total_value = 0
        
        for acc in accessories:
            text += f"• {acc['accessory_name']}\n"
            text += f"  💰 Цена: {acc['price']:,}{CURR}\n"
            text += f"  ✨ Стиль: {acc['style']}%\n\n"
            total_value += acc['price']
        
        text += f"💰 Общая стоимость: *{total_value:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="accessories_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    def add_custom_accessory(self, accessory: dict):
        """Добавить кастомный аксессуар от админа"""
        accessory['id'] = len(self.default_accessories) + len(self.custom_accessories) + 1
        self.custom_accessories.append(accessory)
