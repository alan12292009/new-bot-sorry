from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *

class TradingStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_amount = State()

class Trading:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations

    async def show_transfer_menu(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💸 Перевести деньги", callback_data="transfer_start"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "💱 *ПЕРЕВОДЫ* 💱\n\n"
            f"Комиссия: {TRANSFER_FEE*100}% (идет @{MAIN_ADMIN_USERNAME})\n\n"
            f"Выберите действие:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def transfer_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.message.edit_text("Введите @username получателя:")
        await TradingStates.waiting_for_username.set()

    async def process_username(self, message: types.Message, state: FSMContext):
        username = message.text.replace('@', '')
        await state.update_data(to_username=username)
        await message.reply("Введите сумму перевода:")
        await TradingStates.waiting_for_amount.set()

    async def process_amount(self, message: types.Message, state: FSMContext):
        try:
            amount = int(message.text)
        except ValueError:
            await message.reply("❌ Введите корректную сумму!")
            return
        
        data = await state.get_data()
        user = await self.db.get_user(message.from_user.id)
        
        if user['balance'] < amount:
            await message.reply(f"❌ Недостаточно средств! Баланс: {user['balance']}{CURR}")
            await state.finish()
            return
        
        fee = int(amount * TRANSFER_FEE)
        
        await self.confirmations.ask_confirmation(
            message,
            'transfer',
            {
                'text': f"Перевод: @{data['to_username']}\n"
                        f"Сумма: {amount}{CURR}\n"
                        f"Получит: {amount - fee}{CURR}\n"
                        f"Комиссия: {fee}{CURR}\n\n"
                        f"Подтверждаете перевод?",
                'from_id': message.from_user.id,
                'to_username': data['to_username'],
                'amount': amount,
                'fee': fee
            },
            'TRANSFER_CONFIRM',
            'CANCEL'
        )

    async def execute_transfer(self, callback_query: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.payments.process_transfer(
            confirmed['from_id'],
            confirmed['to_username'],
            confirmed['amount']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def show_trading_menu(self, message: types.Message):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🤝 Предложить обмен", callback_data="trade_start"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🤝 *ТОРГОВЛЯ* 🤝\n\n"
            "Раздел в разработке. Скоро здесь можно будет обмениваться предметами!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def trade_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        await callback_query.answer("Торговля пока в разработке!", show_alert=True)
