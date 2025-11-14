import os
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, URLInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from flask import current_app
from datetime import datetime

load_dotenv('secrets/.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

router = Router()

# Путь к файлу с приветственным сообщением
WELCOME_MESSAGE_FILE = 'data/welcome_message.txt'
DEFAULT_WELCOME = "приветсвенное сообщение"
WELCOME_VIDEO_URL = "https://t.me/adsfjpladijflasjhdf/2"

def get_welcome_message():
    try:
        if os.path.exists(WELCOME_MESSAGE_FILE):
            with open(WELCOME_MESSAGE_FILE, 'r', encoding='utf-8') as file:
                return file.read()
        return DEFAULT_WELCOME
    except Exception as e:
        logger.error(f"Ошибка при чтении приветственного сообщения: {e}")
        return DEFAULT_WELCOME


def get_welcome_image_url():
    try:
        image_file_path = 'data/welcome_image_url.txt'
        if os.path.exists(image_file_path):
            with open(image_file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении URL изображения приветственного сообщения: {e}")
        return None

def get_welcome_video_url():
    """Возвращает URL видео для приветственного сообщения"""
    return WELCOME_VIDEO_URL if WELCOME_VIDEO_URL else None

@router.message(Command("start"))
async def cmd_start(message: Message):
    try:
        # Сохраняем информацию о пользователе
        user_data = {
            'chat_id': str(message.chat.id),
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        os.makedirs('data/users', exist_ok=True)
        
        user_file = f'data/users/{message.chat.id}.json'
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False)
        
        users_list_file = 'data/users/users_list.txt'
        with open(users_list_file, 'a', encoding='utf-8') as f:
            f.write(f"{message.chat.id}\n")
        
        # Получаем приветственное сообщение, изображение и видео
        welcome_message = get_welcome_message()
        welcome_image_url = get_welcome_image_url()
        welcome_video_url = get_welcome_video_url()

        # Создаем клавиатуру с кнопкой веб-приложения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🛍️ Открыть магазин",
                web_app=WebAppInfo(url="https://smarketirk38.ru/")
            )]
        ])

        # Отправляем сообщение с изображением и клавиатурой, если оно есть
        if welcome_image_url:
            await message.answer_photo(
                photo=welcome_image_url,
                caption=welcome_message,
                reply_markup=keyboard
            )
        else:
            await message.answer(
                welcome_message,
                reply_markup=keyboard
            )

        # Отправляем видео, если оно указано
        if welcome_video_url:
            try:
                await message.answer_video(video=welcome_video_url)
                await message.answer("⬆️ видео-инструкция по оформлению заказа через приложение")
            except Exception as video_error:
                logger.error(f"Ошибка при отправке видео: {video_error}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")

_bot = None
_dp = None

async def create_bot():
    global _bot
    if _bot is not None:
        return _bot
        
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Не найден токен бота. Убедитесь, что TELEGRAM_BOT_TOKEN установлен в secrets/.env файле")
        return None
    
    _bot = Bot(token=bot_token)
    return _bot

def get_dispatcher():
    global _dp
    if _dp is None:
        _dp = Dispatcher(storage=MemoryStorage())
        _dp.include_router(router)
    return _dp

async def start_polling():
    try:
        # Загрузим приветственное сообщение перед запуском бота
        welcome_message = get_welcome_message()
        
        bot = await create_bot()
        if bot:
            dp = get_dispatcher()
            logger.info("Запуск бота в режиме поллинга")
            
            # Изменяем эту строку, чтобы отключить обработку сигналов
            await dp.start_polling(bot, skip_updates=True, handle_signals=False)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

async def send_message(chat_id, text, image_url=None):
    bot = await create_bot()
    if not bot:
        return
    
    if image_url:
        await bot.send_photo(chat_id=chat_id, photo=image_url, caption=text)
    else:
        await bot.send_message(chat_id=chat_id, text=text)
        
def init_bot():
    logger.info("Инициализация бота")
    return get_dispatcher()

# Добавьте новую функцию для отправки медиа-группы с текстом
async def send_media_group(chat_id, text, image_urls):
    """
    Отправляет группу изображений с текстом.
    Текст будет добавлен к первому изображению как подпись.
    """
    try:
        # Получаем экземпляр бота
        bot = await create_bot()
        if not bot:
            return False
            
        media = []
        
        # Первое изображение с текстом
        media.append(InputMediaPhoto(
            media=image_urls[0],
            caption=text
        ))
        
        # Остальные изображения без текста
        for url in image_urls[1:]:
            media.append(InputMediaPhoto(media=url))
        
        # Отправляем группу медиа
        await bot.send_media_group(chat_id=chat_id, media=media)
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке медиагруппы пользователю {chat_id}: {e}")
        return False

# Добавьте эту функцию в bot_handler.py для получения токена бота
def get_token():
    return os.getenv("TELEGRAM_BOT_TOKEN")

# Добавьте эту функцию
async def register_webhook(app_url, path='/webhook'):
    """
    Регистрирует вебхук для бота
    """
    try:
        bot = await create_bot()
        if not bot:
            return False
            
        webhook_url = f"{app_url}{path}"
        logger.info(f"Регистрация вебхука: {webhook_url}")
        
        # Удаляем предыдущий вебхук, если он был
        await bot.delete_webhook()
        
        # Устанавливаем новый вебхук
        await bot.set_webhook(url=webhook_url)
        return True
    except Exception as e:
        logger.error(f"Ошибка при регистрации вебхука: {e}")
        return False

# Функция для обработки вебхука
async def process_webhook(request):
    """
    Обрабатывает входящий запрос вебхука
    """
    try:
        bot = await create_bot()
        if not bot:
            return False
            
        dp = get_dispatcher()
        
        # Получаем данные запроса
        data = await request.json()
        
        # Создаем объект обновления
        from aiogram.types import Update
        update = Update.model_validate(data)
        
        # Обрабатываем обновление
        await dp.feed_update(bot, update)
        return True
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return False
