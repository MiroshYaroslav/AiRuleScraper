import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.db.database import AsyncSessionLocal
from app.models import ScrapingTask
from app.services.crawler import find_internal_links

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Crawler")


async def populate_queue(target_url: str):
    links = await find_internal_links(target_url)

    async with AsyncSessionLocal() as db:
        added = 0
        for link in links:
            try:
                task = ScrapingTask(url=link, status="PENDING")
                db.add(task)
                await db.commit()
                added += 1
            except IntegrityError:
                await db.rollback()

        logger.info(f"Added {added} new URLs to the scraping queue from {target_url}.")


async def main():
    parser = argparse.ArgumentParser(
        description="Crawl URLs and add them to the database queue."
    )
    parser.add_argument(
        "--url", type=str, help="Crawl a specific URL (overrides seeds files)"
    )
    args = parser.parse_args()

    if args.url:
        logger.info(f"Starting crawler for CLI URL: {args.url}")
        await populate_queue(args.url)
        return

    seed_file = Path("seeds.txt")
    done_file = Path("seeds_done.txt")

    if not seed_file.exists():
        logger.error("seeds.txt not found and no --url argument provided!")
        return

    done_urls = set()
    if done_file.exists():
        with open(done_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    url_only = line.split("]")[-1].strip()
                    done_urls.add(url_only)

    with open(seed_file, "r", encoding="utf-8") as f:
        all_urls = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    urls_to_process = [url for url in all_urls if url not in done_urls]

    if not urls_to_process:
        logger.info("No new URLs to process. Everything is up to date!")
        return

    for url in urls_to_process:
        logger.info(f"Starting crawler for seed: {url}")
        await populate_queue(url)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(done_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {url}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(
            "Received termination signal (KeyboardInterrupt). Stopping crawler..."
        )
