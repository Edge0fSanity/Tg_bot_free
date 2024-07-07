import json
from config import TOKEN
import datetime
import asyncio
from aiogram import Bot, Dispatcher, types
import os

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

async def send_water_reminders():
    while True:
        now = datetime.datetime.now()
        if now.time().hour in [10, 14, 18]:
            for user in os.listdir('users'):
                with open(f'users/{user}', 'r', encoding='utf-8') as file:
                    user_info = json.load(file)
                if user_info.get('water_reminder') == 'on' and user_info['norm_of_water'] > 0:
                    #last_reminder_date = datetime.datetime.strptime(user_info['date_for_water'], "%Y-%m-%d").date()
                    #if last_reminder_date < now.date():
                    chat_id = user.split('_')[-1].split('.')[0]
                    await bot.send_message(chat_id, 'Не забудьте выпить воды!')
                    user_info['date_for_water'] = now.strftime("%Y-%m-%d")
                    with open(f'users/{user}', 'w', encoding='utf-8') as file:
                        json.dump(user_info, file, ensure_ascii=False, indent=4)
            await asyncio.sleep(3600)  # спим один час

        await asyncio.sleep(60)  # проверяем каждую минуту

async def reset_calories_and_pfc():
    while True:
        now = datetime.datetime.now()
        if now.time().hour == 0:
            for user in os.listdir('users'):
                with open(f'users/{user}', 'r+', encoding='utf-8') as file:
                    user_info = json.load(file)
                    last_reset_date = datetime.datetime.strptime(user_info['date_for_calories_and_pfc'], "%Y-%m-%d").date()
                    if last_reset_date < now.date():
                        user_info['calories'] = 0
                        user_info['pfc']['proteins'] = 0
                        user_info['pfc']['fats'] = 0
                        user_info['pfc']['carbohydrates'] = 0
                        user_info['date_for_calories_and_pfc'] = now.strftime("%Y-%m-%d")
                        json.dump(user_info, file, ensure_ascii=False, indent=4)
                        
            await asyncio.sleep(3600)  # спим один час

        await asyncio.sleep(60)  # проверяем каждую минуту

async def main():
    await asyncio.gather(
        send_water_reminders(),
        reset_calories_and_pfc()
    )

if __name__ == "__main__":
    asyncio.run(main())