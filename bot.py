import logging
import asyncio
import schedule
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from config import *
from load_data import *
import os


path = sorted([(os.path.getmtime(DATA_PATH + '/' + elem), DATA_PATH + '/' + elem)
               for elem in os.listdir(DATA_PATH)])[-1][-1]
# Логирование
logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
# инициализация переменных для работы с ботом
users_code = {}
users_sizes = {}
users_colors = {}
# выгрузка датасета
sizes, stocks, prices, colors, names, code = load_data(path)
# Включаем логирование
dp.middleware.setup(LoggingMiddleware())


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await welcome(message.chat.id)


async def welcome(chat_id: int):
    await bot.send_message(chat_id, "Здравствуйте! Вы обратились к чат-боту Yemag, который поможет проверить"
                                    " наличие размеров в магазине или узнать стоимость. Обратите внимание, что наличие"
                                    " вещей в магазинах может меняться быстрее, чем обновляется информация в системе.")
    await get_code(chat_id)


# Функция для отправки сообщения "Напишите артикул товара"
async def get_code(chat_id: int):
    keyboard = InlineKeyboardMarkup()
    btn_code = InlineKeyboardButton('Где найти артикул', callback_data='btn_code')
    keyboard.add(btn_code)
    await bot.send_message(chat_id, "Напишите артикул товара", reply_markup=keyboard)


async def get_size(chat_id: int):
    curr_code = users_code[chat_id]
    keyboard = InlineKeyboardMarkup()
    if all([elem.upper() in SIZES.keys() for elem in sizes[curr_code]]):
        curr_sizes = sorted(sizes[curr_code], key=lambda x: SIZES[x])
    else:
        curr_sizes = sorted(sizes[curr_code])
    d = []
    for elem in stocks.keys():
        for size in curr_sizes:
            if (curr_code in stocks[elem] and size in stocks[elem][curr_code]
                    and stocks[elem][curr_code][size] != 0):
                d.append(size)
    btns = []
    for i in range(len(curr_sizes)):
        s = str(curr_sizes[i])
        if s in d:
            s = s + ' ✓'
        btns.append(InlineKeyboardButton(s, callback_data=f"btn_size_{i}"))
    keyboard.add(*btns)
    btn1 = InlineKeyboardButton("Нет нужного размера", callback_data=f"btn_not_size")
    btn2 = InlineKeyboardButton("Показать цену", callback_data=f"btn_get_price")
    btn3 = InlineKeyboardButton("Вернуться в начало", callback_data=f"btn_to_start")
    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)
    await bot.send_message(chat_id, f"Выберите нужный размер для товара {names[curr_code]}",
                           reply_markup=keyboard)


async def get_color(chat_id: int):
    curr_code = users_code[chat_id]
    curr_size = users_sizes[chat_id]
    curr_colors = colors[curr_code][curr_size]
    keyboard = InlineKeyboardMarkup()
    btns = []
    for i in range(len(curr_colors)):
        s = str(curr_colors[i])
        btns.append(InlineKeyboardButton(s, callback_data=f"btn_color_{i}"))
    keyboard.add(*btns)
    btn1 = InlineKeyboardButton("Нет нужного цвета", callback_data=f"btn_not_color")
    btn2 = InlineKeyboardButton("Выбрать другой размер", callback_data=f"btn_get_size")
    btn3 = InlineKeyboardButton("Показать цену", callback_data=f"btn_get_price")
    btn4 = InlineKeyboardButton("Вернуться в начало", callback_data=f"btn_to_start")
    keyboard.row(btn1)
    keyboard.row(btn2)
    keyboard.row(btn3)
    keyboard.row(btn4)
    await bot.send_message(chat_id, f"Выберите нужный цвет для товара {names[curr_code]} размера {curr_size}",
                           reply_markup=keyboard)


async def send_stock(chat_id: int):
    global stocks
    curr_code = users_code[chat_id]
    curr_size = users_sizes[chat_id]
    curr_color = users_colors[chat_id]
    keyboard = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("Выбрать другой артикул", callback_data=f"btn_another_code")
    btn2 = InlineKeyboardButton("Выбрать другой размер", callback_data=f"btn_get_size")
    btn3 = InlineKeyboardButton("Вернуться в начало", callback_data=f"btn_to_start")
    keyboard.add(btn1)
    keyboard.add(btn2)
    keyboard.add(btn3)
    d = {}
    for elem in stocks.keys():
        if (curr_code in stocks[elem] and curr_size in stocks[elem][curr_code]
                and stocks[elem][curr_code][curr_size] != 0):
            d[elem] = stocks[elem][curr_code][curr_size]
    s = '\n'.join([f'{i + 1}) {list(d.keys())[i]} в количестве {d[list(d.keys())[i]]}'
                   for i in range(len(d.keys())) if d[list(d.keys())[i]]])
    if s:
        await bot.send_message(chat_id, f"Товар {names[curr_code]} в размере {curr_size}, цвет {curr_color} "
                                        f"найден в:\n {s}\nЦена {prices[curr_code]} ₽", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, f"Товар {names[curr_code]}"
                                        f" в размере {curr_size}, цвет {curr_color} не найден ни на одном из "
                                        f"складов", reply_markup=keyboard)


