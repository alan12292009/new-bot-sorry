import subprocess
import sys
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

def install_requirements():
    """Установка библиотек"""
    print("=" * 50)
    print("🚀 УСТАНОВЩИК МЕГАРОЛЛ v7.0")
    print("=" * 50)
    
    packages = [
        'aiogram==2.25.1',
        'asyncpg==0.28.0',
        'python-dotenv==1.0.0'
    ]
    
    for package in packages:
        print(f"📦 Установка {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
    
    print("✅ Все библиотеки установлены!")

async def test_db():
    """Тест базы данных"""
    load_dotenv()
    url = os.getenv('DATABASE_URL')
    
    if not url:
        print("❌ DATABASE_URL не найден в .env файле!")
        return False
    
    try:
        print(f"🔄 Подключение к базе данных...")
        conn = await asyncpg.connect(url, ssl='require')
        await conn.close()
        print("✅ Подключение к базе данных успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    install_requirements()
    
    print("\n" + "=" * 50)
    print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ")
    print("=" * 50)
    
    asyncio.run(test_db())
    
    print("\n" + "=" * 50)
    print("✅ Установка завершена!")
    print("🚀 Запустите бота командой: python bot.py")
    print("=" * 50)