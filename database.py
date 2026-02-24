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
                    exp BIGINT DEFAULT 0,
                    level INTEGER DEFAULT 1,
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
                    biggest_loss BIGINT DEFAULT 0,
                    duel_wins INTEGER DEFAULT 0,
                    duel_losses INTEGER DEFAULT 0
                )
            ''')

            # ========== ТАБЛИЦА МАШИН ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS cars (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    speed INTEGER NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    created_by BIGINT,
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
                    description TEXT,
                    price INTEGER NOT NULL,
                    camera INTEGER NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА ДОМОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS houses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    house_id INTEGER NOT NULL,
                    house_name TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    rooms INTEGER NOT NULL,
                    area INTEGER NOT NULL,
                    comfort INTEGER NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА АКСЕССУАРОВ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS accessories (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                    accessory_id INTEGER NOT NULL,
                    accessory_name TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    style INTEGER NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== ТАБЛИЦА КАСТОМНЫХ ПРЕДМЕТОВ (ДЛЯ АДМИНА) ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS custom_items (
                    id SERIAL PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    item_data JSONB NOT NULL,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # ========== ТАБЛИЦА КРИПТОВАЛЮТ ==========
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS cryptocurrencies (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    symbol TEXT UNIQUE NOT NULL,
                    price DECIMAL(20, 8) NOT NULL,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            # Проверка на администратора
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
                # Дополнительная проверка на администратора
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

    # ========== МЕТОДЫ ДЛЯ МАШИН ==========

    async def add_car(self, user_id: int, brand: str, model: str, price: int, speed: int, description: str = "", is_custom: bool = False, created_by: int = None) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                car_id = await conn.fetchval('''
                    INSERT INTO cars (user_id, brand, model, description, price, speed, is_custom, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                ''', user_id, brand, model, description, price, speed, is_custom, created_by)
                
                return {
                    'success': True,
                    'car_id': car_id,
                    'message': f'✅ Машина {model} добавлена!'
                }

    async def get_user_cars(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM cars WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    async def get_all_cars(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT * FROM cars ORDER BY price DESC')
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ ТЕЛЕФОНОВ ==========

    async def add_phone(self, user_id: int, brand: str, model: str, price: int, camera: int, description: str = "", is_custom: bool = False, created_by: int = None) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                phone_id = await conn.fetchval('''
                    INSERT INTO phones (user_id, brand, model, description, price, camera, is_custom, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                ''', user_id, brand, model, description, price, camera, is_custom, created_by)
                
                return {
                    'success': True,
                    'phone_id': phone_id,
                    'message': f'✅ Телефон {model} добавлен!'
                }

    async def get_user_phones(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM phones WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ ДОМОВ ==========

    async def add_house(self, user_id: int, house_data: Dict) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                house_id = await conn.fetchval('''
                    INSERT INTO houses (user_id, house_id, house_name, description, price, rooms, area, comfort, is_custom, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                ''', user_id, house_data['id'], house_data['name'], house_data.get('description', ''),
                    house_data['price'], house_data['rooms'], house_data['area'], 
                    house_data['comfort'], house_data.get('is_custom', False), house_data.get('created_by'))
                
                return {
                    'success': True,
                    'house_id': house_id,
                    'message': f'✅ Дом {house_data["name"]} добавлен!'
                }

    async def get_user_houses(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM houses WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ АКСЕССУАРОВ ==========

    async def add_accessory(self, user_id: int, accessory_data: Dict) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                acc_id = await conn.fetchval('''
                    INSERT INTO accessories (user_id, accessory_id, accessory_name, description, price, category, style, is_custom, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                ''', user_id, accessory_data['id'], accessory_data['name'], 
                    accessory_data.get('description', ''), accessory_data['price'],
                    accessory_data['category'], accessory_data['style'],
                    accessory_data.get('is_custom', False), accessory_data.get('created_by'))
                
                return {
                    'success': True,
                    'accessory_id': acc_id,
                    'message': f'✅ Аксессуар {accessory_data["name"]} добавлен!'
                }

    async def get_user_accessories(self, user_id: int) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM accessories WHERE user_id = $1 ORDER BY price DESC
            ''', user_id)
            return [dict(row) for row in rows]

    # ========== МЕТОДЫ ДЛЯ КАСТОМНЫХ ПРЕДМЕТОВ (АДМИНКА) ==========

    async def add_custom_item(self, item_type: str, item_data: Dict, created_by: int) -> Dict:
        async with self.pool.acquire() as conn:
            item_id = await conn.fetchval('''
                INSERT INTO custom_items (item_type, item_data, created_by)
                VALUES ($1, $2, $3)
                RETURNING id
            ''', item_type, json.dumps(item_data), created_by)
            
            return {
                'success': True,
                'item_id': item_id,
                'message': f'✅ {item_type} успешно создан!'
            }

    async def get_custom_items(self, item_type: str = None) -> List[Dict]:
        async with self.pool.acquire() as conn:
            if item_type:
                rows = await conn.fetch('SELECT * FROM custom_items WHERE item_type = $1 AND is_active = TRUE', item_type)
            else:
                rows = await conn.fetch('SELECT * FROM custom_items WHERE is_active = TRUE')
            return [dict(row) for row in rows]

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

    # ========== МЕТОДЫ ДЛЯ КАЗИНО ==========

    async def update_game_stats(self, user_id: int, won: bool, bet: int, win_amount: int = 0):
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

    async def update_duel_stats(self, user_id: int, won: bool):
        async with self.pool.acquire() as conn:
            if won:
                await conn.execute('''
                    UPDATE users SET duel_wins = duel_wins + 1 WHERE user_id = $1
                ''', user_id)
            else:
                await conn.execute('''
                    UPDATE users SET duel_losses = duel_losses + 1 WHERE user_id = $1
                ''', user_id)

    # ========== МЕТОДЫ ДЛЯ КЛАНОВ ==========

    async def create_clan(self, owner_id: int, name: str, tag: str, description: str, clan_type: str) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchval('SELECT 1 FROM clan_members WHERE user_id = $1', owner_id)
                if existing:
                    return {'success': False, 'message': '❌ Вы уже состоите в клане!'}
                
                user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', owner_id)
                if user['balance'] < CLAN_CREATE_PRICE:
                    return {'success': False, 'message': f'❌ Недостаточно средств! Нужно {CLAN_CREATE_PRICE}{CURR}'}
                
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
                ''', CLAN_CREATE_PRICE, owner_id)
                
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

    # ========== МЕТОДЫ ДЛЯ ПРОВЕРКИ АДМИНА ==========

    async def check_admin(self, user_id: int) -> bool:
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
