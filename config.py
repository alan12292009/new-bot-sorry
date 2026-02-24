import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '8239340181').split(',')]
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', '8239340181'))
MAIN_ADMIN_USERNAME = os.getenv('MAIN_ADMIN_USERNAME', 'whearegod')
BOT_NAME = os.getenv('BOT_NAME', 'МегаРолл')
BOT_VERSION = os.getenv('BOT_VERSION', '7.0.0')
CURR = os.getenv('CURR', '$')

# Проверка наличия обязательных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не найден в .env файле!")

# Настройки игры
START_BALANCE = 10000

# КОМИССИИ (ВСЕ ИДУТ АДМИНУ @whearegod)
TRANSFER_FEE = 0.002      # 0.2% при переводе между пользователями
CRYPTO_FEE = 0.0005       # 0.05% при покупке/продаже криптовалюты
GOVERNMENT_FEE = 0.20     # 20% при продаже предметов государству

# Кланы
CLAN_CREATE_PRICE = 10000  # Стоимость создания клана
CLAN_MAX_MEMBERS = 100     # Максимальное количество участников в клане

# Государство
GOVERNMENT_BUY_PERCENT = 80  # Государство покупает за 80% от цены
GOVERNMENT_FEE_PERCENT = 20  # 20% комиссия (отображается пользователю)