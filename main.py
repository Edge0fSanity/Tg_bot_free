"""
TODO: 

Добавить в админ-панель кнопку (сбросить еду)

Добавить поздравление, если пользователь доел до лимита
"""



from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.input_file import InputFile
import asyncio
import aioschedule
from config import TOKEN
import datetime
import json
import parse_pfc
import os
import logging

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage) 
admins_id = [834981315, 779981400,1091119932]

class Form(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    goal = State()
    activity = State()


class FormNewWeight(StatesGroup):
    new_weight = State()


class FormFood(StatesGroup):
    food = State()


class AdminForm(StatesGroup):
    text = State()

def count_norm_of_calories(user_info):
    if user_info['activity'] == "Сидячий образ жизни, никаких упражнений":
        kfa = 1
    elif user_info['activity'] == "Легкая активность (небольшие упражнения 1-3 раза в неделю)":
        kfa = 1.3
    else:
        kfa = 1.5
    if user_info['goal'] == "Набор массы":
        kc = 1.1
    elif user_info['goal'] == "Оставаться в форме":
        kc = 1
    else:
        kc = 0.9
    if user_info['gender'] == 'Женский':
        if 18 <= int(user_info['age']) <= 30:
            user_info['norm_of_calories'] = round((0.062 * float(user_info['weight']) + 2.036) * 240 * kfa * kc)
        elif 30 < int(user_info['age']) <= 60:
            user_info['norm_of_calories'] = round((0.034 * float(user_info['weight']) + 3.538) * 240 * kfa * kc)
        else:
            user_info['norm_of_calories'] = round((0.038 * float(user_info['weight']) + 2.755) * 240 * kfa * kc)
    else:
        if 18 <= int(user_info['age']) <= 30:
            user_info['norm_of_calories'] = round((0.063 * float(user_info['weight']) + 2.896) * 240 * kfa * kc)
        elif 30 < int(user_info['age']) <= 60:
            user_info['norm_of_calories'] = round((0.048 * float(user_info['weight']) + 3.653) * 240 * kfa * kc)
        else:
            user_info['norm_of_calories'] = round((0.049 * float(user_info['weight']) + 2.459) * 240 * kfa * kc)
    return user_info


def count_norm_of_pfc(user_info):
    proteins = round(float(user_info['weight']) * 1.75)
    fats = round(float(user_info['weight']) * 1.15)
    carbohydrates = round(float(user_info['weight']) * 2)
    user_info['norm_of_pfc'] = {
        "proteins": proteins,
        "fats": fats,
        "carbohydrates": carbohydrates
    }
    return user_info

def main_menu_text(message):
    with open(f'users/user_info_{message.chat.id}.json', 'r', encoding='utf-8') as file:
        user_info = json.load(file)

    remaining_water = user_info['norm_of_water'] / 0.25
    water_emoji = "🥛" * int(remaining_water)

    text = f"""{f'Главное меню 🏠':^44}
За сегодня вы съели {user_info["calories"]}/{user_info["norm_of_calories"]} ккал
БЖУ: 
🍖 Белки: {user_info["pfc"]["proteins"]}/{user_info["norm_of_pfc"]["proteins"]}
🥑 Жиры: {user_info["pfc"]["fats"]}/{user_info["norm_of_pfc"]["fats"]}
🍚 Углеводы: {user_info["pfc"]["carbohydrates"]}/{user_info["norm_of_pfc"]["carbohydrates"]}

Вода: {water_emoji}"""

    return text

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Начать"))
    await message.answer(
        f"Появился вопрос ?\n"
        f"Можешь написать разработчику - @edge0fsanity\n"
        f"Может быть тебе помогут эти 2 примера ?", reply_markup=kb)
    await bot.send_photo(message.from_user.id, photo=InputFile("start_picture.jpg"))
    await bot.send_photo(message.from_user.id, photo=InputFile("meal_message_example.jpg"))


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Начать"))
    await message.answer(
        f"Привет, {message.from_user.first_name}, я бот, призванный помочь тебе создать и поддерживать "
        f"твоё тело "
        f"здоровым, "
        f"а в здоровом теле - здоровый дух", reply_markup=kb)
    await bot.send_photo(message.from_user.id, photo=InputFile("start_picture.jpg"))
    


@dp.message_handler(text="Начать")
async def start(message: types.Message):
    if os.path.exists(f"users/user_info_{message.chat.id}.json"):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Профиль")).row(
            types.KeyboardButton('Дневник питания')).row(types.KeyboardButton('Напоминание'))
        
        text = main_menu_text(message)
        await message.answer(text, reply_markup=kb)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Заполнить анкету"))
        await message.answer("У меня нет ваших данных. Пожалуйста, заполните анкету", reply_markup=kb)


