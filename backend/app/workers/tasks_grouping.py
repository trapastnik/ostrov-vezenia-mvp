import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks_grouping.run_grouping_optimizer")
def run_grouping_optimizer():
    """
    Celery task: запускает оптимизатор группировки.
    Вызывается по расписанию через Celery Beat.
    """
    asyncio.run(_run_async())


async def _run_async():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.services.grouping_optimizer import GroupingOptimizer
    from app.services.pochta import PochtaClient

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    pochta = PochtaClient(settings)
    await pochta.start()

    try:
        async with async_session() as session:
            optimizer = GroupingOptimizer(session, pochta)
            decisions = await optimizer.run(sender_postal_code=settings.SENDER_POSTAL_CODE)

            for decision in decisions:
                group = await optimizer.apply_decision(decision)
                logger.info(
                    "Сформирована группа %s: %d заказов, хаб=%s, экономия=%d коп. (причина: %s)",
                    group.number, group.orders_count, group.hub,
                    group.savings_kopecks, decision.reason,
                )
    finally:
        await pochta.close()
        await engine.dispose()
