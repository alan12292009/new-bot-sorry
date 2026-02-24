from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import *

class SettingsStates(StatesGroup):
    waiting_for_nickname = State()

class UserSettings:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        # В реальном проекте эти настройки нужно хранить в БД
        # Здесь для простоты используем словарь
        self.user_settings = {}  # user_id -> settings dict

    def get_default_settings(self):
        """Настройки по умолчанию"""
        return {
            'nickname': None,
            'show_nickname': True,
            'allow_trades': True,
            'allow_duels': True,
            'allow_transfers': True,
            'allow_clan_invites': True,
            'notifications': True,
            'private_mode': False,
            'hide_balance': False
        }

    async def get_user_settings(self, user_id: int) -> dict:
        """Получить настройки пользователя"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = self.get_default_settings()
        return self.user_settings[user_id]

    async def save_user_settings(self, user_id: int, settings: dict):
        """Сохранить настройки пользователя"""
        self.user_settings[user_id] = settings

    async def show_settings_menu(self, message: types.Message):
        """Показать меню настроек"""
        user_id = message.from_user.id
        settings = await self.get_user_settings(user_id)
        
        nickname_display = settings['nickname'] if settings['nickname'] else "Не установлен"
        
        text = f"⚙️ *НАСТРОЙКИ ПРОФИЛЯ* ⚙️\n\n"
        text += f"👤 Твой ник: *{nickname_display}*\n"
        text += f"🆔 Твой ID: `{user_id}`\n\n"
        
        text += f"*Настройки видимости:*\n"
        text += f"• Показывать ник: {'✅' if settings['show_nickname'] else '❌'}\n"
        text += f"• Приватный режим: {'✅' if settings['private_mode'] else '❌'}\n"
        text += f"• Скрывать баланс: {'✅' if settings['hide_balance'] else '❌'}\n\n"
        
        text += f"*Блокировка действий:*\n"
        text += f"• Разрешить трейды: {'✅' if settings['allow_trades'] else '❌'}\n"
        text += f"• Разрешить дуэли: {'✅' if settings['allow_duels'] else '❌'}\n"
        text += f"• Разрешить переводы: {'✅' if settings['allow_transfers'] else '❌'}\n"
        text += f"• Разрешить приглашения в клан: {'✅' if settings['allow_clan_invites'] else '❌'}\n"
        text += f"• Уведомления: {'✅' if settings['notifications'] else '❌'}"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("👤 Установить ник", callback_data="settings_set_nick"),
            InlineKeyboardButton("🗑 Убрать ник", callback_data="settings_remove_nick")
        )
        keyboard.add(
            InlineKeyboardButton("👁 Показывать ник", callback_data="settings_toggle_show_nick"),
            InlineKeyboardButton("🔒 Приватный режим", callback_data="settings_toggle_private")
        )
        keyboard.add(
            InlineKeyboardButton("💰 Скрывать баланс", callback_data="settings_toggle_balance"),
            InlineKeyboardButton("🔄 Разрешить трейды", callback_data="settings_toggle_trades")
        )
        keyboard.add(
            InlineKeyboardButton("⚔️ Разрешить дуэли", callback_data="settings_toggle_duels"),
            InlineKeyboardButton("💸 Разрешить переводы", callback_data="settings_toggle_transfers")
        )
        keyboard.add(
            InlineKeyboardButton("🏰 Приглашения в клан", callback_data="settings_toggle_clan"),
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_toggle_notifications")
        )
        keyboard.add(
            InlineKeyboardButton("◀️ Назад", callback_data="menu")
        )
        
        await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)

    async def set_nickname_start(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Начало установки ника"""
        await callback_query.message.edit_text(
            "👤 *УСТАНОВКА НИКА*\n\n"
            "Введите желаемый ник (макс. 20 символов):\n"
            "Чтобы убрать ник, отправьте '-'",
            parse_mode="Markdown"
        )
        await SettingsStates.waiting_for_nickname.set()

    async def process_nickname(self, message: types.Message, state: FSMContext):
        """Обработка введенного ника"""
        user_id = message.from_user.id
        nickname = message.text.strip()
        
        if nickname == '-':
            nickname = None
            result_text = "✅ Ник убран"
        else:
            if len(nickname) > 20:
                await message.reply("❌ Ник слишком длинный! Максимум 20 символов.")
                return
            result_text = f"✅ Ник установлен: *{nickname}*"
        
        settings = await self.get_user_settings(user_id)
        settings['nickname'] = nickname
        await self.save_user_settings(user_id, settings)
        
        await message.reply(result_text, parse_mode="Markdown")
        await state.finish()

    async def toggle_setting(self, callback_query: types.CallbackQuery, setting: str):
        """Переключение настройки"""
        user_id = callback_query.from_user.id
        settings = await self.get_user_settings(user_id)
        
        setting_map = {
            'show_nick': 'show_nickname',
            'private': 'private_mode',
            'balance': 'hide_balance',
            'trades': 'allow_trades',
            'duels': 'allow_duels',
            'transfers': 'allow_transfers',
            'clan': 'allow_clan_invites',
            'notifications': 'notifications'
        }
        
        setting_key = setting_map.get(setting)
        if setting_key:
            settings[setting_key] = not settings[setting_key]
            await self.save_user_settings(user_id, settings)
        
        # Обновляем отображение
        await self.show_settings_menu(callback_query.message)

    async def check_permission(self, user_id: int, action_type: str) -> bool:
        """Проверка разрешения на действие"""
        settings = await self.get_user_settings(user_id)
        
        permission_map = {
            'trade': 'allow_trades',
            'duel': 'allow_duels',
            'transfer': 'allow_transfers',
            'clan_invite': 'allow_clan_invites'
        }
        
        permission_key = permission_map.get(action_type)
        if permission_key:
            return settings.get(permission_key, True)
        return True

    async def get_display_name(self, user_id: int, username: str = None, first_name: str = None) -> str:
        """Получить отображаемое имя пользователя"""
        settings = await self.get_user_settings(user_id)
        
        if settings['private_mode']:
            return "🔒 Приватный пользователь"
        
        if settings['show_nickname'] and settings['nickname']:
            return settings['nickname']
        
        if username:
            return f"@{username}"
        
        return first_name or f"ID{user_id}"
