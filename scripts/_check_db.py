"""Quick DB stats."""
import asyncio
from sqlalchemy import text
from infrastructure.database.session import engine

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT COUNT(*) FROM listings"))
        total = r.scalar()

        r2 = await conn.execute(text("SELECT platform, COUNT(*) FROM listings GROUP BY platform"))
        platforms = r2.fetchall()

        r3 = await conn.execute(text("SELECT property_type, COUNT(*) FROM listings GROUP BY property_type ORDER BY COUNT(*) DESC"))
        types = r3.fetchall()

        r4 = await conn.execute(text("SELECT COUNT(*) FROM weather_forecasts"))
        weather = r4.scalar()

        r5 = await conn.execute(text("SELECT AVG(base_price) FROM listings WHERE base_price > 0"))
        avg_price = r5.scalar()

        print(f"Total listings: {total}")
        for p in platforms:
            print(f"  {p[0]}: {p[1]}")
        print("Property types:")
        for t in types:
            print(f"  {t[0]}: {t[1]}")
        print(f"Weather forecasts: {weather}")
        print(f"Avg price (where >0): {avg_price:.2f}" if avg_price else "Avg price: N/A")

asyncio.run(check())
