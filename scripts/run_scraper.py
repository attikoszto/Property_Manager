"""
Run scraper manually for the initial data collection.
"""

import asyncio

from workers.scraper_worker import ScraperWorker


async def main() -> None:
    worker = ScraperWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