async def get_price(chat_id: int):
    global prices
    curr_code = users_code[chat_id]
    keyboard = InlineKeyboardMarkup()
    await bot.send_message(chat_id, f"Цена для товара {names[curr_code]}"
                                    f" - {prices[curr_code]} ₽", reply_markup=keyboard)
    await get_size(chat_id)


async def not_size(chat_id: int):
    global prices
    keyboard = InlineKeyboardMarkup()
    await bot.send_message(chat_id, f"Размерная сетка выбранного артикула выведена на кнопках. Пожалуйста,"
                                    f" выберите размер из предложенных.", reply_markup=keyboard)
    await get_size(chat_id)


async def not_color(chat_id: int):
    global prices
    keyboard = InlineKeyboardMarkup()
    await bot.send_message(chat_id, f"Цвета представленны на кнопках. Пожалуйста,"
                                    f" выберите цвет из предложенных.", reply_markup=keyboard)
    await get_color(chat_id)


# Обработчик текстовых сообщений
@dp.message_handler()
async def message_hand(message: types.Message):
    global users_code
    # обработка ввода артикула
    users_code[message.chat.id] = prepare_code(message.text)
    curr_code = users_code[message.chat.id]
    if curr_code not in sizes.keys():
        await message.answer(f"Артикул {curr_code} написан неправильно или не найден в базе данных")
        await get_code(message.chat.id)
    else:
        await get_size(message.chat.id)


# обработчик нажатия на кнопку
@dp.callback_query_handler(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery):
    global users_sizes, users_colors
    code = callback_query.data
    if code == 'btn_code':
        await bot.send_message(callback_query.from_user.id, 'Текст и картинка, содержащие информацию о том,'
                                                            ' как выглядит и где расположен артикул')
        await get_code(callback_query.from_user.id)
    elif code == 'btn_not_size':
        await not_size(callback_query.from_user.id)
    elif code == 'btn_get_size':
        await get_size(callback_query.from_user.id)
    elif code == "btn_another_code":
        await get_code(callback_query.from_user.id)
    elif code == 'btn_get_price':
        await get_price(callback_query.from_user.id)
    elif code == 'btn_to_start':
        await get_code(callback_query.from_user.id)
    elif code == 'btn_not_color':
        await not_color(callback_query.from_user.id)
    elif "btn_size" in code:
        curr_code = users_code[callback_query.from_user.id]
        if all([elem.upper() in SIZES.keys() for elem in sizes[curr_code]]):
            curr_sizes = sorted(sizes[curr_code], key=lambda x: SIZES[x])
        else:
            curr_sizes = sorted(sizes[curr_code])
        users_sizes[callback_query.from_user.id] = curr_sizes[int(code[9:])]
        if colors[curr_code][users_sizes[callback_query.from_user.id]]:
            await get_color(callback_query.from_user.id)
        else:
            await send_stock(callback_query.from_user.id)
    elif "btn_color" in code:
        curr_code = users_code[callback_query.from_user.id]
        curr_size = users_sizes[callback_query.from_user.id]
        users_colors[callback_query.from_user.id] = colors[curr_code][curr_size][int(code[10:])]
        await send_stock(callback_query.from_user.id)


async def load_db():
    global sizes, stocks, prices, colors, names
    a, b, c, d, e, code = load_data(path)
    if code == 0:
        sizes, stocks, prices, colors, names = a, b, c, d, e
        for ID in ADMINS:
            await bot.send_message(ID, "Данные успешно обновлены")
    elif code == 1:
        for ID in ADMINS:
            await bot.send_message(ID, "База данных не найдена")


# Обернем функцию scheduled_job для совместимости с schedule
def job_wrapper():
    asyncio.create_task(load_db())


# Запланировать выполнение функции job каждую секунду
schedule.every().day.at("03:00").do(job_wrapper)


# Функция для запуска schedule в асинхронном режиме
async def scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


# Основная функция
async def main():
    # Запуск расписания
    asyncio.create_task(scheduler())
    # Запуск Telegram бота
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
