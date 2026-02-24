from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class ConfirmationSystem:
    def __init__(self, bot):
        self.bot = bot
        self.active_confirmations = {}

    async def ask_confirmation(self, message: types.Message, action: str, data: dict, confirm_callback: str, cancel_callback: str):
        """Запрос подтверждения действия"""
        confirm_id = f"{message.from_user.id}_{len(self.active_confirmations)}"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{confirm_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{confirm_id}")
        )
        
        self.active_confirmations[confirm_id] = {
            'user_id': message.from_user.id,
            'action': action,
            'data': data,
            'confirm_callback': confirm_callback,
            'cancel_callback': cancel_callback,
            'message_id': message.message_id
        }
        
        await message.reply(
            f"⚠️ *Подтвердите действие*\n\n{data.get('text', '')}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        return confirm_id

    async def process_confirmation(self, callback_query: types.CallbackQuery, state: FSMContext):
        """Обработка подтверждения"""
        data = callback_query.data.split('_')
        action = data[0]
        confirm_id = data[1]
        
        if confirm_id not in self.active_confirmations:
            await callback_query.answer("❌ Подтверждение устарело", show_alert=True)
            return
        
        conf = self.active_confirmations[confirm_id]
        
        if conf['user_id'] != callback_query.from_user.id:
            await callback_query.answer("❌ Это не ваше подтверждение", show_alert=True)
            return
        
        if action == 'confirm':
            await state.update_data(confirmed_data=conf['data'])
            await state.set_state(conf['confirm_callback'])
            await callback_query.message.edit_text("✅ Подтверждено! Продолжайте...")
        else:
            await callback_query.message.edit_text("❌ Действие отменено")
        
        del self.active_confirmations[confirm_id]