@dp.message_handler(text="Заполнить анкету")
async def form(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Мужской"),
                                                            types.KeyboardButton(text="Женский"))
    await message.answer("Какой у вас пол?", reply_markup=kb)
    await Form.next()


@dp.message_handler(state=Form.gender)
async def form(message: types.Message, state: FSMContext):
    if message.text not in ["Мужской", "Женский"]:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов")
        return
    async with state.proxy() as data:
        data['gender'] = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Заполнить анкету заново"))
    await message.answer("Сколько вам лет?", reply_markup=kb)
    await Form.next()


@dp.message_handler(state=Form.age)
async def form(message: types.Message, state: FSMContext):
    if message.text == 'Заполнить анкету заново':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Мужской"),
                                                                types.KeyboardButton(text="Женский"))
        await message.answer("Какой у вас пол?", reply_markup=kb)
        await state.finish()
        await Form.gender.set()
        return
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число")
        return

    async with state.proxy() as data:
        data['age'] = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Заполнить анкету заново"))
    await message.answer("Сколько вы весите (в кг)?", reply_markup=kb)
    await Form.next()


@dp.message_handler(state=Form.weight)
async def form(message: types.Message, state: FSMContext):
    if message.text == 'Заполнить анкету заново':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Мужской"),
                                                                types.KeyboardButton(text="Женский"))
        await message.answer("Какой у вас пол?", reply_markup=kb)
        await state.finish()
        await Form.gender.set()
        return
    # check that message.text is int or float
    if not message.text.replace('.', '', 1).replace(',', '', 1).isdigit():
        await message.answer("Пожалуйста, введите число")
        return

    async with state.proxy() as data:
        data['weight'] = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Набор массы")).row(
        types.KeyboardButton(text="Оставаться в форме")).row(
        types.KeyboardButton(text="Снижение массы"),types.KeyboardButton('Заполнить анкету заново'))
    await message.answer("Какая у вас цель?", reply_markup=kb)
    await Form.next()


@dp.message_handler(state=Form.goal)
async def form(message: types.Message, state: FSMContext):
    if message.text == 'Заполнить анкету заново':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Мужской"),
                                                                types.KeyboardButton(text="Женский"))
        await message.answer("Какой у вас пол?", reply_markup=kb)
        await state.finish()
        await Form.gender.set()
        return
    if message.text not in ["Набор массы", "Оставаться в форме", "Снижение массы"]:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов")
        return
    async with state.proxy() as data:
        data['goal'] = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(
        types.KeyboardButton(text="Сидячий образ жизни, никаких упражнений")).row(
        types.KeyboardButton(text='Легкая активность (небольшие '
                                    'упражнения 1-3 раза в неделю)')).row(
        types.KeyboardButton(text='Высокая активность ('
                                    'тренируюсь более 4-х раз в '
                                    'неделю)')).row(types.KeyboardButton('Заполнить анкету заново'))
    await message.answer("Опишите ваш уровень физической активности.", reply_markup=kb)
    await Form.next()


@dp.message_handler(state=Form.activity)
async def form(message: types.Message, state: FSMContext):
    if message.text == 'Заполнить анкету заново':
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Мужской"),
                                                                types.KeyboardButton(text="Женский"))
        await message.answer("Какой у вас пол?", reply_markup=kb)
        await state.finish()
        await Form.gender.set()
        return
    if message.text not in ["Сидячий образ жизни, никаких упражнений", "Легкая активность "
                            "(небольшие упражнения 1-3 раза в неделю)",
                            "Высокая активность (тренируюсь более 4-х раз в неделю)"]:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов")
        return
    async with state.proxy() as data:
        data['activity'] = message.text
    # count norm of water, round to nearest number that divisible by 0.250
    norm_of_water = float(data['weight']) * 0.03
    norm_of_water = round(norm_of_water * 4) / 4
    user_info = {
        "gender": data['gender'],
        "age": data['age'],
        "weight": data['weight'],
        "goal": data['goal'],
        "activity": data['activity'],
        "water_reminder": "off",
        "norm_of_water": norm_of_water,
        "date_for_water": datetime.datetime.now().strftime("%Y-%m-%d"),
        "date_for_calories_and_pfc": datetime.datetime.now().strftime("%Y-%m-%d"),
        "calories": 0,
        "pfc": {
            "proteins": 0,
            "fats": 0,
            "carbohydrates": 0
        }
    }
    user_info = count_norm_of_calories(user_info)
    user_info = count_norm_of_pfc(user_info)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Главное меню"))
    with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)
    await state.finish()
    await message.answer("Отлично, данные добавлены !", reply_markup=kb)


@dp.message_handler(text="Главное меню")
async def main_menu(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Профиль")).row(
        types.KeyboardButton('Дневник питания')).row(types.KeyboardButton('Напоминание'))

    text =  main_menu_text(message)
    await message.answer(text, reply_markup=kb)


