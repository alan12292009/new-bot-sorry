from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *
import random

class HouseStates(StatesGroup):
    waiting_for_house_confirm = State()

class HouseShop:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations
        
        # КАТЕГОРИИ ДОМОВ (от дешевых до дорогих)
        self.houses = [
            # Эконом (1-5)
            {
                'id': 1,
                'name': '🏚️ Хижина в лесу',
                'description': 'Маленькая хижина для настоящего отшельника',
                'price': 50000,
                'rooms': 1,
                'area': 30,
                'comfort': 20,
                'image': '🏚️'
            },
            {
                'id': 2,
                'name': '🏕️ Дачный домик',
                'description': 'Уютный домик за городом, есть печка',
                'price': 150000,
                'rooms': 2,
                'area': 50,
                'comfort': 35,
                'image': '🏕️'
            },
            {
                'id': 3,
                'name': '🏘️ Квартира-студия',
                'description': 'Современная студия в спальном районе',
                'price': 300000,
                'rooms': 1,
                'area': 40,
                'comfort': 50,
                'image': '🏘️'
            },
            {
                'id': 4,
                'name': '🏢 1-комнатная квартира',
                'description': 'Уютная однушка в центре',
                'price': 500000,
                'rooms': 1,
                'area': 45,
                'comfort': 60,
                'image': '🏢'
            },
            {
                'id': 5,
                'name': '🏬 2-комнатная квартира',
                'description': 'Просторная двушка с ремонтом',
                'price': 800000,
                'rooms': 2,
                'area': 65,
                'comfort': 70,
                'image': '🏬'
            },
            
            # Бизнес-класс (6-10)
            {
                'id': 6,
                'name': '🏤 3-комнатная квартира',
                'description': 'Шикарная трешка в новостройке',
                'price': 1200000,
                'rooms': 3,
                'area': 90,
                'comfort': 80,
                'image': '🏤'
            },
            {
                'id': 7,
                'name': '🏦 Пентхаус',
                'description': 'Квартира на последнем этаже с панорамным видом',
                'price': 2000000,
                'rooms': 4,
                'area': 120,
                'comfort': 90,
                'image': '🏦'
            },
            {
                'id': 8,
                'name': '🏰 Таунхаус',
                'description': 'Двухэтажный дом в коттеджном поселке',
                'price': 3500000,
                'rooms': 4,
                'area': 150,
                'comfort': 85,
                'image': '🏰'
            },
            {
                'id': 9,
                'name': '🏯 Особняк',
                'description': 'Шикарный особняк с садом',
                'price': 5000000,
                'rooms': 6,
                'area': 250,
                'comfort': 95,
                'image': '🏯'
            },
            {
                'id': 10,
                'name': '🏛️ Замок',
                'description': 'Настоящий средневековый замок',
                'price': 10000000,
                'rooms': 15,
                'area': 800,
                'comfort': 100,
                'image': '🏛️'
            },
            
            # Элит-класс (11-15)
            {
                'id': 11,
                'name': '🏝️ Вилла на острове',
                'description': 'Собственный остров с виллой',
                'price': 20000000,
                'rooms': 10,
                'area': 500,
                'comfort': 98,
                'image': '🏝️'
            },
            {
                'id': 12,
                'name': '🏔️ Шале в горах',
                'description': 'Роскошное шале в Альпах',
                'price': 30000000,
                'rooms': 8,
                'area': 400,
                'comfort': 97,
                'image': '🏔️'
            },
            {
                'id': 13,
                'name': '🌆 Пентхаус в Дубае',
                'description': 'Шикарный пентхаус в Бурдж-Халифа',
                'price': 50000000,
                'rooms': 5,
                'area': 300,
                'comfort': 99,
                'image': '🌆'
            },
            {
                'id': 14,
                'name': '🏯 Японский храм',
                'description': 'Отреставрированный древний храм в Киото',
                'price': 75000000,
                'rooms': 12,
                'area': 600,
                'comfort': 96,
                'image': '🏯'
            },
            {
                'id': 15,
                'name': '🚀 Космическая станция',
                'description': 'Собственная орбитальная станция',
                'price': 100000000,
                'rooms': 20,
                'area': 1000,
                'comfort': 100,
                'image': '🚀'
            }
        ]

    async def show_houses_menu(self, message: types.Message):
        """Главное меню домов"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🏠 Все дома", callback_data="houses_all"),
            InlineKeyboardButton("💰 Эконом (до 1 млн)", callback_data="houses_econom"),
            InlineKeyboardButton("💼 Бизнес (1-5 млн)", callback_data="houses_business"),
            InlineKeyboardButton("👑 Элит (от 5 млн)", callback_data="houses_elite"),
            InlineKeyboardButton("📋 Мои дома", callback_data="my_houses"),
            InlineKeyboardButton("🏛️ Продать дом", callback_data="sell_house"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🏠 *НЕДВИЖИМОСТЬ* 🏠\n\n"
            "Выберите категорию домов:\n\n"
            "💰 *Эконом* - до 1 млн\n"
            "💼 *Бизнес* - 1-5 млн\n"
            "👑 *Элит* - от 5 млн",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def show_houses_by_category(self, callback_query: types.CallbackQuery, category: str):
        """Показать дома по категории"""
        if category == 'econom':
            houses = [h for h in self.houses if h['price'] <= 1000000]
            title = "💰 *ЭКОНОМ КЛАСС* (до 1 млн)"
        elif category == 'business':
            houses = [h for h in self.houses if 1000000 < h['price'] <= 5000000]
            title = "💼 *БИЗНЕС КЛАСС* (1-5 млн)"
        elif category == 'elite':
            houses = [h for h in self.houses if h['price'] > 5000000]
            title = "👑 *ЭЛИТ КЛАСС* (от 5 млн)"
        else:
            houses = self.houses
            title = "🏠 *ВСЕ ДОМА*"
        
        if not houses:
            await callback_query.answer("В этой категории пока нет домов!", show_alert=True)
            return
        
        text = f"{title}\n\n"
        
        for house in houses:
            text += f"{house['image']} *{house['name']}*\n"
            text += f"   💰 {house['price']:,}{CURR}\n"
            text += f"   🚪 {house['rooms']} комн | 📏 {house['area']}м² | ✨ {house['comfort']}%\n\n"
        
        # Создаем кнопки для каждого дома
        keyboard = InlineKeyboardMarkup(row_width=1)
        for house in houses:
            keyboard.add(InlineKeyboardButton(
                f"{house['image']} {house['name']} - {house['price']:,}{CURR}",
                callback_data=f"house_view_{house['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="houses_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def view_house(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Просмотр конкретного дома"""
        house_id = int(callback_query.data.replace('house_view_', ''))
        house = next((h for h in self.houses if h['id'] == house_id), None)
        
        if not house:
            await callback_query.answer("❌ Дом не найден!", show_alert=True)
            return
        
        user = await self.db.get_user(callback_query.from_user.id)
        
        text = f"{house['image']} *{house['name']}*\n\n"
        text += f"📝 *Описание:* {house['description']}\n\n"
        text += f"💰 *Цена:* {house['price']:,}{CURR}\n"
        text += f"🚪 *Комнат:* {house['rooms']}\n"
        text += f"📏 *Площадь:* {house['area']} м²\n"
        text += f"✨ *Комфорт:* {house['comfort']}%\n\n"
        text += f"💳 *Ваш баланс:* {user['balance']:,}{CURR}\n"
        
        can_afford = user['balance'] >= house['price']
        status = "✅ *Доступно для покупки*" if can_afford else "❌ *Недостаточно средств*"
        text += status
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        if can_afford:
            keyboard.add(InlineKeyboardButton("✅ Купить", callback_data=f"house_buy_{house['id']}"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="houses_all"))
        
        await state.update_data(house=house)
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def confirm_buy_house(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждение покупки дома"""
        house_id = int(callback_query.data.replace('house_buy_', ''))
        house = next((h for h in self.houses if h['id'] == house_id), None)
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'buy_house',
            {
                'text': f"Покупка дома:\n\n"
                        f"{house['image']} *{house['name']}*\n"
                        f"💰 Цена: {house['price']:,}{CURR}\n\n"
                        f"Подтверждаете покупку?",
                'user_id': callback_query.from_user.id,
                'house': house
            },
            'BUY_HOUSE_CONFIRM',
            'CANCEL'
        )

    async def execute_buy_house(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение покупки дома"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        house = confirmed['house']
        
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # Проверяем баланс
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', confirmed['user_id'])
                if user['balance'] < house['price']:
                    await callback_query.message.edit_text("❌ Недостаточно средств!")
                    await state.finish()
                    return
                
                # Списываем деньги
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', 
                                  house['price'], confirmed['user_id'])
                
                # Добавляем дом в инвентарь
                await conn.execute('''
                    INSERT INTO houses (user_id, house_id, house_name, price, rooms, area, comfort)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', confirmed['user_id'], house['id'], house['name'], house['price'], 
                    house['rooms'], house['area'], house['comfort'])
        
        await callback_query.message.edit_text(
            f"✅ *Поздравляем с покупкой\\!*\n\n"
            f"Вы стали владельцем {house['image']} *{house['name']}*\n"
            f"💰 Потрачено: {house['price']:,}{CURR}",
            parse_mode="MarkdownV2"
        )
        await state.finish()

    async def show_my_houses(self, callback_query: types.CallbackQuery):
        """Показать мои дома"""
        user_id = callback_query.from_user.id
        
        async with self.db.pool.acquire() as conn:
            houses = await conn.fetch('SELECT * FROM houses WHERE user_id = $1 ORDER BY price DESC', user_id)
        
        if not houses:
            await callback_query.answer("❌ У вас нет домов!", show_alert=True)
            return
        
        text = "🏠 *МОИ ДОМА* 🏠\n\n"
        total_value = 0
        
        for i, house in enumerate(houses, 1):
            text += f"{i}. {house['house_name']}\n"
            text += f"   💰 Стоимость: {house['price']:,}{CURR}\n"
            text += f"   🚪 {house['rooms']} комн | 📏 {house['area']}м² | ✨ {house['comfort']}%\n\n"
            total_value += house['price']
        
        text += f"💰 Общая стоимость недвижимости: *{total_value:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🏛️ Продать дом", callback_data="sell_house_menu"),
            InlineKeyboardButton("◀️ Назад", callback_data="houses_menu")
        )
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def sell_house_menu(self, callback_query: types.CallbackQuery):
        """Меню продажи дома"""
        user_id = callback_query.from_user.id
        
        async with self.db.pool.acquire() as conn:
            houses = await conn.fetch('SELECT * FROM houses WHERE user_id = $1 ORDER BY price DESC', user_id)
        
        if not houses:
            await callback_query.answer("❌ У вас нет домов для продажи!", show_alert=True)
            return
        
        text = "🏛️ *ПРОДАЖА ДОМА ГОСУДАРСТВУ* 🏛️\n\n"
        text += f"Государство выкупает дома за *{GOVERNMENT_BUY_PERCENT}%* от цены\n"
        text += f"Комиссия: {GOVERNMENT_FEE_PERCENT}% (идет @{MAIN_ADMIN_USERNAME})\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for house in houses:
            buy_price = int(house['price'] * GOVERNMENT_BUY_PERCENT / 100)
            keyboard.add(InlineKeyboardButton(
                f"{house['house_name']} - {buy_price:,}{CURR}",
                callback_data=f"sell_house_{house['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="my_houses"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def confirm_sell_house(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждение продажи дома"""
        house_id = int(callback_query.data.replace('sell_house_', ''))
        
        async with self.db.pool.acquire() as conn:
            house = await conn.fetchrow('SELECT * FROM houses WHERE id = $1', house_id)
        
        buy_price = int(house['price'] * GOVERNMENT_BUY_PERCENT / 100)
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'sell_house',
            {
                'text': f"Продажа дома:\n\n"
                        f"{house['house_name']}\n"
                        f"💰 Цена покупки: {house['price']:,}{CURR}\n"
                        f"🏛️ Государство даст: {buy_price:,}{CURR}\n"
                        f"📊 Комиссия: {house['price'] - buy_price:,}{CURR}\n\n"
                        f"Подтверждаете продажу?",
                'user_id': callback_query.from_user.id,
                'house_id': house_id,
                'house_name': house['house_name'],
                'house_price': house['price'],
                'buy_price': buy_price
            },
            'SELL_HOUSE_CONFIRM',
            'CANCEL'
        )

    async def execute_sell_house(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение продажи дома"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # Удаляем дом
                await conn.execute('DELETE FROM houses WHERE id = $1', confirmed['house_id'])
                
                # Начисляем деньги пользователю
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2',
                                  confirmed['buy_price'], confirmed['user_id'])
                
                # Комиссия админу
                commission = confirmed['house_price'] - confirmed['buy_price']
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2',
                                  commission, MAIN_ADMIN_ID)
        
        await callback_query.message.edit_text(
            f"✅ Вы продали {confirmed['house_name']} государству за {confirmed['buy_price']:,}{CURR}\n"
            f"Комиссия: {commission:,}{CURR} (идет @{MAIN_ADMIN_USERNAME})"
        )
        await state.finish()
