"""Telegram бот"""
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from config import settings
from database import db
from openai_service import openai_service


# Инициализация бота (только если токен валидный)
bot = None
dp = None

try:
    if settings.telegram_bot_token and settings.telegram_bot_token != "your_telegram_bot_token_here":
        bot = Bot(token=settings.telegram_bot_token)
        dp = Dispatcher()
    else:
        print("WARNING: Telegram bot token not configured. Bot will not start.")
except Exception as e:
    print(f"WARNING: Failed to initialize Telegram bot: {e}. Bot will not start.")


# Регистрация обработчиков (только если бот инициализирован)
if dp:
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        """Обработчик команды /start"""
        await message.answer(
            "Привет! Отправь мне сообщение, и я проверю его через OpenAI."
        )


    @dp.message()
    async def handle_message(message: Message):
        """Обработчик всех сообщений"""
        try:
            # Получаем текст сообщения
            message_text = message.text or message.caption or ""
            
            if not message_text:
                await message.answer("Пожалуйста, отправьте текстовое сообщение.")
                return
            
            # Показываем пользователю, что сообщение обрабатывается
            processing_msg = await message.answer("⏳ Обрабатываю ваше сообщение...")
            
            # Проверяем сообщение через OpenAI
            result = await openai_service.check_message(message_text)
            
            # Сохраняем в базу данных
            await db.add_message(
                user_id=message.from_user.id,
                username=message.from_user.username,
                message_text=message_text,
                openai_response=json.dumps(result, ensure_ascii=False),
                status=result['status']
            )
            
            # Удаляем сообщение об обработке
            await processing_msg.delete()
            
            # Отвечаем пользователю в зависимости от статуса
            if result['status'] == 'ok':
                await message.answer("✅ Объява промодерирована, скоро будет на экране!")
            else:
                await message.answer("❌ Надо переписать")
                
        except Exception as e:
            # Обработка ошибок
            await message.answer(f"Произошла ошибка: {str(e)}")


async def start_bot():
    """Запуск бота"""
    # Инициализируем базу данных
    await db.init_db()
    
    # Запускаем бота только если он инициализирован
    if bot and dp:
        await dp.start_polling(bot)
    else:
        print("Telegram bot is not configured. Skipping bot startup.")
        # Бесконечный цикл, чтобы задача не завершилась
        while True:
            await asyncio.sleep(3600)  # Спим час


async def stop_bot():
    """Остановка бота"""
    if not bot or not dp:
        return
    try:
        await dp.stop_polling()
    except Exception:
        pass
    try:
        await bot.session.close()
    except Exception:
        pass