@dp.message_handler(text="Назад")
async def main_menu(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Профиль")).row(
        types.KeyboardButton('Дневник питания')).row(types.KeyboardButton('Напоминание'))
    
    text = main_menu_text(message)
    await message.answer(text, reply_markup=kb)


@dp.message_handler(text="Профиль")
async def profile(message: types.Message):
    try:
        with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
            user_info = json.load(file)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton('Изменить профиль')).row(
            types.KeyboardButton('Записать изменение веса')).row(types.KeyboardButton('Назад'))
        await message.answer(f"Ваш профиль:\n\n"
                            f"Пол: {user_info['gender']}\n"
                            f"Возраст: {user_info['age']}\n"
                            f"Вес: {user_info['weight']}\n"
                            f"Цель: {user_info['goal']}\n"
                            f"Активность: {user_info['activity']}", reply_markup=kb)
    except FileNotFoundError:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Заполнить анкету"))
        await message.answer("У вас нет профиля. Пожалуйста, заполните анкету", reply_markup=kb)


@dp.message_handler(text="Изменить профиль")
async def edit_profile(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Заполнить анкету")).row(
        types.KeyboardButton('Назад'))
    await message.answer("Чтобы изменить профиль, заполните заново анкету", reply_markup=kb)


@dp.message_handler(text="Записать изменение веса") # Функция, для которой нет кнопки
async def weight_change(message: types.Message):
    await message.answer("Введите ваш новый вес", reply_markup=types.ReplyKeyboardRemove())
    await FormNewWeight.new_weight.set()


@dp.message_handler(state=FormNewWeight.new_weight)     # Функция, которая никогда не вызывается
async def weight_change(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).replace(',', '', 1).isdigit():
        await message.answer("Пожалуйста, введите число")
        return
    async with state.proxy() as data:
        data['new_weight'] = message.text
    with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    user_info['weight'] = data['new_weight']
    user_info = count_norm_of_calories(user_info)
    user_info = count_norm_of_pfc(user_info)
    with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)
    await state.finish()
    await message.answer("Ваш вес успешно изменен", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(
        types.KeyboardButton(text="Назад"))
                        )


@dp.message_handler(text="Дневник питания")
async def food_diary(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Выпить стакан")).row(
        types.KeyboardButton('Записать приём пищи')).row(types.KeyboardButton('Назад'))
    await message.answer("Дневник питания", reply_markup=kb)


@dp.message_handler(text="Напоминание")
async def reminder(message: types.Message):
    with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    if user_info['water_reminder'] == "off":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Включить")).row(
            types.KeyboardButton('Назад'))
        await message.answer("Напоминания о воды выключены", reply_markup=kb)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Выключить")).row(
            types.KeyboardButton('Назад'))
        await message.answer("Напоминания о воды включены", reply_markup=kb)


@dp.message_handler(text="Включить")
async def reminder_on(message: types.Message):
    with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    user_info['water_reminder'] = "on"
    with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Выключить")).row(
        types.KeyboardButton('Назад'))
    await message.answer("Напоминания о воды включены", reply_markup=kb)


@dp.message_handler(text="Выключить")
async def reminder_off(message: types.Message):
    with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    user_info['water_reminder'] = "off"
    with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
        json.dump(user_info, file, ensure_ascii=False, indent=4)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Включить")).row(
        types.KeyboardButton('Назад'))
    await message.answer("Напоминания о воды выключены", reply_markup=kb)


@dp.message_handler(text="Выпить стакан")
async def drink_glass(message: types.Message):
    with open(f"users/user_info_{message.chat.id}.json", 'r', encoding='utf-8') as file:
        user_info = json.load(file)
    # if now time - water reminder time >= 24 hours, then update date for water and norm of water
    if (datetime.datetime.now() - datetime.datetime.strptime(user_info['date_for_water'], "%Y-%m-%d")).days >= 1:
        user_info['date_for_water'] = datetime.datetime.now().strftime("%Y-%m-%d")
        norm_of_water = float(user_info['weight']) * 0.03
        norm_of_water = round(norm_of_water * 4) / 4
        user_info['norm_of_water'] = norm_of_water - 0.25
        with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
            json.dump(user_info, file, ensure_ascii=False, indent=4)
    else:
        user_info['norm_of_water'] -= 0.25
        with open(f"users/user_info_{message.chat.id}.json", 'w', encoding='utf-8') as file:
            json.dump(user_info, file, ensure_ascii=False, indent=4)
    remaining = user_info['norm_of_water'] / 0.25
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Дневник питания"))
    await message.answer(f"Вы выпили стакан воды. Вам осталось выпить {user_info['norm_of_water']}л воды или "
                        f" {remaining} стаканов на сегодня.",
                        reply_markup=kb)


