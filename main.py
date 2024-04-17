import asyncio
import logging
import sys
import os
import warnings
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import Router
from config import TOKEN
warnings.filterwarnings("ignore")

dp = Dispatcher()
router = Router()

def include_handlers(dp: Dispatcher):
    handlers_dir = 'handlers'
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py'):
            module_name = filename[:-3]
            try:
                handler_module = __import__(f'{handlers_dir}.{module_name}', fromlist=['router'])
                router = getattr(handler_module, 'router', None)  # Get the 'router' object from the module
                if router:
                    dp.include_router(router)
            except Exception as e:
                pass


async def main() -> None:
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    include_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


