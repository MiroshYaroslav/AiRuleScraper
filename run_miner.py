import asyncio
import logging
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.models import ReviewRule, Technology, ScrapingTask
from app.services.scraper import fetch_article_text
from app.services.ai_miner import extract_rules_from_text, generate_embedding

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MinerWorker")

SIMILARITY_THRESHOLD = 0.15


async def process_task(db, task: ScrapingTask) -> int:
    logger.info(f"Processing URL: {task.url}")
    task.status = "PROCESSING"
    await db.commit()

    try:
        raw_text = await fetch_article_text(task.url)
        if not raw_text or len(raw_text) < 100:
            task.status = "ERROR"
            await db.commit()
            return 0

        proposed_rules = await extract_rules_from_text(raw_text)

        for rule_data in proposed_rules:
            rule_name = rule_data.get("name", "Unknown Rule")
            rule_text = f"Rule: {rule_name}. Desc: {rule_data.get('description', '')}. Bad: {rule_data.get('example_bad', '')} Good: {rule_data.get('example_good', '')}"

            embedding = await generate_embedding(rule_text)
            if not embedding:
                continue

            distance_expr = ReviewRule.embedding.cosine_distance(embedding)
            stmt = (
                select(ReviewRule.name, distance_expr).order_by(distance_expr).limit(1)
            )
            nearest = (await db.execute(stmt)).first()

            if nearest and nearest[1] < SIMILARITY_THRESHOLD:
                continue

            tech_objects = []
            for t_name in rule_data.get("technologies", []):
                t_name = t_name.lower().strip()
                t_stmt = select(Technology).where(Technology.name == t_name)
                tech = (await db.execute(t_stmt)).scalar_one_or_none()
                if not tech:
                    tech = Technology(name=t_name)
                    db.add(tech)
                    await db.commit()
                    await db.refresh(tech)
                tech_objects.append(tech)

            new_rule = ReviewRule(
                name=rule_name,
                description=rule_data.get("description", ""),
                example_bad=rule_data.get("example_bad", ""),
                example_good=rule_data.get("example_good", ""),
                is_global=True,
                embedding=embedding,
                technologies=tech_objects,
            )
            db.add(new_rule)
            await db.commit()
            logger.info(f"Added new rule: '{rule_name}'")

            await asyncio.sleep(4.0)

        task.status = "DONE"
        await db.commit()
        return 15

    except Exception as e:
        await db.rollback()
        error_msg = str(e)

        if (
            "429" in error_msg
            or "exhausted" in error_msg.lower()
            or "503" in error_msg
            or "unavailable" in error_msg.lower()
        ):
            logger.warning(
                f"All pools exhausted for {task.url}. Requeuing and sleeping for 60s..."
            )
            task.status = "PENDING"
            await db.commit()
            return 60
        else:
            logger.error(f"Critical error processing {task.url}", exc_info=True)
            task.status = "ERROR"
            await db.commit()
            return 0


async def worker_loop():
    logger.info("Miner worker started. Waiting for tasks...")
    while True:
        sleep_time = 10

        try:
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(ScrapingTask)
                    .where(ScrapingTask.status == "PENDING")
                    .limit(1)
                )
                task = (await db.execute(stmt)).scalar_one_or_none()

                if task:
                    sleep_time = await process_task(db, task)

        except Exception:
            logger.error("Database connection error in worker loop", exc_info=True)
            sleep_time = 10

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info(
            "Received termination signal (KeyboardInterrupt). Initiating graceful shutdown..."
        )
