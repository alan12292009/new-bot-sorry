from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from confirmations import ConfirmationSystem
from config import *
import random

class CarStates(StatesGroup):
    waiting_for_car_brand = State()
    waiting_for_car_confirm = State()

class CarShop:
    def __init__(self, bot, db: Database, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.confirmations = confirmations
        
        self.car_brands = {
            'Lada': {'min_price': 100000, 'max_price': 500000, 'speed': 150},
            'Kia': {'min_price': 500000, 'max_price': 1500000, 'speed': 200},
            'Hyundai': {'min_price': 600000, 'max_price': 2000000, 'speed': 220},
            'Toyota': {'min_price': 1000000, 'max_price': 3000000, 'speed': 250},
            'BMW': {'min_price': 3500000, 'max_price': 9000000, 'speed': 330},
            'Mercedes': {'min_price': 4000000, 'max_price': 10000000, 'speed': 340},
            'Ferrari': {'min_price': 10000000, 'max_price': 30000000, 'speed': 370}
        }

    async def show_car_shop(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for brand in list(self.car_brands.keys())[:8]:
            price_range = self.car_brands[brand]
            btn_text = f"{brand} ({price_range['min_price']//1000}к - {price_range['max_price']//1000}к)"
            keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"car_buy_{brand}"))
        
        keyboard.add(
            InlineKeyboardButton("📋 Мои машины", callback_data="my_cars"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🏎️ *АВТОСАЛОН* 🏎️\n\n"
            "Выберите марку автомобиля:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def select_car_brand(self, callback_query: types.CallbackQuery, state: FSMContext):
        brand = callback_query.data.replace('car_buy_', '')
        price_range = self.car_brands[brand]
        
        price = random.randint(price_range['min_price'], price_range['max_price'])
        
        await state.update_data(car_brand=brand, car_price=price, car_speed=price_range['speed'])
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'buy_car',
            {
                'text': f"Покупка: *{brand}*\n"
                        f"💰 Цена: {price}{CURR}\n"
                        f"⚡ Скорость: {price_range['speed']} км/ч\n\n"
                        f"Подтверждаете покупку?",
                'car_brand': brand,
                'car_price': price,
                'car_speed': price_range['speed']
            },
            'BUY_CAR_CONFIRM',
            'CANCEL'
        )

    async def execute_buy_car(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.db.buy_car(
            callback_query.from_user.id,
            confirmed['car_brand'],
            confirmed['car_price']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_my_cars(self, callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id
        cars = await self.db.get_user_cars(user_id)
        
        if not cars:
            await callback_query.answer("❌ У вас нет машин!", show_alert=True)
            return
        
        text = "🏎️ *МОИ МАШИНЫ* 🏎️\n\n"
        total_value = 0
        
        for car in cars:
            text += f"• *{car['model']}*\n"
            text += f"  💰 Цена: {car['price']:,}{CURR}\n"
            text += f"  ⚡ Скорость: {car['speed']} км/ч\n\n"
            total_value += car['price']
        
        text += f"💰 Общая стоимость: *{total_value:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
