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

async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_all_smiles_from_db() -> list[str]:
    """
    Async helper to stream all SMILES from the DB.
    This runs within the Celery task's event loop.
    """
    smiles_list = []
    async with AsyncSessionLocal() as session:
        repo = MoleculeRepository(session)
        smiles_stream = repo.get_all_smiles_stream()
        async for smiles in smiles_stream:
            smiles_list.append(smiles)
    return smiles_list


@celery_app.task(name="molecules.run_substructure_search")
def run_substructure_search(substructure_smiles: str) -> List[str]:
    """
    Celery task to run the substructure search.
    It fetches all molecules from the DB and then runs the search.
    """
    logger.info(f"Celery task started for: {substructure_smiles}")

    try:
        molecule_smiles_list = asyncio.run(get_all_smiles_from_db())
    except Exception as e:
        logger.error(f"Error fetching SMILES from DB in Celery task: {e}")
        raise

    if not molecule_smiles_list:
        logger.warning("No molecules in DB to search.")
        return []

    try:
        matches = substructure_search(molecule_smiles_list, substructure_smiles)
        return matches
    except Exception as e:
        logger.error(f"Error during RDKit search in Celery task: {e}")
        raise
