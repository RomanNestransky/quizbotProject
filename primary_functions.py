import aiosqlite
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types


async def new_quiz(message, quiz_data, db_name):
    user_id = message.from_user.id
    current_question_index = 0
    current_score = 0
    # Также устанавливаем 0 нашему счёту очков
    await update_current_score(user_id, current_score, db_name)
    await update_quiz_index(user_id, current_question_index, db_name)
    await get_question(message, user_id, quiz_data, db_name)


async def get_question(message, user_id, quiz_data, db_name):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id, db_name)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        # Определяем верность ответов 1 - правильно, 0 - неправильно (оптимизация, т.к. макс. размер коллбэка – 64байта)
        if option == right_answer:
            answer_state = "1"
        else:
            answer_state = "0"
        builder.add(types.InlineKeyboardButton(
            text=option,
            # Callback составной. Он будет ловиться по первому слову, затем разбиваться на части с помощью split()
            callback_data=f"answer:{answer_state}:{option}")
        )

    builder.adjust(1)
    return builder.as_markup()


# Получение индекса текущего вопроса
async def get_quiz_index(user_id, db_name):
    # Подключаемся к базе данных
    async with aiosqlite.connect(db_name) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results[0] is not None:
                return results[0]
            else:
                return 0


# Обновление индекса текущего вопроса
async def update_quiz_index(user_id, index, db_name):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(db_name) as db:
        # Вставка или замена. Пришлось сильно модифицировать этот запрос, чтобы он ничего не удалял
        await db.execute('''
            INSERT OR REPLACE INTO quiz_state (user_id, question_index, current_score, highscore)
            VALUES (?, ?, 
                    (SELECT current_score FROM quiz_state WHERE user_id = ?), 
                    (SELECT highscore FROM quiz_state WHERE user_id = ?)
            )
        ''', (user_id, index, user_id, user_id))
        # Сохраняем изменения
        await db.commit()


# Получение текущего счёта очков
async def get_current_score(user_id, db_name):
    async with aiosqlite.connect(db_name) as db:
        async with db.execute('SELECT current_score FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            results = await cursor.fetchone()
            if results[0] is not None:
                return results[0]
            else:
                return 0


# Обновляем текущие очки
async def update_current_score(user_id, c_score, db_name):
    # Соединение
    async with aiosqlite.connect(db_name) as db:
        # Вставка или замена
        await db.execute('''
            INSERT OR REPLACE INTO quiz_state (user_id, current_score, question_index, highscore)
            VALUES (?, ?, 
                    COALESCE((SELECT question_index FROM quiz_state WHERE user_id = ?), 0), 
                    COALESCE((SELECT highscore FROM quiz_state WHERE user_id = ?), 0)
            )
        ''', (user_id, c_score, user_id, user_id))
        # Применение изменений
        await db.commit()


# Получение текущего рекорда
async def get_highscore(user_id, db_name):
    # Соединение
    async with aiosqlite.connect(db_name) as db:
        # Получение рекорда
        async with db.execute('SELECT highscore FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results[0] is not None:
                return results[0]
            else:
                return 0


# Обновляем рекорды
async def update_highscore(user_id, h_score, db_name):
    # Соединение
    async with aiosqlite.connect(db_name) as db:
        # Вставка или замена
        await db.execute('''
            INSERT OR REPLACE INTO quiz_state (user_id, highscore, question_index, current_score)
            VALUES (?, ?, 
                    COALESCE((SELECT question_index FROM quiz_state WHERE user_id = ?), 0), 
                    COALESCE((SELECT current_score FROM quiz_state WHERE user_id = ?), 0)
            )
        ''', (user_id, h_score, user_id, user_id))
        # Применение изменений
        await db.commit()
