import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.core.security import get_password_hash

async def main():
    new_hash = get_password_hash("12345678")
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET hashed_password = :h WHERE phone = '01700000000' OR phone = '01601593895';"),
            {"h": new_hash}
        )
        print("Password reset to 12345678")

asyncio.run(main())
