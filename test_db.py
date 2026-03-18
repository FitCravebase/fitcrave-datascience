import asyncio
from app.database import init_db

async def main():
    try:
        await init_db()
        print("Test passed: Database initialized successfully.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
