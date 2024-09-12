import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import F

# token
from telegram_token import BOT_TOKEN
# quiz data
from quiz_data import quiz_export
# database module
from database_creation import create_table
# primary functions
from primary_functions import (new_quiz, get_question, update_quiz_index,
                               update_current_score, get_quiz_index, get_current_score,
                               get_highscore, update_highscore)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()

# Зададим имя базы данных
db_name = 'quiz_bot.db'

# Структура опроса
quiz_data = quiz_export


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Получение текущего вопроса из словаря состояний пользователя
    greetings_string = f"Добро пожаловать в квиз!"
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer(greetings_string, reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /quiz
@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message, quiz_data, db_name)


# Хэндлер, получающий данные от нажатия кнопок ответов
@dp.callback_query(lambda c_str: c_str.data.startswith('answer'))
async def handle_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    # Это ID пользователя (например, меня)
    user_id = callback.from_user.id
    # Разбираем callback на несколько составляющих его частей, отбрасываем answer так как он больше не нужен
    callback_data_list = callback.data.split(':')[1:]

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id, db_name)
    # Чтобы избежать "may be referenced before assignment", будем каждый раз запрашивать счёт вне первого if'а
    current_score = await get_current_score(user_id, db_name)

    # Проверка, верен ли вопрос
    if callback_data_list[0] == "1":
        # Обновление текущего счёта
        current_score += 1
        await update_current_score(user_id, current_score, db_name)
        await callback.message.answer(f"Верно! {callback_data_list[1]} – правильный ответ!\nВаш счёт — {current_score}")
    else:
        correct_option = quiz_data[current_question_index]['correct_option']
        await callback.message.answer(f"Неправильно. "
                                      f"Правильный ответ: "
                                      f"{quiz_data[current_question_index]['options'][correct_option]}"
                                      f"\nВаш счёт — {current_score}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(user_id, current_question_index, db_name)

    # Проверка, остались ли ещё вопросы
    if current_question_index < len(quiz_data):
        await get_question(callback.message, user_id, quiz_data, db_name)
    else:
        # Обновление рекорда, если он побит
        highscore = await get_highscore(user_id, db_name)
        if current_score > highscore:
            highscore = current_score
            await update_highscore(user_id, highscore, db_name)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваш рекорд: {highscore}")


# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table(db_name)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
