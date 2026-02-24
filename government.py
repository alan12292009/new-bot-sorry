from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *

class Government:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations

    async def show_government_menu(self, message: types.Message):
        """Показать меню государства"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🚗 Продать машину", callback_data="gov_sell_car"),
            InlineKeyboardButton("📱 Продать телефон", callback_data="gov_sell_phone"),
            InlineKeyboardButton("📊 Информация", callback_data="gov_info"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🏛️ *ГОСУДАРСТВЕННАЯ КОМИССИЯ* 🏛️\n\n"
            f"Государство выкупает ваши предметы!\n"
            f"💰 Цена выкупа: *{GOVERNMENT_BUY_PERCENT}%* от рыночной стоимости\n"
            f"📊 Комиссия: *{GOVERNMENT_FEE_PERCENT}%* (идет @{MAIN_ADMIN_USERNAME})\n\n"
            f"Выберите категорию:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def show_sell_cars(self, callback_query: types.CallbackQuery):
        """Показать машины для продажи"""
        user_id = callback_query.from_user.id
        cars = await self.db.get_user_cars(user_id)
        
        if not cars:
            await callback_query.answer("❌ У вас нет машин!", show_alert=True)
            return
        
        text = "🚗 *ПРОДАЖА МАШИН ГОСУДАРСТВУ* 🚗\n\n"
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for car in cars:
            buy_price = int(car['price'] * GOVERNMENT_BUY_PERCENT / 100)
            text += f"• *{car['model']}*\n  💰 Куплена за: {car['price']}{CURR}\n  🏛️ Выкупим за: {buy_price}{CURR}\n\n"
            keyboard.add(InlineKeyboardButton(
                f"📌 {car['model'][:20]} - {buy_price}{CURR}",
                callback_data=f"gov_sell_car_{car['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="gov_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def confirm_sell_car(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждение продажи машины"""
        car_id = int(callback_query.data.replace('gov_sell_car_', ''))
        
        async with self.db.pool.acquire() as conn:
            car = await conn.fetchrow('SELECT * FROM cars WHERE id = $1', car_id)
            
            if not car:
                await callback_query.answer("❌ Машина не найдена!", show_alert=True)
                return
            
            buy_price = int(car['price'] * GOVERNMENT_BUY_PERCENT / 100)
            
            await self.confirmations.ask_confirmation(
                callback_query.message,
                'sell_car',
                {
                    'text': f"Продажа: *{car['model']}*\n"
                            f"Цена покупки: {car['price']}{CURR}\n"
                            f"Государство даст: {buy_price}{CURR}\n"
                            f"Комиссия: {car['price'] - buy_price}{CURR}",
                    'car_id': car_id,
                    'car_model': car['model'],
                    'car_price': car['price'],
                    'buy_price': buy_price
                },
                'SELL_CAR_CONFIRM',
                'CANCEL'
            )

    async def execute_sell_car(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение продажи машины"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.db.sell_car_to_government(
            callback_query.from_user.id,
            confirmed['car_id']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_sell_phones(self, callback_query: types.CallbackQuery):
        """Показать телефоны для продажи"""
        user_id = callback_query.from_user.id
        phones = await self.db.get_user_phones(user_id)
        
        if not phones:
            await callback_query.answer("❌ У вас нет телефонов!", show_alert=True)
            return
        
        text = "📱 *ПРОДАЖА ТЕЛЕФОНОВ ГОСУДАРСТВУ* 📱\n\n"
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for phone in phones:
            buy_price = int(phone['price'] * GOVERNMENT_BUY_PERCENT / 100)
            text += f"• *{phone['model']}*\n  💰 Куплен за: {phone['price']}{CURR}\n  🏛️ Выкупим за: {buy_price}{CURR}\n\n"
            keyboard.add(InlineKeyboardButton(
                f"📌 {phone['model'][:20]} - {buy_price}{CURR}",
                callback_data=f"gov_sell_phone_{phone['id']}"
            ))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="gov_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def confirm_sell_phone(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подтверждение продажи телефона"""
        phone_id = int(callback_query.data.replace('gov_sell_phone_', ''))
        
        async with self.db.pool.acquire() as conn:
            phone = await conn.fetchrow('SELECT * FROM phones WHERE id = $1', phone_id)
            
            if not phone:
                await callback_query.answer("❌ Телефон не найден!", show_alert=True)
                return
            
            buy_price = int(phone['price'] * GOVERNMENT_BUY_PERCENT / 100)
            
            await self.confirmations.ask_confirmation(
                callback_query.message,
                'sell_phone',
                {
                    'text': f"Продажа: *{phone['model']}*\n"
                            f"Цена покупки: {phone['price']}{CURR}\n"
                            f"Государство даст: {buy_price}{CURR}\n"
                            f"Комиссия: {phone['price'] - buy_price}{CURR}",
                    'phone_id': phone_id,
                    'phone_model': phone['model'],
                    'phone_price': phone['price'],
                    'buy_price': buy_price
                },
                'SELL_PHONE_CONFIRM',
                'CANCEL'
            )

    async def execute_sell_phone(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение продажи телефона"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.db.sell_phone_to_government(
            callback_query.from_user.id,
            confirmed['phone_id']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_info(self, callback_query: types.CallbackQuery):
        """Показать информацию о государственных услугах"""
        text = "📊 *ИНФОРМАЦИЯ О ГОСУДАРСТВЕ* 📊\n\n"
        text += "🏛️ Государство выполняет следующие функции:\n\n"
        text += f"1. *Выкуп предметов* - {GOVERNMENT_BUY_PERCENT}% от цены\n"
        text += f"2. *Комиссия* - {GOVERNMENT_FEE_PERCENT}% (идет @{MAIN_ADMIN_USERNAME})\n"
        text += f"3. *Поддержка* - @{MAIN_ADMIN_USERNAME}\n\n"
        text += "Все вырученные средства идут на развитие проекта!"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="gov_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)