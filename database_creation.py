import aiosqlite


async def create_table(db_name):
    async with aiosqlite.connect(db_name) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS quiz_state (
                user_id INTEGER PRIMARY KEY,
                question_index INTEGER,
                current_score INTEGER,
                highscore INTEGER
            )
        ''')
        await db.commit()
