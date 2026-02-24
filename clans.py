from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from confirmations import ConfirmationSystem
from config import *

class ClanStates(StatesGroup):
    waiting_for_clan_name = State()
    waiting_for_clan_tag = State()
    waiting_for_clan_description = State()
    waiting_for_clan_type = State()
    waiting_for_application_text = State()

class Clans:
    def __init__(self, bot, db: Database, confirmations: ConfirmationSystem):
        self.bot = bot
        self.db = db
        self.confirmations = confirmations
        
        self.clan_types = {
            'open': '🔓 Открытый (можно вступить сразу)',
            'closed': '🔒 Закрытый (по заявкам)',
            'invite': '📨 По приглашениям'
        }

    async def show_clans_menu(self, message: types.Message):
        """Главное меню кланов"""
        user_id = message.from_user.id
        user_clan = await self.db.get_user_clan(user_id)
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        if user_clan:
            keyboard.add(
                InlineKeyboardButton("🏰 Мой клан", callback_data="my_clan"),
                InlineKeyboardButton("👥 Участники", callback_data="clan_members"),
                InlineKeyboardButton("💰 Казна", callback_data="clan_treasury"),
                InlineKeyboardButton("⚙️ Управление", callback_data="clan_manage")
            )
        else:
            keyboard.add(
                InlineKeyboardButton("💰 Создать клан", callback_data="clan_create"),
                InlineKeyboardButton("🔍 Найти клан", callback_data="clan_list_1"),
                InlineKeyboardButton("📋 Мои заявки", callback_data="my_applications"),
                InlineKeyboardButton("🏆 Топ кланов", callback_data="clan_top")
            )
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="menu"))
        
        text = "🏰 *КЛАНЫ МЕГАРОЛЛ* 🏰\n\n"
        
        if user_clan:
            clan_type_emoji = "🔓" if user_clan['type'] == 'open' else "🔒"
            text += f"Вы в клане: *{user_clan['name']}* [{user_clan['tag']}]\n"
            text += f"Тип: {clan_type_emoji}\n"
            text += f"Участников: *{user_clan['members_count']}/{user_clan['max_members']}*\n"
            text += f"Казна: *{user_clan['balance']:,}{CURR}*\n"
            if user_clan['description']:
                text += f"\n📝 *Описание:* {user_clan['description']}\n"
        else:
            text += f"💰 Создание клана: *{CLAN_CREATE_PRICE}{CURR}*\n"
            text += f"👥 Макс. участников: *{CLAN_MAX_MEMBERS}*\n\n"
            text += "Создайте свой клан или вступите в существующий!"
        
        await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)

    async def clan_list(self, callback_query: types.CallbackQuery, page: int = 1):
        """Показать список кланов"""
        clans = await self.db.get_all_clans(page)
        total_clans = await self.db.get_total_clans()
        total_pages = (total_clans + 4) // 5
        
        text = f"📋 *СПИСОК КЛАНОВ (стр. {page}/{total_pages})* 📋\n\n"
        
        for i, clan in enumerate(clans, (page-1)*5 + 1):
            clan_type_emoji = "🔓" if clan['type'] == 'open' else "🔒" if clan['type'] == 'closed' else "📨"
            text += f"{i}. {clan_type_emoji} *{clan['name']}* [{clan['tag']}]\n"
            text += f"   👑 Владелец: @{clan['owner_name'] or 'Неизвестно'}\n"
            text += f"   👥 Участников: {clan['members_count']}/{clan['max_members']}\n"
            text += f"   💰 Казна: {clan['balance']:,}{CURR}\n\n"
            
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(
                f"🔍 Просмотреть {clan['name']}",
                callback_data=f"clan_view_{clan['id']}"
            ))
            
            await callback_query.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
            text = ""
        
        nav_keyboard = InlineKeyboardMarkup(row_width=3)
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"clan_list_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="clan_list_current"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"clan_list_{page+1}"))
        
        nav_keyboard.row(*nav_buttons)
        nav_keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="menu"))
        
        await callback_query.message.answer("Навигация:", reply_markup=nav_keyboard)
        await callback_query.message.delete()

    async def view_clan(self, callback_query: types.CallbackQuery):
        """Просмотр информации о клане"""
        clan_id = int(callback_query.data.replace('clan_view_', ''))
        user_id = callback_query.from_user.id
        
        async with self.db.pool.acquire() as conn:
            clan = await conn.fetchrow('''
                SELECT c.*, u.username as owner_name
                FROM clans c
                JOIN users u ON c.owner_id = u.user_id
                WHERE c.id = $1
            ''', clan_id)
            
            is_member = await conn.fetchval('SELECT 1 FROM clan_members WHERE clan_id = $1 AND user_id = $2', clan_id, user_id)
        
        clan_type_emoji = "🔓" if clan['type'] == 'open' else "🔒" if clan['type'] == 'closed' else "📨"
        
        text = f"{clan_type_emoji} *{clan['name']}* [{clan['tag']}]\n\n"
        text += f"👑 *Владелец:* @{clan['owner_name']}\n"
        text += f"👥 *Участников:* {clan['members_count']}/{clan['max_members']}\n"
        text += f"💰 *Казна:* {clan['balance']:,}{CURR}\n\n"
        
        if clan['description']:
            text += f"📝 *Описание:* {clan['description']}\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        if not is_member:
            if clan['type'] == 'open':
                keyboard.add(InlineKeyboardButton("✅ Вступить", callback_data=f"clan_join_{clan_id}"))
            elif clan['type'] == 'closed':
                keyboard.add(InlineKeyboardButton("📝 Подать заявку", callback_data=f"clan_apply_{clan_id}"))
        
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="clan_list_1"))
        
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    async def create_clan_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало создания клана"""
        user_id = callback_query.from_user.id
        
        user_clan = await self.db.get_user_clan(user_id)
        if user_clan:
            await callback_query.answer("❌ Вы уже в клане!", show_alert=True)
            return
        
        user = await self.db.get_user(user_id)
        if user['balance'] < CLAN_CREATE_PRICE:
            await callback_query.answer(f"❌ Нужно {CLAN_CREATE_PRICE}{CURR}!", show_alert=True)
            return
        
        await callback_query.message.edit_text("Введите название клана (от 3 до 20 символов):")
        await ClanStates.waiting_for_clan_name.set()

    async def process_clan_name(self, message: types.Message, state: FSMContext):
        """Обработка названия клана"""
        name = message.text.strip()
        
        if len(name) < 3 or len(name) > 20:
            await message.reply("❌ Название должно быть от 3 до 20 символов!")
            return
        
        await state.update_data(clan_name=name)
        await message.reply("Введите тег клана (2-5 символов, например: LEG):")
        await ClanStates.waiting_for_clan_tag.set()

    async def process_clan_tag(self, message: types.Message, state: FSMContext):
        """Обработка тега клана"""
        tag = message.text.upper().strip()
        
        if len(tag) < 2 or len(tag) > 5:
            await message.reply("❌ Тег должен быть от 2 до 5 символов!")
            return
        
        await state.update_data(clan_tag=tag)
        await message.reply("Введите описание клана (макс. 200 символов):")
        await ClanStates.waiting_for_clan_description.set()

    async def process_clan_description(self, message: types.Message, state: FSMContext):
        """Обработка описания клана"""
        description = message.text.strip()
        
        if len(description) > 200:
            await message.reply("❌ Описание слишком длинное!")
            return
        
        await state.update_data(description=description)
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for type_key, type_name in self.clan_types.items():
            keyboard.add(InlineKeyboardButton(type_name, callback_data=f"clan_type_{type_key}"))
        
        await message.reply("Выберите тип клана:", reply_markup=keyboard)
        await ClanStates.waiting_for_clan_type.set()

    async def process_clan_type(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработка типа клана"""
        clan_type = callback_query.data.replace('clan_type_', '')
        
        data = await state.get_data()
        
        await self.confirmations.ask_confirmation(
            callback_query.message,
            'create_clan',
            {
                'text': f"Создание клана:\n"
                        f"Название: {data['clan_name']} [{data['clan_tag']}]\n"
                        f"Тип: {self.clan_types[clan_type]}\n"
                        f"Описание: {data['description']}\n"
                        f"Стоимость: {CLAN_CREATE_PRICE}{CURR}",
                'clan_name': data['clan_name'],
                'clan_tag': data['clan_tag'],
                'description': data['description'],
                'clan_type': clan_type
            },
            'CREATE_CLAN_CONFIRM',
            'CANCEL'
        )

    async def execute_create_clan(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Выполнение создания клана"""
        data = await state.get_data()
        confirmed = data.get('confirmed_data', {})
        
        result = await self.db.create_clan(
            callback_query.from_user.id,
            confirmed['clan_name'],
            confirmed['clan_tag'],
            confirmed['description'],
            confirmed['clan_type']
        )
        
        await callback_query.message.edit_text(result['message'], parse_mode="Markdown")
        await state.finish()

    async def apply_to_clan(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Подача заявки в клан"""
        clan_id = int(callback_query.data.replace('clan_apply_', ''))
        await state.update_data(apply_clan_id=clan_id)
        
        await callback_query.message.edit_text("Напишите сопроводительное письмо для заявки:")
        await ClanStates.waiting_for_application_text.set()

    async def process_application(self, message: types.Message, state: FSMContext):
        """Обработка текста заявки"""
        text = message.text.strip()
        
        if len(text) > 200:
            await message.reply("❌ Текст слишком длинный!")
            return
        
        data = await state.get_data()
        
        result = await self.db.apply_to_clan(data['apply_clan_id'], message.from_user.id, text)
        
        await message.reply(result['message'])
        await state.finish()

    async def join_open_clan(self, callback_query: types.CallbackQuery):
        """Вступление в открытый клан"""
        clan_id = int(callback_query.data.replace('clan_join_', ''))
        
        result = await self.db.join_open_clan(clan_id, callback_query.from_user.id)
        
        await callback_query.answer(result['message'], show_alert=True)
        if result['success']:
            await callback_query.message.delete()