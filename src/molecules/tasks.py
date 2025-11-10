import asyncio
from typing import List
from src.core.logger import get_logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from src.core.celery_app import celery_app
from src.molecules.search import substructure_search
from src.molecules.repository import MoleculeRepository
from src.core.config import settings

logger = get_logger(__name__)

_async_engine = None
_AsyncSessionLocal = None


def get_async_session_maker():
    """
    Lazy initialization of async engine and session maker for Celery worker.
    Each worker process should have its own connection pool.
    """
    global _async_engine, _AsyncSessionLocal
    if _async_engine is None:
        logger.info("Initializing async engine in Celery worker")
        _async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
        _AsyncSessionLocal = sessionmaker(
            bind=_async_engine, class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal


async def get_all_smiles_from_db() -> list[str]:
    """
    Async helper to stream all SMILES from the DB.
    This runs within the Celery task's event loop.
    """
    smiles_list = []
    AsyncSessionLocal = get_async_session_maker()
    
    async with AsyncSessionLocal() as session:
        try:
            repo = MoleculeRepository(session)
            smiles_stream = repo.get_all_smiles_stream()
            async for smiles in smiles_stream:
                smiles_list.append(smiles)
        except Exception as e:
            logger.error(f"Error streaming SMILES from DB: {e}")
            raise
    
    return smiles_list


@celery_app.task(name="molecules.run_substructure_search")
def run_substructure_search(substructure_smiles: str) -> List[str]:
    """
    Celery task to run the substructure search.
    It fetches all molecules from the DB and then runs the search.
    """
    logger.info(f"Celery task started for substructure: {substructure_smiles}")

    try:
        molecule_smiles_list = asyncio.run(get_all_smiles_from_db())
        logger.info(f"Fetched {len(molecule_smiles_list)} molecules from DB")
    except Exception as e:
        logger.error(f"Error fetching SMILES from DB in Celery task: {e}")
        raise

    if not molecule_smiles_list:
        logger.warning("No molecules in DB to search.")
        return []

    try:
        matches = substructure_search(molecule_smiles_list, substructure_smiles)
        logger.info(f"Found {len(matches)} matches for substructure search")
        return matches
    except Exception as e:
        logger.error(f"Error during RDKit search in Celery task: {e}")
        raise
