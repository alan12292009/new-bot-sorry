from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *

class CryptoStates(StatesGroup):
    waiting_for_crypto_select = State()
    waiting_for_buy_amount = State()
    waiting_for_sell_amount = State()

class CryptoMarket:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations

    async def show_crypto_market(self, message: types.Message):
        cryptos = await self.db.get_crypto_list()
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for crypto in cryptos[:6]:
            btn_text = f"{crypto['symbol']} - {float(crypto['price']):.2f}{CURR}"
            keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"crypto_select_{crypto['id']}"))
        
        keyboard.add(
            InlineKeyboardButton("📊 Мой портфель", callback_data="crypto_wallet"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "💎 *КРИПТО-БИРЖА* 💎\n\n"
            "Выберите криптовалюту для торговли:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def select_crypto(self, callback_query: types.CallbackQuery, state: FSMContext):
        crypto_id = int(callback_query.data.replace('crypto_select_', ''))
        crypto = await self.db.get_crypto_by_id(crypto_id)
        
        await state.update_data(crypto_id=crypto_id, crypto_symbol=crypto['symbol'], crypto_price=float(crypto['price']))
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💰 Купить", callback_data="crypto_buy"),
            InlineKeyboardButton("💸 Продать", callback_data="crypto_sell"),
            InlineKeyboardButton("◀️ Назад", callback_data="crypto_menu")
        )
        
        await callback_query.message.edit_text(
            f"💎 *{crypto['name']} ({crypto['symbol']})*\n\n"
            f"💰 Текущая цена: *{float(crypto['price']):.2f}{CURR}*\n\n"
            f"Выберите действие:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def buy_crypto_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.message.edit_text("Введите сумму в USD для покупки:")
        await CryptoStates.waiting_for_buy_amount.set()

    async def process_buy_amount(self, message: types.Message, state: FSMContext):
        try:
            amount = float(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную сумму!")
            return
        
        data = await state.get_data()
        user = await self.db.get_user(message.from_user.id)
        
        if user['balance'] < amount:
            await message.reply(f"❌ Недостаточно средств! Баланс: {user['balance']}{CURR}")
            await state.finish()
            return
        
        await self.confirmations.ask_confirmation(
            message,
            'buy_crypto',
            {
                'text': f"Покупка: {data['crypto_symbol']}\n"
                        f"Сумма: {amount}{CURR}\n"
                        f"Цена: {data['crypto_price']:.2f}{CURR}\n"
                        f"Комиссия: {amount * CRYPTO_FEE:.2f}{CURR}\n\n"
                        f"Подтверждаете покупку?",
                'user_id': message.from_user.id,
                'crypto_id': data['crypto_id'],
                'amount_usd': amount,
                'crypto_symbol': data['crypto_symbol'],
                'crypto_price': data['crypto_price']
            },
            'BUY_CRYPTO_CONFIRM',
            'CANCEL'
        )

    async def execute_buy_crypto(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.payments.process_crypto_buy(
            confirmed['user_id'],
            confirmed['crypto_id'],
            confirmed['amount_usd'],
            confirmed['crypto_symbol'],
            confirmed['crypto_price']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def sell_crypto_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        
        wallets = await self.db.get_user_crypto_wallet(callback_query.from_user.id)
        user_crypto = None
        
        for w in wallets:
            if w['crypto_id'] == data['crypto_id']:
                user_crypto = w
                break
        
        if not user_crypto or float(user_crypto['amount']) <= 0:
            await callback_query.answer(f"❌ У вас нет {data['crypto_symbol']}!", show_alert=True)
            return
        
        await state.update_data(crypto_amount=float(user_crypto['amount']), avg_price=float(user_crypto['average_buy_price']))
        
        await callback_query.message.edit_text(
            f"Введите количество {data['crypto_symbol']} для продажи:\n"
            f"Доступно: {float(user_crypto['amount']):.8f}"
        )
        await CryptoStates.waiting_for_sell_amount.set()

    async def process_sell_amount(self, message: types.Message, state: FSMContext):
        try:
            amount = float(message.text)
        except ValueError:
            await message.reply("❌ Введите корректное количество!")
            return
        
        data = await state.get_data()
        
        if amount > data['crypto_amount']:
            await message.reply(f"❌ У вас только {data['crypto_amount']:.8f} {data['crypto_symbol']}!")
            return
        
        await self.confirmations.ask_confirmation(
            message,
            'sell_crypto',
            {
                'text': f"Продажа: {data['crypto_symbol']}\n"
                        f"Количество: {amount:.8f}\n"
                        f"Цена: {data['crypto_price']:.2f}{CURR}\n"
                        f"Сумма: {amount * data['crypto_price']:.2f}{CURR}\n"
                        f"Комиссия: {amount * data['crypto_price'] * CRYPTO_FEE:.2f}{CURR}\n\n"
                        f"Подтверждаете продажу?",
                'user_id': message.from_user.id,
                'crypto_id': data['crypto_id'],
                'crypto_amount': amount,
                'crypto_symbol': data['crypto_symbol'],
                'crypto_price': data['crypto_price'],
                'avg_price': data['avg_price']
            },
            'SELL_CRYPTO_CONFIRM',
            'CANCEL'
        )

    async def execute_sell_crypto(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.payments.process_crypto_sell(
            confirmed['user_id'],
            confirmed['crypto_id'],
            confirmed['crypto_amount'],
            confirmed['crypto_symbol'],
            confirmed['crypto_price'],
            confirmed['avg_price']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_wallet(self, callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id
        wallets = await self.db.get_user_crypto_wallet(user_id)
        
        if not wallets:
            await callback_query.answer("❌ У вас нет криптовалюты!", show_alert=True)
            return
        
        text = "📊 *КРИПТО-ПОРТФЕЛЬ* 📊\n\n"
        total_value = 0
        
        for w in wallets:
            value = float(w['amount']) * float(w['price'])
            profit = (float(w['price']) - float(w['average_buy_price'])) * float(w['amount'])
            profit_emoji = "🟢" if profit >= 0 else "🔴"
            
            text += f"*{w['symbol']}*\n"
            text += f"   Количество: {float(w['amount']):.8f}\n"
            text += f"   Цена: {float(w['price']):.2f}{CURR}\n"
            text += f"   Стоимость: {value:.2f}{CURR}\n"
            text += f"   {profit_emoji} P/L: {profit:+.2f}{CURR}\n\n"
            total_value += value
        
        text += f"💰 Общая стоимость: *{total_value:.2f}{CURR}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