@dp.message_handler(text="Записать приём пищи")
async def food_entry(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Назад"))
    await message.answer("Запишите, что вы съели", reply_markup=kb)
    await FormFood.food.set()


@dp.message_handler(state=FormFood.food)
async def food_entry(message: types.Message, state: FSMContext):
    mes_del = await message.answer("Подождите, идет обработка запроса...")
    mes, result = parse_pfc.parse_pfc(message.text)
    mes += 'Добавить в съеденное за сегодня?'

    with open(f'users/user_info_{message.chat.id}.json', 'r+', encoding='utf-8') as file:
        user_info = json.load(file)
        user_info['intermediate_result'] = result
        file.seek(0)
        json.dump(user_info, file, ensure_ascii=False, indent=4)
        file.truncate()
        
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Да")).row(
        types.KeyboardButton('Нет'))
    await bot.delete_message(chat_id=message.chat.id, message_id=mes_del.message_id)
    await message.answer(mes, reply_markup=kb)
    await state.finish()


@dp.message_handler(text="Да")
async def add_to_food_diary(message: types.Message):
    with open(f'users/user_info_{message.chat.id}.json', 'r+', encoding='utf-8') as file:
        user_info = json.load(file)

        # Rewrite file with a new data
        user_info['calories'] += user_info['intermediate_result']['sum_calories']
        user_info['pfc']['proteins'] += user_info['intermediate_result']['sum_protein']
        user_info['pfc']['fats'] += user_info['intermediate_result']['sum_fat']
        user_info['pfc']['carbohydrates'] += user_info['intermediate_result']['sum_carbohydrate']

        file.seek(0)
        json.dump(user_info, file, ensure_ascii=False, indent=4)
        file.truncate()
        
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Дневник питания"))
    await message.answer(f'За сегодня вы съели {user_info["calories"]}/{user_info["norm_of_calories"]} ккал\nБЖУ: \n'
                        f'{user_info["pfc"]["proteins"]}/{user_info["norm_of_pfc"]["proteins"]}\n'
                        f'{user_info["pfc"]["fats"]}/{user_info["norm_of_pfc"]["fats"]}\n'
                        f'{user_info["pfc"]["carbohydrates"]}/{user_info["norm_of_pfc"]["carbohydrates"]}',
                        reply_markup=kb)


@dp.message_handler(text="Нет")
async def add_to_food_diary(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Выпить стакан")).row(
        types.KeyboardButton('Записать приём пищи')).row(types.KeyboardButton('Назад'))
    await message.answer("Запись не добавлена", reply_markup=kb)

@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if message.chat.id in admins_id:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton(text="Сделать рассылку")).row('Назад')
        await message.answer("Админ панель", reply_markup=kb)
    else:
        await message.answer("У вас нет прав администратора")

@dp.message_handler(text="Сделать рассылку")
async def mailing(message: types.Message):
    if message.chat.id in admins_id:
        await message.answer("Введите текст рассылки",reply_markup=types.ReplyKeyboardRemove())
        await AdminForm.text.set()
    else:
        await message.answer("У вас нет прав администратора")


@dp.message_handler(state=AdminForm.text, content_types=['photo'])
async def mailing(message: types.Message, state: FSMContext):
    for user in os.listdir('users'):
        user = user.split('_')[-1].split('.')[0]
        if message.photo:
            await bot.send_photo(user, photo=message.photo[-1].file_id, caption=message.caption)
        else:
            await bot.send_message(user, message.text)
    logging.info("[INFO] Admin has sent a message")
    await state.finish()
    await message.answer("Рассылка завершена",reply_markup=types.ReplyKeyboardMarkup
    (resize_keyboard=True).row(types.KeyboardButton(text="Назад")))


async def send_water_reminders():
        now = datetime.datetime.now()
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

async def reset_calories_and_pfc():
    
    for user in os.listdir('users'):
        now = datetime.datetime.now()
        with open(f'users/{user}', 'r+', encoding='utf-8') as file:
            user_info = json.load(file)
            last_reset_date = datetime.datetime.strptime(user_info['date_for_calories_and_pfc'], "%Y-%m-%d").date()
            if last_reset_date < now.date():
                user_info['calories'] = 0
                user_info['pfc']['proteins'] = 0
                user_info['pfc']['fats'] = 0
                user_info['pfc']['carbohydrates'] = 0
                user_info['date_for_calories_and_pfc'] = now.strftime("%Y-%m-%d")
                file.seek(0)
                json.dump(user_info, file, ensure_ascii=False, indent=4)
                file.truncate()

async def scheduler():
    aioschedule.every().day.at("03:15").do(reset_calories_and_pfc)
    for hour in [10, 14, 18]:
        aioschedule.every().day.at(f"{hour}:00").do(send_water_reminders)
    aioschedule.every()
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

