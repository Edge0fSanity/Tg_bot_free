import json
from config import TOKEN
import datetime
import asyncio
from aiogram import Bot, Dispatcher, types, executor
bot = Bot(token=TOKEN,parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
# get files from the folder with os
import os
async def main():
    while True:
        if datetime.datetime.now().time().hour in [10, 14, 18] and datetime.datetime.now().time().minute == 0:
            for user in os.listdir('users'):
                with open(f'users/{user}') as file:
                    user_info = json.load(file)
                if user_info['water_reminder'] == 'on':
                    if user_info['norm_of_water']>0:
                        chat_id = user.split('_')[-1].split('.')[0]
                        await bot.send_message(chat_id, f'Не забудьте выпить воды!')

        await asyncio.sleep(60)
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
