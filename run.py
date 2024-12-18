from fastapi import FastAPI, Request

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN
from handlers import ROUTER
CHANNEL_ID = -1002343780142
app = FastAPI()

BOT = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
DP = Dispatcher()
scheduler = AsyncIOScheduler()

async def check_subscription(user_id: int) -> bool:
    try:
        member = await BOT.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status
    except Exception:
        return False

async def main():
    ROUTER.bot = BOT
    ROUTER.scheduler = scheduler
    DP.include_router(ROUTER)
    ROUTER.scheduler.start()  # Запуск планировщика
    await DP.start_polling(BOT)


@app.post("/check_subscription")
async def check_subscription_route(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    is_subscribed = await check_subscription(int(user_id))
    return {"is_subscribed": is_subscribed}

if __name__ == "__main__":
    asyncio.run(main())