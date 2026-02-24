from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *

class TradingStates(StatesGroup):
    waiting_for_trade_type = State()
    waiting_for_username = State()
    waiting_for_amount = State()
    waiting_for_item_selection = State()
    waiting_for_item_quantity = State()
    waiting_for_trade_offer = State()

class Trading:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations

    async def show_trading_menu(self, message: types.Message):
        """Главное меню торговли"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💸 Перевести деньги", callback_data="transfer_money"),
            InlineKeyboardButton("🤝 Обмен предметами", callback_data="trade_items"),
            InlineKeyboardButton("💰 Продать государству", callback_data="gov_menu"),
            InlineKeyboardButton("📦 Мой инвентарь", callback_data="inventory"),
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(
            "🤝 *ТОРГОВАЯ ПЛОЩАДКА* 🤝\n\n"
            f"Комиссия за перевод: {TRANSFER_FEE*100}%\n"
            f"Комиссия за продажу государству: {GOVERNMENT_FEE_PERCENT}%\n\n"
            f"Что можно передавать:\n"
            f"✅ Деньги\n"
            f"✅ Криптовалюту\n"
            f"✅ Машины\n"
            f"✅ Телефоны\n"
            f"✅ Дома\n"
            f"✅ Аксессуары\n\n"
            f"Выберите действие:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # ========== ПЕРЕВОД ДЕНЕГ ==========
    
    async def transfer_money_start(self, callback_query: types.CallbackQuery, state: FSMContext, user_settings=None):
        """Начало перевода денег"""
        from settings import UserSettings
        if user_settings is None:
            user_settings = UserSettings(self.bot, self.db)
        
        # Проверяем настройки отправителя
        sender_check = await user_settings.check_permission(
            callback_query.from_user.id, 
            'transfer'
        )
        
        if not sender_check:
            await callback_query.answer(
                "❌ Вы запретили переводы в настройках!", 
                show_alert=True
            )
            return
        
        await callback_query.message.edit_text(
            "💸 *ПЕРЕВОД ДЕНЕГ*\n\n"
            f"Комиссия: {TRANSFER_FEE*100}% (идет @{MAIN_ADMIN_USERNAME})\n\n"
            "Введите @username получателя:",
            parse_mode="Markdown"
        )
        await TradingStates.waiting_for_username.set()
        await state.update_data(trade_type='money')

    async def process_username(self, message: types.Message, state: FSMContext):
        """Обработка имени получателя"""
        username = message.text.replace('@', '')
        
        # Проверяем настройки получателя
        from settings import UserSettings
        user_settings = UserSettings(self.bot, self.db)
        
        async with self.db.pool.acquire() as conn:
            receiver = await conn.fetchrow('SELECT * FROM users WHERE username ILIKE $1', username)
            
            if receiver:
                receiver_check = await user_settings.check_permission(receiver['user_id'], 'transfer')
                if not receiver_check:
                    await message.reply(f"❌ @{username} запретил получать переводы в настройках!")
                    await state.finish()
                    return
        
        await state.update_data(to_username=username)
        
        data = await state.get_data()
        
        if data['trade_type'] == 'money':
            await message.reply("Введите сумму перевода:")
            await TradingStates.waiting_for_amount.set()
        else:
            await self.show_user_items_for_trade(message, state)

    async def process_amount(self, message: types.Message, state: FSMContext):
        """Обработка суммы перевода"""
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
            'transfer_money',
            {
                'text': f"💸 *Подтверждение перевода*\n\n"
                        f"Кому: @{data['to_username']}\n"
                        f"Сумма: {amount}{CURR}\n"
                        f"Получит: {amount - fee}{CURR}\n"
                        f"Комиссия: {fee}{CURR}\n\n"
                        f"Подтверждаете?",
                'from_id': message.from_user.id,
                'to_username': data['to_username'],
                'amount': amount,
                'fee': fee
            },
            'TRANSFER_CONFIRM',
            'CANCEL'
        )

    async def execute_transfer(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение перевода"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.payments.process_transfer(
            confirmed['from_id'],
            confirmed['to_username'],
            confirmed['amount']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    # ========== ОБМЕН ПРЕДМЕТАМИ ==========
    
    async def trade_items_start(self, callback_query: types.CallbackQuery, state: FSMContext, user_settings=None):
        """Начало обмена предметами"""
        from settings import UserSettings
        if user_settings is None:
            user_settings = UserSettings(self.bot, self.db)
        
        # Проверяем настройки
        sender_check = await user_settings.check_permission(
            callback_query.from_user.id, 
            'trade'
        )
        
        if not sender_check:
            await callback_query.answer(
                "❌ Вы запретили трейды в настройках!", 
                show_alert=True
            )
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💰 Криптовалюта", callback_data="trade_crypto"),
            InlineKeyboardButton("🚗 Машины", callback_data="trade_cars"),
            InlineKeyboardButton("📱 Телефоны", callback_data="trade_phones"),
            InlineKeyboardButton("🏠 Дома", callback_data="trade_houses"),
            InlineKeyboardButton("👕 Аксессуары", callback_data="trade_accessories"),
            InlineKeyboardButton("◀️ Назад", callback_data="trading_menu")
        )
        
        await callback_query.message.edit_text(
            "🤝 *ОБМЕН ПРЕДМЕТАМИ*\n\n"
            "Что хотите передать?",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await state.update_data(trade_type='item')
        await TradingStates.waiting_for_trade_type.set()

    async def show_user_items_for_trade(self, message: types.Message, state: FSMContext):
        """Показать предметы пользователя для обмена"""
        data = await state.get_data()
        trade_type = data.get('trade_subtype', data.get('trade_type'))
        user_id = message.from_user.id
        
        items = []
        if trade_type == 'crypto':
            items = await self.db.get_user_crypto_wallet(user_id)
        elif trade_type == 'cars':
            items = await self.db.get_user_cars(user_id)
        elif trade_type == 'phones':
            items = await self.db.get_user_phones(user_id)
        elif trade_type == 'houses':
            async with self.db.pool.acquire() as conn:
                items = await conn.fetch('SELECT * FROM houses WHERE user_id = $1', user_id)
        elif trade_type == 'accessories':
            items = await self.db.get_user_accessories(user_id)
        
        if not items:
            await message.reply(f"❌ У вас нет {trade_type} для передачи!")
            await state.finish()
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for item in items:
            if trade_type == 'crypto':
                value = float(item['amount']) * float(item['price'])
                btn_text = f"{item['symbol']}: {float(item['amount']):.8f} ({value:.2f}{CURR})"
                callback_data = f"trade_item_crypto_{item['crypto_id']}_{item['amount']}"
            elif trade_type == 'cars':
                btn_text = f"{item['model']} - {item['price']:,}{CURR}"
                callback_data = f"trade_item_car_{item['id']}"
            elif trade_type == 'phones':
                btn_text = f"{item['model']} - {item['price']:,}{CURR}"
                callback_data = f"trade_item_phone_{item['id']}"
            elif trade_type == 'houses':
                btn_text = f"{item['house_name']} - {item['price']:,}{CURR}"
                callback_data = f"trade_item_house_{item['id']}"
            elif trade_type == 'accessories':
                btn_text = f"{item['accessory_name']} - {item['price']:,}{CURR}"
                callback_data = f"trade_item_accessory_{item['id']}"
            
            keyboard.add(InlineKeyboardButton(btn_text, callback_data=callback_data))
        
        keyboard.add(InlineKeyboardButton("◀️ Отмена", callback_data="trading_menu"))
        
        await message.reply("Выберите предмет для передачи:", reply_markup=keyboard)

    async def process_trade_item(self, callback_query: types.CallbackQuery, state: FSMContext, user_settings=None):
        """Обработка выбранного предмета"""
        from settings import UserSettings
        if user_settings is None:
            user_settings = UserSettings(self.bot, self.db)
        
        data = callback_query.data.split('_')
        item_type = data[2]
        
        if item_type == 'crypto':
            crypto_id = int(data[3])
            amount = float(data[4])
            await state.update_data(trade_item_type='crypto', trade_item_id=crypto_id, trade_amount=amount)
        elif item_type == 'car':
            car_id = int(data[3])
            await state.update_data(trade_item_type='car', trade_item_id=car_id)
        elif item_type == 'phone':
            phone_id = int(data[3])
            await state.update_data(trade_item_type='phone', trade_item_id=phone_id)
        elif item_type == 'house':
            house_id = int(data[3])
            await state.update_data(trade_item_type='house', trade_item_id=house_id)
        elif item_type == 'accessory':
            accessory_id = int(data[3])
            await state.update_data(trade_item_type='accessory', trade_item_id=accessory_id)
        
        await callback_query.message.edit_text("Введите @username получателя:")
        await TradingStates.waiting_for_username.set()

    async def confirm_trade(self, message: types.Message, state: FSMContext):
        """Подтверждение передачи предмета"""
        username = message.text.replace('@', '')
        data = await state.get_data()
        
        # Проверяем настройки получателя
        from settings import UserSettings
        user_settings = UserSettings(self.bot, self.db)
        
        async with self.db.pool.acquire() as conn:
            receiver = await conn.fetchrow('SELECT * FROM users WHERE username ILIKE $1', username)
            
            if receiver:
                receiver_check = await user_settings.check_permission(receiver['user_id'], 'trade')
                if not receiver_check:
                    await message.reply(f"❌ @{username} запретил получать предметы в настройках!")
                    await state.finish()
                    return
        
        # Получаем информацию о предмете
        item_info = ""
        if data['trade_item_type'] == 'crypto':
            crypto = await self.db.get_crypto_by_id(data['trade_item_id'])
            item_info = f"{data['trade_amount']:.8f} {crypto['symbol']}"
        elif data['trade_item_type'] == 'car':
            async with self.db.pool.acquire() as conn:
                car = await conn.fetchrow('SELECT * FROM cars WHERE id = $1', data['trade_item_id'])
                item_info = f"🚗 {car['model']}"
        elif data['trade_item_type'] == 'phone':
            async with self.db.pool.acquire() as conn:
                phone = await conn.fetchrow('SELECT * FROM phones WHERE id = $1', data['trade_item_id'])
                item_info = f"📱 {phone['model']}"
        elif data['trade_item_type'] == 'house':
            async with self.db.pool.acquire() as conn:
                house = await conn.fetchrow('SELECT * FROM houses WHERE id = $1', data['trade_item_id'])
                item_info = f"🏠 {house['house_name']}"
        elif data['trade_item_type'] == 'accessory':
            async with self.db.pool.acquire() as conn:
                acc = await conn.fetchrow('SELECT * FROM accessories WHERE id = $1', data['trade_item_id'])
                item_info = f"👕 {acc['accessory_name']}"
        
        await self.confirmations.ask_confirmation(
            message,
            'trade_item',
            {
                'text': f"🤝 *Подтверждение передачи*\n\n"
                        f"Кому: @{username}\n"
                        f"Предмет: {item_info}\n\n"
                        f"Подтверждаете?",
                'from_id': message.from_user.id,
                'to_username': username,
                'item_type': data['trade_item_type'],
                'item_id': data['trade_item_id'],
                'item_amount': data.get('trade_amount')
            },
            'TRADE_ITEM_CONFIRM',
            'CANCEL'
        )

    async def execute_trade(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение передачи предмета"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        # Находим получателя
        async with self.db.pool.acquire() as conn:
            receiver = await conn.fetchrow('SELECT * FROM users WHERE username ILIKE $1', confirmed['to_username'])
            
            if not receiver:
                await callback_query.message.edit_text("❌ Получатель не найден!")
                await state.finish()
                return
            
            async with conn.transaction():
                if confirmed['item_type'] == 'crypto':
                    # Передача крипты
                    await conn.execute('''
                        UPDATE crypto_wallets 
                        SET amount = amount - $1 
                        WHERE user_id = $2 AND crypto_id = $3
                    ''', confirmed['item_amount'], confirmed['from_id'], confirmed['item_id'])
                    
                    receiver_wallet = await conn.fetchrow('''
                        SELECT * FROM crypto_wallets 
                        WHERE user_id = $1 AND crypto_id = $2
                    ''', receiver['user_id'], confirmed['item_id'])
                    
                    if receiver_wallet:
                        await conn.execute('''
                            UPDATE crypto_wallets 
                            SET amount = amount + $1 
                            WHERE user_id = $2 AND crypto_id = $3
                        ''', confirmed['item_amount'], receiver['user_id'], confirmed['item_id'])
                    else:
                        await conn.execute('''
                            INSERT INTO crypto_wallets (user_id, crypto_id, amount, average_buy_price)
                            VALUES ($1, $2, $3, $4)
                        ''', receiver['user_id'], confirmed['item_id'], confirmed['item_amount'], 0)
                
                elif confirmed['item_type'] == 'car':
                    await conn.execute('''
                        UPDATE cars SET user_id = $1 WHERE id = $2
                    ''', receiver['user_id'], confirmed['item_id'])
                
                elif confirmed['item_type'] == 'phone':
                    await conn.execute('''
                        UPDATE phones SET user_id = $1 WHERE id = $2
                    ''', receiver['user_id'], confirmed['item_id'])
                
                elif confirmed['item_type'] == 'house':
                    await conn.execute('''
                        UPDATE houses SET user_id = $1 WHERE id = $2
                    ''', receiver['user_id'], confirmed['item_id'])
                
                elif confirmed['item_type'] == 'accessory':
                    await conn.execute('''
                        UPDATE accessories SET user_id = $1 WHERE id = $2
                    ''', receiver['user_id'], confirmed['item_id'])
        
        await callback_query.message.edit_text(
            f"✅ Предмет успешно передан пользователю @{confirmed['to_username']}!"
        )
        await state.finish()
