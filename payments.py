from aiogram import types
from aiogram.dispatcher import FSMContext
from database import Database
from config import *
from typing import Dict

class PaymentSystem:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.admin_id = MAIN_ADMIN_ID
        self.admin_username = MAIN_ADMIN_USERNAME

    async def process_transfer(self, from_id: int, to_username: str, amount: int) -> Dict:
        """Перевод денег с комиссией админу"""
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                sender = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', from_id)
                
                if not sender:
                    return {'success': False, 'message': '❌ Отправитель не найден'}
                
                if sender['is_banned']:
                    return {'success': False, 'message': '❌ Вы забанены'}
                
                if sender['balance'] < amount:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Баланс: {sender["balance"]}{CURR}'}
                
                receiver = await conn.fetchrow('SELECT * FROM users WHERE username ILIKE $1', to_username.replace('@', ''))
                
                if not receiver:
                    return {'success': False, 'message': '❌ Получатель не найден'}
                
                if receiver['is_banned']:
                    return {'success': False, 'message': '❌ Получатель забанен'}
                
                if receiver['user_id'] == from_id:
                    return {'success': False, 'message': '❌ Нельзя перевести самому себе'}
                
                fee = int(amount * TRANSFER_FEE)
                amount_after_fee = amount - fee
                
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', amount, from_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', amount_after_fee, receiver['user_id'])
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', fee, self.admin_id)
                
                await conn.execute('''
                    INSERT INTO transactions (from_id, to_id, amount, fee, type)
                    VALUES ($1, $2, $3, $4, 'transfer')
                ''', from_id, receiver['user_id'], amount, fee)
                
                sender_name = sender['username'] or sender['first_name'] or f"ID{sender['user_id']}"
                await self.bot.send_message(
                    receiver['user_id'],
                    f"💰 *Вам перевели деньги\\!*\n\n"
                    f"От: @{sender_name}\n"
                    f"Сумма: *{amount_after_fee}{CURR}*\n"
                    f"Комиссия: {fee}{CURR} (идет @{self.admin_username})",
                    parse_mode="MarkdownV2"
                )
                
                return {
                    'success': True,
                    'message': f'✅ Переведено {amount_after_fee}{CURR} пользователю @{receiver["username"]}\nКомиссия: {fee}{CURR}',
                    'amount': amount_after_fee,
                    'fee': fee
                }

    async def process_crypto_buy(self, user_id: int, crypto_id: int, amount_usd: float, crypto_symbol: str, crypto_price: float) -> Dict:
        """Покупка крипты с комиссией админу"""
        fee = amount_usd * CRYPTO_FEE
        amount_after_fee = amount_usd - fee
        crypto_amount = amount_after_fee / crypto_price
        
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', amount_usd, user_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(fee), self.admin_id)
                
                wallet = await conn.fetchrow('SELECT * FROM crypto_wallets WHERE user_id = $1 AND crypto_id = $2', user_id, crypto_id)
                
                if wallet:
                    total_amount = float(wallet['amount']) + crypto_amount
                    total_cost = (float(wallet['amount']) * float(wallet['average_buy_price'])) + amount_after_fee
                    avg_price = total_cost / total_amount
                    
                    await conn.execute('''
                        UPDATE crypto_wallets SET amount = $1, average_buy_price = $2
                        WHERE user_id = $3 AND crypto_id = $4
                    ''', total_amount, avg_price, user_id, crypto_id)
                else:
                    await conn.execute('''
                        INSERT INTO crypto_wallets (user_id, crypto_id, amount, average_buy_price)
                        VALUES ($1, $2, $3, $4)
                    ''', user_id, crypto_id, crypto_amount, amount_after_fee / crypto_amount)
        
        return {
            'success': True,
            'message': f'✅ Куплено {crypto_amount:.8f} {crypto_symbol} за {amount_after_fee:.2f}{CURR}\nКомиссия: {fee:.2f}{CURR}',
            'crypto_amount': crypto_amount
        }

    async def process_crypto_sell(self, user_id: int, crypto_id: int, crypto_amount: float, crypto_symbol: str, crypto_price: float, avg_price: float) -> Dict:
        """Продажа крипты с комиссией админу"""
        usd_amount = crypto_amount * crypto_price
        fee = usd_amount * CRYPTO_FEE
        usd_after_fee = usd_amount - fee
        
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(usd_after_fee), user_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(fee), self.admin_id)
        
        profit = (crypto_price - avg_price) * crypto_amount
        
        return {
            'success': True,
            'message': f'✅ Продано {crypto_amount:.8f} {crypto_symbol} за {usd_after_fee:.2f}{CURR}\nКомиссия: {fee:.2f}{CURR}\nПрибыль: {profit:+.2f}{CURR}'
        }

    async def get_admin_balance(self) -> int:
        """Получение баланса админа"""
        async with self.db.pool.acquire() as conn:
            balance = await conn.fetchval('SELECT balance FROM users WHERE user_id = $1', self.admin_id)
            return balance or 0
