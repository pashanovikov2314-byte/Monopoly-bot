from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("test"))
async def cmd_test(message: Message):
    await message.answer("✅ Тест пройден!")

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🚀 Бот запущен!")

def setup_test_handlers(dp):
    dp.include_router(router)
