import asyncio
from sqlalchemy import text
from app.db.session import engine

async def main():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT phone, role, full_name FROM users;"))
        for row in result:
            print(row)
        
        # Make the first user an admin if they exist
        await conn.execute(text("UPDATE users SET role = 'SUPER_ADMIN' WHERE phone = '01700000000' OR phone = '+8801700000000';"))

asyncio.run(main())
