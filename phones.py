from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from confirmations import ConfirmationSystem
from config import *
import random

class PhoneStates(StatesGroup):
    waiting_for_phone_brand = State()
    waiting_for_phone_confirm = State()

class PhoneShop:
    def __init__(self, bot, db: Database, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.confirmations = confirmations
        
        self.phone_brands = {
            'Xiaomi': {'min_price': 15000, 'max_price': 50000, 'camera': 48},
            'Samsung': {'min_price': 20000, 'max_price': 100000, 'camera': 108},
            'Apple iPhone': {'min_price': 50000, 'max_price': 150000, 'camera': 48},
            'Google Pixel': {'min_price': 40000, 'max_price': 90000, 'camera': 50},
            'OnePlus': {'min_price': 35000, 'max_price': 80000, 'camera': 50},
            'Sony': {'min_price': 45000, 'max_price': 120000, 'camera': 52}
        }

    async def show_phone_shop(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for brand in list(self.phone_brands.keys())[:8]:
            price_range = self.phone_brands[brand]
            btn_text = f"{brand} ({price_range['min_price']//1000}к - {price_range['max_price']//1000}к)"
            keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"phone_buy_{brand}"))
        
        keyboard.add(
            InlineKeyboardButton("📋 Мои телефоны", callback_data="my_phones"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "📱 *МАГАЗИН ТЕЛЕФОНОВ* 📱\n\n"
            "Выберите марку телефона:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def select_phone_brand(self, callback_query: types.CallbackQuery, state: FSMContext):
        brand = callback_query.data.replace('phone_buy_', '')
        price_range = self.phone_brands[brand]
        
        price = random.randint(price_range['min_price'], price_range['max_price'])
        
        await state.update_data(phone_brand=brand, phone_price=price, phone_camera=price_range['camera'])
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'buy_phone',
            {
                'text': f"Покупка: *{brand}*\n"
                        f"💰 Цена: {price}{CURR}\n"
                        f"📷 Камера: {price_range['camera']} МП\n\n"
                        f"Подтверждаете покупку?",
                'phone_brand': brand,
                'phone_price': price,
                'phone_camera': price_range['camera']
            },
            'BUY_PHONE_CONFIRM',
            'CANCEL'
        )

    async def execute_buy_phone(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.db.buy_phone(
            callback_query.from_user.id,
            confirmed['phone_brand'],
            confirmed['phone_price']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_my_phones(self, callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id
        phones = await self.db.get_user_phones(user_id)
        
        if not phones:
            await callback_query.answer("❌ У вас нет телефонов!", show_alert=True)
            return
        
        text = "📱 *МОИ ТЕЛЕФОНЫ* 📱\n\n"
        total_value = 0
        
        for phone in phones:
            text += f"• *{phone['model']}*\n"
            text += f"  💰 Цена: {phone['price']:,}{CURR}\n"
            text += f"  📷 Камера: {phone['camera']} МП\n\n"
            total_value += phone['price']
        
        text += f"💰 Общая стоимость: *{total_value:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
