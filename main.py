import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from settings import API_TOKEN, NEED_SAVE_LOGS_TO_FILE

import os
if NEED_SAVE_LOGS_TO_FILE:
    logging.basicConfig(filename="pizzabot.log",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG)

if "https_proxy" in os.environ:
    proxy_url = os.environ["https_proxy"]
    bot = Bot(token=API_TOKEN, proxy=proxy_url)
else:
    bot = Bot(token=API_TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

class StateMachine(StatesGroup):
    questions_started = State()

questions = [
    {
        "text": "1. Какой стандарт мобильной связи является аналоговым",
        "answers": ["2G", "1G", "3G", "4G"]
    },
    {
        "text": '2. Кто придумал термин "Искусственный интеллект"',
        "answers": ["Алан Тьюринг", "Марвин Миски", "Джон Маккарти", "Герберт Саймон"]
    },
    {
        "text": "3. Как называется процедура проверки подлинности",
        "answers": ["идентификация", "дактилоскопия", "шифрование", "аутентификация"]
    },
    {
        "text": "4. Что такое майнинг",
        "answers": ["подтверждение блоков в цепочке транзакций", "добыча криптовалюты", "подсчет значения хеш-функции", "добыча полезных ископаемых"]
    },
]

def get_question_text_by_id(id):
    return questions[id].get("text")

def generate_answers_markup_by_id(id):
    markup = InlineKeyboardMarkup()
    for i in range(len(questions[id].get("answers"))):
        answer_text = questions[id].get("answers")[i]
        markup.add(InlineKeyboardButton(answer_text, callback_data=f"answer_{i}"))
    return markup

@dp.message_handler(commands=['start', 'help'], state="*")
async def send_welcome(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add( # клавиатура будет удалятьс с экрана
        KeyboardButton("Начать"),
    )

    await message.reply("Здравствуйте! Я предлагаю вам ответить на тестовые вопросы!", reply_markup=markup)

    logging.info(f"{message.from_user.username}: {message.text}")

@dp.message_handler(text='Начать', state="*")
async def start_questions(message: types.Message, state: FSMContext):
    await StateMachine.questions_started.set()

    async with state.proxy() as data:
        data["current_question"] = 0
        data["answers"] = []

    await message.answer(get_question_text_by_id(0), reply_markup=generate_answers_markup_by_id(0))

@dp.callback_query_handler(text_startswith="answer_", state=StateMachine.questions_started)
async def but_pressed(call: types.CallbackQuery, state: FSMContext):
    answer = int(call.data.split('_')[1])

    await call.message.edit_reply_markup(InlineKeyboardMarkup())

    async with state.proxy() as data:
        data["current_question"] += 1
        current_question = data["current_question"]
        data["answers"].append(answer)

    if current_question < len(questions):
        await call.message.edit_text(get_question_text_by_id(current_question), reply_markup=generate_answers_markup_by_id(current_question))
    else:
        async with state.proxy() as data:
            answers = data["answers"]
        print(f"User {call.from_user.username} done questions.\nAnswers is {answers}")
        await state.finish()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(
            KeyboardButton("Начать"),
        )
        if data["answers"] == [1,2,3,0]:
            await call.message.edit_text("Вы успешно прошли тест!", reply_markup=InlineKeyboardMarkup())
        else:
            await call.message.answer("Вы ответили не на все вопросы, пройдите тест еще раз!", reply_markup=markup)

def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()