from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from payments import PaymentSystem
from confirmations import ConfirmationSystem
from config import *
import random
import asyncio

class CasinoStates(StatesGroup):
    waiting_for_dice_bet = State()
    waiting_for_roulette_bet = State()
    waiting_for_roulette_color = State()
    waiting_for_roulette_number = State()
    waiting_for_duel_username = State()
    waiting_for_duel_bet = State()
    waiting_for_duel_accept = State()

class Casino:
    def __init__(self, bot, db: Database, payments: PaymentSystem, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.payments = payments
        self.confirmations = confirmations
        self.active_duels = {}  # Словарь для активных дуэлей
        self.jackpot = 1000000  # Начальный джекпот

    async def show_casino_menu(self, message: types.Message):
        """Главное меню казино"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎲 Играть в кости", callback_data="casino_dice"),
            InlineKeyboardButton("🎰 Рулетка", callback_data="casino_roulette"),
            InlineKeyboardButton("🤼 Сразиться с игроком", callback_data="casino_duel"),
            InlineKeyboardButton("🎯 Джекпот", callback_data="casino_jackpot"),
            InlineKeyboardButton("📊 Моя статистика", callback_data="casino_stats"),
            InlineKeyboardButton("🏆 Топ казино", callback_data="casino_top"),
            InlineKeyboardButton("◀️ В главное меню", callback_data="menu")
        )
        
        await message.reply(
            f"🎰 *КАЗИНО МЕГАРОЛЛ* 🎰\n\n"
            f"💰 Текущий джекпот: *{self.jackpot:,}{CURR}*\n"
            f"🎲 Минимальная ставка: *{MIN_BET}{CURR}*\n"
            f"🎲 Максимальная ставка: *{MAX_BET}{CURR}*\n\n"
            f"🤼 *Сразиться с игроком* - вызови другого игрока на дуэль!\n\n"
            f"Выберите игру:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # ========== ИГРА В КОСТИ ==========
    
    async def play_dice(self, callback_query: types.CallbackQuery):
        """Начало игры в кости"""
        user_id = callback_query.from_user.id
        balance = await self.db.get_balance(user_id)
        
        if balance < MIN_BET:
            await self.bot.answer_callback_query(
                callback_query.id,
                f"❌ Недостаточно средств! Минимум {MIN_BET}{CURR}",
                show_alert=True
            )
            return
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад в казино", callback_data="casino_menu"))
        
        await self.bot.edit_message_text(
            f"🎲 *ИГРА В КОСТИ*\n\n"
            f"💰 Твой баланс: *{balance:,}{CURR}*\n"
            f"💵 Джекпот: *{self.jackpot:,}{CURR}*\n\n"
            f"Введи сумму ставки:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await CasinoStates.waiting_for_dice_bet.set()

    async def process_dice_bet(self, message: types.Message, state: FSMContext):
        """Обработка ставки в кости"""
        try:
            bet = int(message.text)
        except ValueError:
            await message.reply("❌ Введите число!")
            return
        
        user_id = message.from_user.id
        balance = await self.db.get_balance(user_id)
        
        if bet < MIN_BET:
            await message.reply(f"❌ Минимальная ставка {MIN_BET}{CURR}!")
            return
        
        if bet > balance:
            await message.reply(f"❌ У тебя только {balance:,}{CURR}!")
            return
        
        if bet > MAX_BET:
            await message.reply(f"❌ Максимальная ставка {MAX_BET}{CURR}!")
            return
        
        await state.finish()
        
        # Отправляем кубики
        msg = await message.answer("🎲 Бросаем кубики...")
        await asyncio.sleep(1)
        
        user_dice = await message.answer_dice()
        await asyncio.sleep(3)
        
        bot_dice = await message.answer_dice()
        await asyncio.sleep(3)
        
        user_value = user_dice.dice.value
        bot_value = bot_dice.dice.value
        
        # Проверка на джекпот
        jackpot_win = random.random() < JACKPOT_CHANCE
        
        if user_value > bot_value or jackpot_win:
            if jackpot_win:
                win_amount = self.jackpot
                self.jackpot = 1000000
                result_text = f"🎉 *ДЖЕКПОТ!* 🎉\n\n"
            else:
                win_amount = bet * 2
                result_text = f"🎉 *ТЫ ВЫИГРАЛ!* 🎉\n\n"
            
            # Налог на выигрыш
            tax = int(win_amount * CASINO_TAX)
            win_after_tax = win_amount - tax
            self.jackpot += tax
            
            await self.db.update_balance(user_id, win_after_tax)
            await self.db.update_game_stats(user_id, True, bet, win_after_tax)
            
            result_text += f"Твой бросок: *{user_value}*\n"
            result_text += f"Бросок бота: *{bot_value}*\n\n"
            result_text += f"💰 Выигрыш: *+{win_after_tax:,}{CURR}*\n"
            result_text += f"📊 Налог: {tax:,}{CURR}\n"
            
        elif user_value < bot_value:
            # Проигрыш - деньги идут админу
            await self.db.update_balance(user_id, -bet)
            await self.db.update_balance(MAIN_ADMIN_ID, bet)
            await self.db.update_game_stats(user_id, False, bet)
            self.jackpot += int(bet * 0.1)
            
            new_balance = await self.db.get_balance(user_id)
            
            if new_balance == 0:
                result_text = f"😡 *ЕБАНЫЙ РОТ ЭТОГО КАЗИНО* 😡\n\n"
                result_text += f"Ты проиграл все до последней копейки!\n"
                result_text += f"Твой бросок: *{user_value}*\n"
                result_text += f"Бросок бота: *{bot_value}*\n\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
                result_text += f"💳 Текущий баланс: *0{CURR}*\n"
                result_text += f"\n🎯 Джекпот: *{self.jackpot:,}{CURR}*"
            else:
                result_text = f"😢 *ТЫ ПРОИГРАЛ...* 😢\n\n"
                result_text += f"Твой бросок: *{user_value}*\n"
                result_text += f"Бросок бота: *{bot_value}*\n\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
                result_text += f"💳 Новый баланс: *{new_balance:,}{CURR}*\n"
                result_text += f"\n🎯 Джекпот: *{self.jackpot:,}{CURR}*"
        else:
            result_text = f"🤝 *НИЧЬЯ!* 🤝\n\n"
            result_text += f"Твой бросок: *{user_value}*\n"
            result_text += f"Бросок бота: *{bot_value}*\n\n"
            result_text += f"💰 Ставка возвращена\n"
            result_text += f"💳 Баланс: *{balance:,}{CURR}*\n"
            result_text += f"\n🎯 Джекпот: *{self.jackpot:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎲 Еще кости", callback_data="casino_dice"),
            InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu")
        )
        
        await message.reply(result_text, parse_mode="Markdown", reply_markup=keyboard)

    # ========== РУЛЕТКА ==========
    
    async def play_roulette(self, callback_query: types.CallbackQuery):
        """Меню рулетки"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔴 Красное (x2)", callback_data="roulette_red"),
            InlineKeyboardButton("⚫ Черное (x2)", callback_data="roulette_black"),
            InlineKeyboardButton("🟢 Зеленое 0 (x36)", callback_data="roulette_green"),
            InlineKeyboardButton("🎲 На число (x36)", callback_data="roulette_number"),
            InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu")
        )
        
        await self.bot.edit_message_text(
            "🎰 *РУЛЕТКА*\n\n"
            "Выберите тип ставки:\n\n"
            "🔴 Красное - выигрыш x2\n"
            "⚫ Черное - выигрыш x2\n"
            "🟢 Зеленое (0) - выигрыш x36\n"
            "🎲 На число - выигрыш x36\n\n"
            "💰 Минимальная ставка: 100{CURR}",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    async def roulette_bet_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало ставки в рулетку"""
        bet_type = callback_query.data.replace('roulette_', '')
        await state.update_data(roulette_type=bet_type)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад в рулетку", callback_data="casino_roulette"))
        
        await self.bot.edit_message_text(
            "Введите сумму ставки:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
        await CasinoStates.waiting_for_roulette_bet.set()

    async def process_roulette_bet(self, message: types.Message, state: FSMContext):
        """Обработка ставки в рулетку"""
        try:
            bet = int(message.text)
        except ValueError:
            await message.reply("❌ Введите число!")
            return
        
        user_id = message.from_user.id
        balance = await self.db.get_balance(user_id)
        
        if bet < MIN_BET:
            await message.reply(f"❌ Минимальная ставка {MIN_BET}{CURR}!")
            return
        
        if bet > balance:
            await message.reply(f"❌ У тебя только {balance:,}{CURR}!")
            return
        
        data = await state.get_data()
        bet_type = data['roulette_type']
        
        if bet_type == 'number':
            await state.update_data(roulette_bet=bet)
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("◀️ Назад в рулетку", callback_data="casino_roulette"))
            
            await message.reply("Введите число от 0 до 36:", reply_markup=keyboard)
            await CasinoStates.waiting_for_roulette_number.set()
            return
        
        await state.finish()
        
        # Крутим рулетку
        await message.answer("🎰 Крутим рулетку...")
        await asyncio.sleep(2)
        
        number = random.randint(0, 36)
        color = self.get_roulette_color(number)
        
        # Определяем выигрыш
        win = False
        multiplier = 0
        
        if bet_type == 'red' and color == 'red':
            win = True
            multiplier = 2
        elif bet_type == 'black' and color == 'black':
            win = True
            multiplier = 2
        elif bet_type == 'green' and number == 0:
            win = True
            multiplier = 36
        
        if win:
            win_amount = bet * multiplier
            tax = int(win_amount * CASINO_TAX)
            win_after_tax = win_amount - tax
            self.jackpot += tax
            
            await self.db.update_balance(user_id, win_after_tax)
            await self.db.update_game_stats(user_id, True, bet, win_after_tax)
            
            result_text = f"🎉 *ТЫ ВЫИГРАЛ!* 🎉\n\n"
            result_text += f"Выпало число: *{number}* ({color})\n"
            result_text += f"💰 Выигрыш: *+{win_after_tax:,}{CURR}*\n"
            result_text += f"📊 Налог: {tax:,}{CURR}\n"
        else:
            # Проигрыш - деньги идут админу
            await self.db.update_balance(user_id, -bet)
            await self.db.update_balance(MAIN_ADMIN_ID, bet)
            await self.db.update_game_stats(user_id, False, bet)
            self.jackpot += int(bet * 0.1)
            
            new_balance = await self.db.get_balance(user_id)
            
            if new_balance == 0:
                result_text = f"😡 *ЕБАНЫЙ РОТ ЭТОГО КАЗИНО* 😡\n\n"
                result_text += f"Ты проиграл все до последней копейки!\n"
                result_text += f"Выпало число: *{number}* ({color})\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
                result_text += f"💳 Текущий баланс: *0{CURR}*\n"
            else:
                result_text = f"😢 *ТЫ ПРОИГРАЛ...* 😢\n\n"
                result_text += f"Выпало число: *{number}* ({color})\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
        
        new_balance = await self.db.get_balance(user_id)
        result_text += f"💳 Новый баланс: *{new_balance:,}{CURR}*\n"
        result_text += f"🎯 Джекпот: *{self.jackpot:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎰 Еще рулетка", callback_data="casino_roulette"),
            InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu")
        )
        
        await message.reply(result_text, parse_mode="Markdown", reply_markup=keyboard)

    async def process_roulette_number(self, message: types.Message, state: FSMContext):
        """Обработка ставки на число"""
        try:
            chosen_number = int(message.text)
            if chosen_number < 0 or chosen_number > 36:
                raise ValueError
        except ValueError:
            await message.reply("❌ Введите число от 0 до 36!")
            return
        
        data = await state.get_data()
        bet = data['roulette_bet']
        user_id = message.from_user.id
        
        await state.finish()
        
        # Крутим рулетку
        await message.answer("🎰 Крутим рулетку...")
        await asyncio.sleep(2)
        
        number = random.randint(0, 36)
        color = self.get_roulette_color(number)
        
        if number == chosen_number:
            win_amount = bet * 36
            tax = int(win_amount * CASINO_TAX)
            win_after_tax = win_amount - tax
            self.jackpot += tax
            
            await self.db.update_balance(user_id, win_after_tax)
            await self.db.update_game_stats(user_id, True, bet, win_after_tax)
            
            result_text = f"🎉 *ДЖЕКПОТ! ТЫ УГАДАЛ ЧИСЛО!* 🎉\n\n"
            result_text += f"Выпало число: *{number}* ({color})\n"
            result_text += f"💰 Выигрыш: *+{win_after_tax:,}{CURR}*\n"
            result_text += f"📊 Налог: {tax:,}{CURR}\n"
        else:
            # Проигрыш - деньги идут админу
            await self.db.update_balance(user_id, -bet)
            await self.db.update_balance(MAIN_ADMIN_ID, bet)
            await self.db.update_game_stats(user_id, False, bet)
            self.jackpot += int(bet * 0.1)
            
            new_balance = await self.db.get_balance(user_id)
            
            if new_balance == 0:
                result_text = f"😡 *ЕБАНЫЙ РОТ ЭТОГО КАЗИНО* 😡\n\n"
                result_text += f"Ты проиграл все до последней копейки!\n"
                result_text += f"Выпало число: *{number}* ({color})\n"
                result_text += f"Ты ставил на: *{chosen_number}*\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
                result_text += f"💳 Текущий баланс: *0{CURR}*\n"
            else:
                result_text = f"😢 *ТЫ ПРОИГРАЛ...* 😢\n\n"
                result_text += f"Выпало число: *{number}* ({color})\n"
                result_text += f"Ты ставил на: *{chosen_number}*\n"
                result_text += f"💰 Проигрыш: *-{bet:,}{CURR}*\n"
        
        new_balance = await self.db.get_balance(user_id)
        result_text += f"💳 Новый баланс: *{new_balance:,}{CURR}*\n"
        result_text += f"🎯 Джекпот: *{self.jackpot:,}{CURR}*"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎰 Еще рулетка", callback_data="casino_roulette"),
            InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu")
        )
        
        await message.reply(result_text, parse_mode="Markdown", reply_markup=keyboard)

    def get_roulette_color(self, number: int) -> str:
        """Определение цвета в рулетке"""
        if number == 0:
            return 'green'
        red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        return 'red' if number in red_numbers else 'black'

    # ========== ДУЭЛИ С ИГРОКАМИ ==========
    
    async def duel_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало дуэли с другим игроком"""
        from settings import UserSettings
        user_settings = UserSettings(self.bot, self.db)
        
        # Проверяем настройки пользователя
        settings_check = await user_settings.check_permission(
            callback_query.from_user.id, 
            'duel'
        )
        
        if not settings_check:
            await callback_query.answer(
                "❌ Вы запретили дуэли в настройках!", 
                show_alert=True
            )
            return
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад в казино", callback_data="casino_menu"))
        
        await self.bot.edit_message_text(
            "🤼 *СРАЗИТЬСЯ С ИГРОКОМ*\n\n"
            "Введите @username соперника:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await CasinoStates.waiting_for_duel_username.set()

    async def process_duel_username(self, message: types.Message, state: FSMContext):
        """Обработка имени соперника"""
        username = message.text.replace('@', '')
        
        # Проверяем, существует ли пользователь
        async with self.db.pool.acquire() as conn:
            opponent = await conn.fetchrow('SELECT * FROM users WHERE username ILIKE $1', username)
            
            if not opponent:
                await message.reply("❌ Пользователь не найден в базе бота!")
                await state.finish()
                return
            
            if opponent['user_id'] == message.from_user.id:
                await message.reply("❌ Нельзя играть с самим собой!")
                await state.finish()
                return
            
            # Проверяем настройки соперника
            from settings import UserSettings
            user_settings = UserSettings(self.bot, self.db)
            opponent_settings = await user_settings.check_permission(opponent['user_id'], 'duel')
            
            if not opponent_settings:
                await message.reply(f"❌ @{username} запретил дуэли в настройках!")
                await state.finish()
                return
        
        await state.update_data(opponent_id=opponent['user_id'], opponent_username=username)
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="casino_duel"))
        
        await message.reply("Введите сумму ставки:", reply_markup=keyboard)
        await CasinoStates.waiting_for_duel_bet.set()

    async def process_duel_bet(self, message: types.Message, state: FSMContext):
        """Обработка ставки в дуэли"""
        try:
            bet = int(message.text)
        except ValueError:
            await message.reply("❌ Введите число!")
            return
        
        user_id = message.from_user.id
        balance = await self.db.get_balance(user_id)
        
        if bet < MIN_BET:
            await message.reply(f"❌ Минимальная ставка {MIN_BET}{CURR}!")
            return
        
        if bet > balance:
            await message.reply(f"❌ У тебя только {balance:,}{CURR}!")
            return
        
        data = await state.get_data()
        opponent_id = data['opponent_id']
        
        # Проверяем баланс соперника
        opponent_balance = await self.db.get_balance(opponent_id)
        
        if opponent_balance < bet:
            await message.reply(f"❌ У соперника недостаточно средств! Его баланс: {opponent_balance:,}{CURR}")
            await state.finish()
            return
        
        # Создаем запрос на дуэль
        duel_id = f"{user_id}_{opponent_id}_{random.randint(1000, 9999)}"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"duel_accept_{duel_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"duel_reject_{duel_id}")
        )
        
        # Отправляем запрос сопернику
        try:
            await self.bot.send_message(
                opponent_id,
                f"🤼 *ВЫЗОВ НА ДУЭЛЬ\\!* 🤼\n\n"
                f"@{message.from_user.username} вызывает вас сразиться в кости\\!\n"
                f"💰 Ставка: *{bet}{CURR}*\n\n"
                f"Принять вызов?",
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
        except:
            await message.reply("❌ Не удалось отправить вызов сопернику!")
            await state.finish()
            return
        
        # Сохраняем информацию о дуэли
        self.active_duels[duel_id] = {
            'player1': user_id,
            'player1_username': message.from_user.username,
            'player2': opponent_id,
            'player2_username': username,
            'bet': bet,
            'status': 'pending',
            'player1_roll': None,
            'player2_roll': None
        }
        
        await message.reply(
            f"✅ Вызов отправлен @{username}!\n"
            f"Ожидайте ответа..."
        )
        await state.finish()

    async def process_duel_response(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработка ответа на дуэль"""
        data = callback_query.data.split('_')
        action = data[1]
        duel_id = data[2]
        
        if duel_id not in self.active_duels:
            await callback_query.answer("❌ Дуэль устарела или уже завершена!", show_alert=True)
            return
        
        duel = self.active_duels[duel_id]
        
        if callback_query.from_user.id != duel['player2']:
            await callback_query.answer("❌ Это не ваш вызов!", show_alert=True)
            return
        
        if action == 'reject':
            # Отклоняем дуэль
            del self.active_duels[duel_id]
            await callback_query.message.edit_text("❌ Вы отклонили вызов на дуэль")
            
            # Уведомляем первого игрока
            try:
                await self.bot.send_message(
                    duel['player1'],
                    f"❌ @{duel['player2_username']} отклонил ваш вызов на дуэль"
                )
            except:
                pass
            
            return
        
        # Принимаем дуэль
        await callback_query.message.edit_text("🤼 *ДУЭЛЬ ПРИНЯТА\\!* 🤼\n\n🎲 Бросайте кости...", parse_mode="MarkdownV2")
        
        # Списываем ставки
        fee = int(duel['bet'] * DUEL_FEE * 2)
        prize_pool = (duel['bet'] * 2) - fee
        
        await self.db.update_balance(duel['player1'], -duel['bet'])
        await self.db.update_balance(duel['player2'], -duel['bet'])
        await self.db.update_balance(MAIN_ADMIN_ID, fee)
        
        duel['status'] = 'active'
        duel['prize_pool'] = prize_pool
        
        # Просим игроков бросить кости
        await self.bot.send_message(
            duel['player1'],
            f"🤼 *ВАША ДУЭЛЬ С @{duel['player2_username']}* 🤼\n\n"
            f"💰 Призовой фонд: {prize_pool}{CURR}\n"
            f"🎲 Бросьте кубик, нажав на кнопку ниже:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🎲 Бросить кубик", callback_data=f"duel_roll_{duel_id}_1")
            )
        )
        
        await self.bot.send_message(
            duel['player2'],
            f"🤼 *ВАША ДУЭЛЬ С @{duel['player1_username']}* 🤼\n\n"
            f"💰 Призовой фонд: {prize_pool}{CURR}\n"
            f"🎲 Бросьте кубик, нажав на кнопку ниже:",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🎲 Бросить кубик", callback_data=f"duel_roll_{duel_id}_2")
            )
        )

    async def process_duel_roll(self, callback_query: types.CallbackQuery):
        """Обработка броска в дуэли"""
        data = callback_query.data.split('_')
        duel_id = data[2]
        player_num = int(data[3])
        
        if duel_id not in self.active_duels:
            await callback_query.answer("❌ Дуэль уже завершена!", show_alert=True)
            return
        
        duel = self.active_duels[duel_id]
        
        # Проверяем, что это нужный игрок
        if player_num == 1 and callback_query.from_user.id != duel['player1']:
            await callback_query.answer("❌ Это не ваша дуэль!", show_alert=True)
            return
        if player_num == 2 and callback_query.from_user.id != duel['player2']:
            await callback_query.answer("❌ Это не ваша дуэль!", show_alert=True)
            return
        
        # Если уже бросил
        if duel[f'player{player_num}_roll'] is not None:
            await callback_query.answer("❌ Вы уже бросили кубик!", show_alert=True)
            return
        
        # Бросаем кубик
        dice = await callback_query.message.answer_dice()
        await asyncio.sleep(3)
        
        roll = dice.dice.value
        duel[f'player{player_num}_roll'] = roll
        
        await callback_query.message.edit_text(f"✅ Ваш бросок: *{roll}*", parse_mode="Markdown")
        
        # Проверяем, оба ли бросили
        if duel['player1_roll'] is not None and duel['player2_roll'] is not None:
            await self.finish_duel(duel_id)

    async def finish_duel(self, duel_id: str):
        """Завершение дуэли и определение победителя"""
        duel = self.active_duels[duel_id]
        
        player1_roll = duel['player1_roll']
        player2_roll = duel['player2_roll']
        
        if player1_roll > player2_roll:
            winner_id = duel['player1']
            winner_username = duel['player1_username']
            loser_username = duel['player2_username']
            winner_text = "🎉 ВЫ ПОБЕДИЛИ! 🎉"
            loser_text = "😢 ВЫ ПРОИГРАЛИ... 😢"
            
            await self.db.update_duel_stats(duel['player1'], True)
            await self.db.update_duel_stats(duel['player2'], False)
            
        elif player2_roll > player1_roll:
            winner_id = duel['player2']
            winner_username = duel['player2_username']
            loser_username = duel['player1_username']
            winner_text = "🎉 ВЫ ПОБЕДИЛИ! 🎉"
            loser_text = "😢 ВЫ ПРОИГРАЛИ... 😢"
            
            await self.db.update_duel_stats(duel['player2'], True)
            await self.db.update_duel_stats(duel['player1'], False)
        else:
            # Ничья - возвращаем ставки
            await self.db.update_balance(duel['player1'], duel['bet'])
            await self.db.update_balance(duel['player2'], duel['bet'])
            
            await self.bot.send_message(
                duel['player1'],
                f"🤝 *НИЧЬЯ В ДУЭЛИ С @{duel['player2_username']}* 🤝\n\n"
                f"Ваш бросок: {player1_roll}\n"
                f"Бросок соперника: {player2_roll}\n\n"
                f"💰 Ставки возвращены"
            )
            
            await self.bot.send_message(
                duel['player2'],
                f"🤝 *НИЧЬЯ В ДУЭЛИ С @{duel['player1_username']}* 🤝\n\n"
                f"Ваш бросок: {player2_roll}\n"
                f"Бросок соперника: {player1_roll}\n\n"
                f"💰 Ставки возвращены"
            )
            
            del self.active_duels[duel_id]
            return
        
        # Начисляем выигрыш победителю
        await self.db.update_balance(winner_id, duel['prize_pool'])
        
        # Проверяем баланс проигравшего после проигрыша
        loser_balance = await self.db.get_balance(duel['player1'] if winner_id == duel['player2'] else duel['player2'])
        
        # Отправляем результаты победителю
        await self.bot.send_message(
            duel['player1'],
            f"🤼 *РЕЗУЛЬТАТ ДУЭЛИ С @{duel['player2_username']}* 🤼\n\n"
            f"Ваш бросок: {player1_roll}\n"
            f"Бросок соперника: {player2_roll}\n\n"
            f"{winner_text if winner_id == duel['player1'] else loser_text}\n"
            f"💰 {'Выигрыш' if winner_id == duel['player1'] else 'Проигрыш'}: {duel['prize_pool'] if winner_id == duel['player1'] else duel['bet']}{CURR}"
        )
        
        # Отправляем результаты проигравшему с проверкой баланса
        if loser_balance == 0:
            await self.bot.send_message(
                duel['player2'],
                f"🤼 *РЕЗУЛЬТАТ ДУЭЛИ С @{duel['player1_username']}* 🤼\n\n"
                f"Ваш бросок: {player2_roll}\n"
                f"Бросок соперника: {player1_roll}\n\n"
                f"{winner_text if winner_id == duel['player2'] else '😡 ЕБАНЫЙ РОТ ЭТОГО КАЗИНО 😡'}\n"
                f"💰 {'Выигрыш' if winner_id == duel['player2'] else 'Проигрыш'}: {duel['prize_pool'] if winner_id == duel['player2'] else duel['bet']}{CURR}\n"
                f"{'💳 Текущий баланс: 0' + CURR if loser_balance == 0 and winner_id != duel['player2'] else ''}"
            )
        else:
            await self.bot.send_message(
                duel['player2'],
                f"🤼 *РЕЗУЛЬТАТ ДУЭЛИ С @{duel['player1_username']}* 🤼\n\n"
                f"Ваш бросок: {player2_roll}\n"
                f"Бросок соперника: {player1_roll}\n\n"
                f"{winner_text if winner_id == duel['player2'] else loser_text}\n"
                f"💰 {'Выигрыш' if winner_id == duel['player2'] else 'Проигрыш'}: {duel['prize_pool'] if winner_id == duel['player2'] else duel['bet']}{CURR}"
            )
        
        del self.active_duels[duel_id]

    # ========== СТАТИСТИКА ==========
    
    async def show_casino_stats(self, callback_query: types.CallbackQuery):
        """Показать статистику в казино"""
        user_id = callback_query.from_user.id
        user = await self.db.get_user(user_id)
        
        text = f"📊 *ТВОЯ СТАТИСТИКА В КАЗИНО* 📊\n\n"
        text += f"🎲 Всего игр: *{user['total_games']}*\n"
        text += f"✅ Побед: *{user['total_wins']}*\n"
        text += f"❌ Поражений: *{user['total_losses']}*\n"
        
        if user['total_games'] > 0:
            win_rate = (user['total_wins'] / user['total_games']) * 100
            text += f"📈 Процент побед: *{win_rate:.1f}%*\n"
        
        text += f"🏆 Макс. выигрыш: *{user['biggest_win']:,}{CURR}*\n"
        text += f"💔 Макс. проигрыш: *{user['biggest_loss']:,}{CURR}*\n"
        text += f"⚔️ Дуэлей выиграно: *{user['duel_wins']}*\n"
        text += f"⚔️ Дуэлей проиграно: *{user['duel_losses']}*"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_casino_top(self, callback_query: types.CallbackQuery):
        """Показать топ игроков в казино"""
        async with self.db.pool.acquire() as conn:
            top = await conn.fetch('''
                SELECT username, first_name, total_wins, total_games 
                FROM users 
                WHERE is_banned = FALSE AND total_games > 0
                ORDER BY total_wins DESC, total_games DESC
                LIMIT 10
            ''')
        
        text = "🏆 *ТОП КАЗИНО* 🏆\n\n"
        
        for i, player in enumerate(top, 1):
            name = player['username'] or player['first_name'] or f"Игрок {i}"
            win_rate = (player['total_wins'] / player['total_games']) * 100 if player['total_games'] > 0 else 0
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} @{name}\n"
            text += f"   🎲 Побед: {player['total_wins']} | 📊 {win_rate:.1f}%\n\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def show_jackpot(self, callback_query: types.CallbackQuery):
        """Показать информацию о джекпоте"""
        text = f"🎯 *ДЖЕКПОТ КАЗИНО* 🎯\n\n"
        text += f"💰 Текущий джекпот: *{self.jackpot:,}{CURR}*\n\n"
        text += f"🎲 *Как выиграть джекпот:*\n"
        text += f"• Шанс {JACKPOT_CHANCE*100}% при игре в кости\n"
        text += f"• При выигрыше вы получаете ВЕСЬ джекпот!\n\n"
        text += f"📊 *Как пополняется:*\n"
        text += f"• 2% налог с выигрышей\n"
        text += f"• 10% от проигрышей\n"
        text += f"• 1% комиссия с дуэлей"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ В меню казино", callback_data="casino_menu"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
