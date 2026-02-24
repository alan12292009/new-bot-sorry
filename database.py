import asyncpg
import datetime
import random
import logging
from typing import Optional, List, Dict
from config import *

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """Подключение к Railway PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=1,
                max_size=10,
                ssl='require'
            )
            logger.info("✅ Подключение к Railway PostgreSQL установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            raise

    async def create_tables(self):
        """Создание всех таблиц"""
        async with self.pool.acquire() as conn:
            # ========== ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance BIGINT DEFAULT 10000,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_earnings BIGINT DEFAULT 0,
                    referral_count INTEGER DEFAULT 0,
                    total_games INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    biggest_win BIGINT DEFAULT 0,
                    biggest_loss BIGINT DEFAULT 0
                )
            ''')

            # ========== ТАБЛИЦА МАШИН ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS cars (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    speed INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА ТЕЛЕФОНОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS phones (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    camera INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА ДОМОВ (НОВАЯ) ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS houses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    house_id INTEGER NOT NULL,
                    house_name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    rooms INTEGER NOT NULL,
                    area INTEGER NOT NULL,
                    comfort INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА КРИПТОВАЛЮТ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS cryptocurrencies (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    symbol TEXT UNIQUE NOT NULL,
                    price DECIMAL(20, 8) NOT NULL
                )
            ''')

            # ========== ТАБЛИЦА КРИПТО-КОШЕЛЬКОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS crypto_wallets (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    crypto_id INTEGER REFERENCES cryptocurrencies(id),
                    amount DECIMAL(20, 8) DEFAULT 0,
                    average_buy_price DECIMAL(20, 8),
                    UNIQUE(user_id, crypto_id)
                )
            ''')

            # ========== ТАБЛИЦА КЛАНОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clans (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    tag TEXT UNIQUE NOT NULL,
                    owner_id BIGINT REFERENCES users(user_id),
                    description TEXT,
                    type TEXT DEFAULT 'closed',
                    balance BIGINT DEFAULT 0,
                    members_count INTEGER DEFAULT 1,
                    max_members INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА УЧАСТНИКОВ КЛАНА ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clan_members (
                    clan_id INTEGER REFERENCES clans(id) ON DELETE CASCADE,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    role TEXT DEFAULT 'member',
                    rank INTEGER DEFAULT 1,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (clan_id, user_id)
                )
            ''')

            # ========== ТАБЛИЦА ЗАЯВОК В КЛАН ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clan_applications (
                    id SERIAL PRIMARY KEY,
                    clan_id INTEGER REFERENCES clans(id) ON DELETE CASCADE,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    message TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА ТРАНЗАКЦИЙ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    from_id BIGINT,
                    to_id BIGINT,
                    amount INTEGER NOT NULL,
                    fee INTEGER DEFAULT 0,
                    type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА ЕЖЕНЕДЕЛЬНЫХ ТОПОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weekly_top_balance (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    username TEXT,
                    balance BIGINT NOT NULL,
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    rank INTEGER,
                    claimed BOOLEAN DEFAULT FALSE
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weekly_top_referrals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    username TEXT,
                    referral_count INTEGER NOT NULL,
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    rank INTEGER,
                    claimed BOOLEAN DEFAULT FALSE
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weekly_top_clans (
                    id SERIAL PRIMARY KEY,
                    clan_id INTEGER,
                    clan_name TEXT,
                    clan_tag TEXT,
                    total_balance BIGINT NOT NULL,
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    rank INTEGER,
                    claimed BOOLEAN DEFAULT FALSE
                )
            ''')

            # ========== ТАБЛИЦА ДОСТИЖЕНИЙ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    reward INTEGER NOT NULL,
                    condition_type TEXT NOT NULL,
                    condition_value INTEGER NOT NULL
                )
            ''')

            # ========== ТАБЛИЦА ПОЛУЧЕННЫХ ДОСТИЖЕНИЙ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    achievement_id INTEGER REFERENCES achievements(id),
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, achievement_id)
                )
            ''')

            logger.info("✅ Все таблицы созданы")
            
            # Инициализация криптовалют
            await self.init_cryptocurrencies(conn)
            
            # Инициализация достижений
            await self.init_achievements(conn)

    async def init_cryptocurrencies(self, conn):
        """Инициализация криптовалют"""
        cryptos = [
            ('Bitcoin', 'BTC', 50000.00),
            ('Ethereum', 'ETH', 3000.00),
            ('Binance Coin', 'BNB', 500.00),
            ('Solana', 'SOL', 150.00),
            ('Dogecoin', 'DOGE', 0.15)
        ]
        
        for name, symbol, price in cryptos:
            await conn.execute('''
                INSERT INTO cryptocurrencies (name, symbol, price)
                VALUES ($1, $2, $3)
                ON CONFLICT (symbol) DO UPDATE SET price = EXCLUDED.price
            ''', name, symbol, price)
        
        logger.info(f"✅ {len(cryptos)} криптовалют инициализировано")

    async def init_achievements(self, conn):
        """Инициализация достижений"""
        achievements = [
            ('Новичок', 'Сыграть первую игру', 1000, 'games', 1),
            ('Игрок', 'Сыграть 100 игр', 5000, 'games', 100),
            ('Победитель', 'Выиграть 10 игр', 2000, 'wins', 10),
            ('Богач', f'Накопить 1 млн {CURR}', 50000, 'balance', 1000000),
            ('Реферал', 'Пригласить 10 друзей', 10000, 'referrals', 10)
        ]
        
        for name, desc, reward, cond_type, cond_value in achievements:
            await conn.execute('''
                INSERT INTO achievements (name, description, reward, condition_type, condition_value)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
            ''', name, desc, reward, cond_type, cond_value)
        
        logger.info(f"✅ {len(achievements)} достижений инициализировано")

    # ========== ОСНОВНЫЕ МЕТОДЫ ==========

    async def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        async with self.pool.acquire() as conn:
            existing = await conn.fetchval('SELECT user_id FROM users WHERE user_id = $1', user_id)
            if existing:
                await conn.execute('''
                    UPDATE users SET last_active = CURRENT_TIMESTAMP,
                    username = COALESCE($2, username),
                    first_name = COALESCE($3, first_name)
                    WHERE user_id = $1
                ''', user_id, username, first_name)
                return False
            
            # ВАЖНО: Правильная проверка на администратора
            from config import ADMIN_IDS, MAIN_ADMIN_ID
            is_admin = user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID
            
            await conn.execute('''
                INSERT INTO users (user_id, username, first_name, is_admin)
                VALUES ($1, $2, $3, $4)
            ''', user_id, username, first_name, is_admin)
            
            return True

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
            if row:
                user = dict(row)
                # Дополнительная проверка на администратора при каждом запросе
                from config import ADMIN_IDS, MAIN_ADMIN_ID
                if user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID:
                    user['is_admin'] = True
                return user
            return None

    async def update_balance(self, user_id: int, amount: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute('''
                UPDATE users SET balance = balance + $1, last_active = CURRENT_TIMESTAMP
                WHERE user_id = $2 AND balance + $1 >= 0
            ''', amount, user_id)
            return result == 'UPDATE 1'

    async def get_balance(self, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            balance = await conn.fetchval('SELECT balance FROM users WHERE user_id = $1', user_id)
            return balance or 0

    async def add_exp(self, user_id: int, exp: int) -> Dict:
        """Добавление опыта"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
            new_exp = user['exp'] + exp
            
            await conn.execute('''
                UPDATE users SET exp = $1 WHERE user_id = $2
            ''', new_exp, user_id)
            
            return {'exp_gained': exp}

    # ========== МЕТОДЫ ДЛЯ КАЗИНО ==========

    async def update_game_stats(self, user_id: int, won: bool, bet: int, win_amount: int = 0):
        """Обновление статистики игр в казино"""
        async with self.pool.acquire() as conn:
            if won:
                await conn.execute('''
                    UPDATE users 
                    SET total_games = total_games + 1,
                        total_wins = total_wins + 1,
                        biggest_win = GREATEST(biggest_win, $1)
                    WHERE user_id = $2
                ''', win_amount, user_id)
            else:
                await conn.execute('''
                    UPDATE users 
                    SET total_games = total_games + 1,
                        total_losses = total_losses + 1,
                        biggest_loss = GREATEST(biggest_loss, $1)
                    WHERE user_id = $2
                ''', bet, user_id)

    # ========== МЕТОДЫ ДЛЯ МАШИН ==========

    async def buy_car(self, user_id: int, brand: str, price: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
                
                if user['balance'] < price:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Нужно {price}{CURR}'}
                
                models = ['Sport', 'Luxury', 'Premium', 'Limited']
                model = f"{brand} {random.choice(models)} {random.randint(2022, 2024)}"
                speed = random.randint(200, 350)
                
                await conn.execute('''
                    INSERT INTO cars (user_id, brand, model, price, speed)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, brand, model, price, speed)
                
                await conn.execute('''
                    UPDATE users SET balance = balance - $1 WHERE user_id = $2
                ''', price, user_id)
                
                return {
                    'success': True,
                    'message': f'✅ Вы купили {model} за {price}{CURR}!',
                    'car': model
                }

    async def get_user_cars(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM cars WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ ТЕЛЕФОНОВ ==========

    async def buy_phone(self, user_id: int, brand: str, price: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
                
                if user['balance'] < price:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Нужно {price}{CURR}'}
                
                models = ['Pro Max', 'Ultra', 'Plus', 'Premium']
                model = f"{brand} {random.choice(models)} {random.randint(13, 15)}"
                camera = random.randint(48, 108)
                
                await conn.execute('''
                    INSERT INTO phones (user_id, brand, model, price, camera)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, brand, model, price, camera)
                
                await conn.execute('''
                    UPDATE users SET balance = balance - $1 WHERE user_id = $2
                ''', price, user_id)
                
                return {
                    'success': True,
                    'message': f'✅ Вы купили {model} за {price}{CURR}!',
                    'phone': model
                }

    async def get_user_phones(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM phones WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ ДОМОВ ==========

    async def buy_house(self, user_id: int, house: Dict) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
                
                if user['balance'] < house['price']:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Нужно {house["price"]}{CURR}'}
                
                await conn.execute('''
                    INSERT INTO houses (user_id, house_id, house_name, price, rooms, area, comfort)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', user_id, house['id'], house['name'], house['price'], 
                    house['rooms'], house['area'], house['comfort'])
                
                await conn.execute('''
                    UPDATE users SET balance = balance - $1 WHERE user_id = $2
                ''', house['price'], user_id)
                
                return {
                    'success': True,
                    'message': f'✅ Вы купили {house["name"]} за {house["price"]}{CURR}!'
                }

    async def get_user_houses(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM houses WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    async def sell_house_to_government(self, user_id: int, house_id: int, buy_price: int, commission: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('DELETE FROM houses WHERE id = $1', house_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', buy_price, user_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', commission, MAIN_ADMIN_ID)
                
                return {'success': True}

    # ========== МЕТОДЫ ДЛЯ КРИПТОВАЛЮТЫ ==========

    async def get_crypto_list(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM cryptocurrencies')
            return [dict(row) for row in rows]

    async def get_crypto_by_id(self, crypto_id: int) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM cryptocurrencies WHERE id = $1', crypto_id)
            return dict(row) if row else None

    async def get_user_crypto_wallet(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT cw.*, c.name, c.symbol, c.price
                FROM crypto_wallets cw
                JOIN cryptocurrencies c ON cw.crypto_id = c.id
                WHERE cw.user_id = $1 AND cw.amount > 0
            ''', user_id)
            return [dict(row) for row in rows]

    async def buy_crypto(self, user_id: int, crypto_id: int, amount_usd: float, crypto_amount: float, fee: float) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', amount_usd, user_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(fee), MAIN_ADMIN_ID)
                
                wallet = await conn.fetchrow('''
                    SELECT * FROM crypto_wallets WHERE user_id = $1 AND crypto_id = $2
                ''', user_id, crypto_id)
                
                if wallet:
                    total_amount = float(wallet['amount']) + crypto_amount
                    total_cost = (float(wallet['amount']) * float(wallet['average_buy_price'])) + (amount_usd - fee)
                    avg_price = total_cost / total_amount
                    
                    await conn.execute('''
                        UPDATE crypto_wallets SET amount = $1, average_buy_price = $2
                        WHERE user_id = $3 AND crypto_id = $4
                    ''', total_amount, avg_price, user_id, crypto_id)
                else:
                    await conn.execute('''
                        INSERT INTO crypto_wallets (user_id, crypto_id, amount, average_buy_price)
                        VALUES ($1, $2, $3, $4)
                    ''', user_id, crypto_id, crypto_amount, (amount_usd - fee) / crypto_amount)
                
                return {'success': True}

    async def sell_crypto(self, user_id: int, crypto_id: int, crypto_amount: float, usd_after_fee: float, fee: float) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(usd_after_fee), user_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', int(fee), MAIN_ADMIN_ID)
                
                wallet = await conn.fetchrow('''
                    SELECT * FROM crypto_wallets WHERE user_id = $1 AND crypto_id = $2
                ''', user_id, crypto_id)
                
                new_amount = float(wallet['amount']) - crypto_amount
                if new_amount < 0.00000001:
                    await conn.execute('DELETE FROM crypto_wallets WHERE user_id = $1 AND crypto_id = $2', user_id, crypto_id)
                else:
                    await conn.execute('UPDATE crypto_wallets SET amount = $1 WHERE user_id = $2 AND crypto_id = $3', new_amount, user_id, crypto_id)
                
                return {'success': True}

    # ========== МЕТОДЫ ДЛЯ КЛАНОВ ==========

    async def create_clan(self, owner_id: int, name: str, tag: str, description: str, clan_type: str, price: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchval('SELECT 1 FROM clan_members WHERE user_id = $1', owner_id)
                if existing:
                    return {'success': False, 'message': '❌ Вы уже состоите в клане!'}
                
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', owner_id)
                if user['balance'] < price:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Нужно {price}{CURR}'}
                
                clan_id = await conn.fetchval('''
                    INSERT INTO clans (name, tag, owner_id, description, type, balance)
                    VALUES ($1, $2, $3, $4, $5, 0)
                    RETURNING id
                ''', name, tag.upper(), owner_id, description, clan_type)
                
                await conn.execute('''
                    INSERT INTO clan_members (clan_id, user_id, role, rank)
                    VALUES ($1, $2, 'owner', 5)
                ''', clan_id, owner_id)
                
                await conn.execute('''
                    UPDATE users SET balance = balance - $1 WHERE user_id = $2
                ''', price, owner_id)
                
                return {
                    'success': True,
                    'message': f'✅ Клан {name} [{tag.upper()}] создан!',
                    'clan_id': clan_id
                }

    async def get_user_clan(self, user_id: int) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT c.*, cm.role, cm.rank
                FROM clans c
                JOIN clan_members cm ON c.id = cm.clan_id
                WHERE cm.user_id = $1
            ''', user_id)
            return dict(row) if row else None

    async def get_all_clans(self, page: int = 1, limit: int = 5) -> List[Dict]:
        async with self.pool.acquire() as conn:
            offset = (page - 1) * limit
            rows = await conn.fetch('''
                SELECT c.*, u.username as owner_name
                FROM clans c
                JOIN users u ON c.owner_id = u.user_id
                ORDER BY c.balance DESC
                LIMIT $1 OFFSET $2
            ''', limit, offset)
            return [dict(row) for row in rows]

    async def get_total_clans(self) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval('SELECT COUNT(*) FROM clans')

    async def apply_to_clan(self, clan_id: int, user_id: int, message: str) -> Dict:
        async with self.pool.acquire() as conn:
            existing = await conn.fetchval('''
                SELECT 1 FROM clan_applications 
                WHERE clan_id = $1 AND user_id = $2 AND status = 'pending'
            ''', clan_id, user_id)
            
            if existing:
                return {'success': False, 'message': '❌ Вы уже подали заявку!'}
            
            await conn.execute('''
                INSERT INTO clan_applications (clan_id, user_id, message)
                VALUES ($1, $2, $3)
            ''', clan_id, user_id, message)
            
            return {'success': True, 'message': '✅ Заявка отправлена!'}

    async def get_clan_applications(self, clan_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT a.*, u.username, u.first_name
                FROM clan_applications a
                JOIN users u ON a.user_id = u.user_id
                WHERE a.clan_id = $1 AND a.status = 'pending'
            ''', clan_id)
            return [dict(row) for row in rows]

    async def accept_application(self, app_id: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                app = await conn.fetchrow('SELECT * FROM clan_applications WHERE id = $1', app_id)
                
                if not app or app['status'] != 'pending':
                    return {'success': False, 'message': '❌ Заявка уже обработана!'}
                
                clan = await conn.fetchrow('SELECT * FROM clans WHERE id = $1', app['clan_id'])
                
                if clan['members_count'] >= clan['max_members']:
                    return {'success': False, 'message': '❌ Клан достиг максимума!'}
                
                await conn.execute('''
                    INSERT INTO clan_members (clan_id, user_id, role, rank)
                    VALUES ($1, $2, 'member', 1)
                ''', app['clan_id'], app['user_id'])
                
                await conn.execute('UPDATE clans SET members_count = members_count + 1 WHERE id = $1', app['clan_id'])
                await conn.execute('UPDATE clan_applications SET status = $1 WHERE id = $2', 'accepted', app_id)
                
                return {
                    'success': True,
                    'message': '✅ Заявка принята!',
                    'user_id': app['user_id'],
                    'clan_name': clan['name']
                }

    async def reject_application(self, app_id: int) -> Dict:
        async with self.pool.acquire() as conn:
            app = await conn.fetchrow('SELECT * FROM clan_applications WHERE id = $1', app_id)
            
            if not app or app['status'] != 'pending':
                return {'success': False, 'message': '❌ Заявка уже обработана!'}
            
            await conn.execute('UPDATE clan_applications SET status = $1 WHERE id = $2', 'rejected', app_id)
            
            return {
                'success': True,
                'message': '✅ Заявка отклонена',
                'user_id': app['user_id']
            }

    async def join_open_clan(self, clan_id: int, user_id: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                clan = await conn.fetchrow('SELECT * FROM clans WHERE id = $1 AND type = $2', clan_id, 'open')
                
                if not clan:
                    return {'success': False, 'message': '❌ Клан не найден или не является открытым!'}
                
                if clan['members_count'] >= clan['max_members']:
                    return {'success': False, 'message': '❌ Клан достиг максимума!'}
                
                existing = await conn.fetchval('SELECT 1 FROM clan_members WHERE user_id = $1', user_id)
                if existing:
                    return {'success': False, 'message': '❌ Вы уже в клане!'}
                
                await conn.execute('''
                    INSERT INTO clan_members (clan_id, user_id, role, rank)
                    VALUES ($1, $2, 'member', 1)
                ''', clan_id, user_id)
                
                await conn.execute('UPDATE clans SET members_count = members_count + 1 WHERE id = $1', clan_id)
                
                return {
                    'success': True,
                    'message': f'✅ Вы вступили в клан {clan["name"]}!'
                }

    # ========== МЕТОДЫ ДЛЯ ТРАНЗАКЦИЙ ==========

    async def transfer_money(self, from_id: int, to_id: int, amount: int, fee: int) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', amount, from_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', amount - fee, to_id)
                await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', fee, MAIN_ADMIN_ID)
                
                await conn.execute('''
                    INSERT INTO transactions (from_id, to_id, amount, fee, type)
                    VALUES ($1, $2, $3, $4, 'transfer')
                ''', from_id, to_id, amount, fee)
                
                return {'success': True}

    # ========== МЕТОДЫ ДЛЯ ЕЖЕНЕДЕЛЬНЫХ ТОПОВ ==========

    async def update_weekly_tops(self):
        """Обновление еженедельных топов"""
        async with self.pool.acquire() as conn:
            now = datetime.datetime.now()
            week_start = (now - datetime.timedelta(days=7)).date()
            week_end = now.date()
            
            await conn.execute('DELETE FROM weekly_top_balance WHERE week_end = $1', week_end)
            await conn.execute('DELETE FROM weekly_top_referrals WHERE week_end = $1', week_end)
            await conn.execute('DELETE FROM weekly_top_clans WHERE week_end = $1', week_end)
            
            await conn.execute('''
                INSERT INTO weekly_top_balance (user_id, username, balance, week_start, week_end, rank)
                SELECT user_id, username, balance, $1, $2,
                       ROW_NUMBER() OVER (ORDER BY balance DESC) as rank
                FROM users
                WHERE is_banned = FALSE
                ORDER BY balance DESC
                LIMIT 10
            ''', week_start, week_end)
            
            await conn.execute('''
                INSERT INTO weekly_top_referrals (user_id, username, referral_count, week_start, week_end, rank)
                SELECT user_id, username, referral_count, $1, $2,
                       ROW_NUMBER() OVER (ORDER BY referral_count DESC) as rank
                FROM users
                WHERE is_banned = FALSE
                ORDER BY referral_count DESC
                LIMIT 10
            ''', week_start, week_end)
            
            await conn.execute('''
                INSERT INTO weekly_top_clans (clan_id, clan_name, clan_tag, total_balance, week_start, week_end, rank)
                SELECT c.id, c.name, c.tag, c.balance, $1, $2,
                       ROW_NUMBER() OVER (ORDER BY c.balance DESC) as rank
                FROM clans c
                ORDER BY c.balance DESC
                LIMIT 10
            ''', week_start, week_end)
            
            logger.info("🏆 Еженедельные топы обновлены")

    async def get_weekly_top_balance(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM weekly_top_balance 
                WHERE week_end = (SELECT MAX(week_end) FROM weekly_top_balance)
                ORDER BY rank
            ''')
            return [dict(row) for row in rows]

    async def get_weekly_top_referrals(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM weekly_top_referrals 
                WHERE week_end = (SELECT MAX(week_end) FROM weekly_top_referrals)
                ORDER BY rank
            ''')
            return [dict(row) for row in rows]

    async def get_weekly_top_clans(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM weekly_top_clans 
                WHERE week_end = (SELECT MAX(week_end) FROM weekly_top_clans)
                ORDER BY rank
            ''')
            return [dict(row) for row in rows]

    async def get_weekly_winners(self) -> Dict:
        async with self.pool.acquire() as conn:
            balance_winner = await conn.fetchrow('''
                SELECT * FROM weekly_top_balance 
                WHERE rank = 1 AND week_end = (SELECT MAX(week_end) FROM weekly_top_balance)
            ''')
            
            referrals_winner = await conn.fetchrow('''
                SELECT * FROM weekly_top_referrals 
                WHERE rank = 1 AND week_end = (SELECT MAX(week_end) FROM weekly_top_referrals)
            ''')
            
            clans_winner = await conn.fetchrow('''
                SELECT * FROM weekly_top_clans 
                WHERE rank = 1 AND week_end = (SELECT MAX(week_end) FROM weekly_top_clans)
            ''')
            
            return {
                'balance': dict(balance_winner) if balance_winner else None,
                'referrals': dict(referrals_winner) if referrals_winner else None,
                'clans': dict(clans_winner) if clans_winner else None
            }

    # ========== МЕТОДЫ ДЛЯ ПРОВЕРКИ АДМИНА ==========

    async def check_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        from config import ADMIN_IDS, MAIN_ADMIN_ID
        return user_id in ADMIN_IDS or user_id == MAIN_ADMIN_ID

    # ========== ПРИВЕТСТВИЯ ==========

    def get_greeting(self, username: str) -> str:
        hour = datetime.datetime.now().hour
        
        if 5 <= hour <= 11:
            return f"🌅 Доброе утро, {username}!"
        elif 12 <= hour <= 17:
            return f"☀️ Добрый день, {username}!"
        elif 18 <= hour <= 23:
            return f"🌆 Добрый вечер, {username}!"
        else:
            night_greetings = [
                f"🌙 Не спится, {username}?",
                f"🦉 Полуночник {username}?",
                f"⭐ {username}, уже поздно..."
            ]
            return random.choice(night_greetings)
