from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, asc
from typing import List, Optional, AsyncGenerator

from src.core.logger import get_logger
from src.molecules.models import Molecule
from src.molecules.schemas import MoleculeCreate, MoleculeUpdate

logger = get_logger(__name__)


class MoleculeRepository:
    """
    Handles all database operations for molecules.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add(self, molecule: MoleculeCreate) -> Molecule:
        """
        Adds a new molecule to the database.
        """
        logger.info(f"Adding molecule to DB: {molecule.smiles_string}")
        db_molecule = Molecule(smiles_string=molecule.smiles_string, name=molecule.name)
        self.db_session.add(db_molecule)
        await self.db_session.commit()
        await self.db_session.refresh(db_molecule)
        return db_molecule

    async def get_by_id(self, molecule_id: int) -> Optional[Molecule]:
        """
        Retrieves a molecule by its primary key ID.
        """
        logger.debug(f"Getting molecule by ID: {molecule_id}")
        result = await self.db_session.execute(
            select(Molecule).where(Molecule.id == molecule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_smiles(self, smiles_string: str) -> Optional[Molecule]:
        """
        Retrieves a molecule by its SMILES string.
        """
        logger.debug(f"Getting molecule by SMILES: {smiles_string}")
        result = await self.db_session.execute(
            select(Molecule).where(Molecule.smiles_string == smiles_string)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Molecule]:
        """
        Lists all molecules with pagination (limit/offset).
        """
        logger.debug(f"Listing molecules: skip={skip}, limit={limit}")
        result = await self.db_session.execute(
            select(Molecule).order_by(asc(Molecule.id)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_all_smiles_stream(self) -> AsyncGenerator[str, None]:
        """
        Streams all SMILES strings from the database.
        """
        logger.info("Streaming all SMILES for search task")

        result = await self.db_session.stream(
            select(Molecule.smiles_string).order_by(asc(Molecule.id))
        )
        async for row in result:
            yield row[0]

    async def update(
        self, molecule_id: int, molecule_data: MoleculeUpdate
    ) -> Optional[Molecule]:
        """
        Updates an existing molecule by ID.
        """
        logger.info(f"Updating molecule ID: {molecule_id}")

        db_molecule = await self.get_by_id(molecule_id)
        if not db_molecule:
            return None

        update_data = molecule_data.model_dump(exclude_unset=True)

        if not update_data:
            return db_molecule

        await self.db_session.execute(
            sqlalchemy_update(Molecule)
            .where(Molecule.id == molecule_id)
            .values(**update_data)
        )
        await self.db_session.commit()
        await self.db_session.refresh(db_molecule)
        return db_molecule

    async def delete(self, molecule_id: int) -> bool:
        """
        Deletes a molecule by ID. Returns True on success.
        """
        logger.info(f"Deleting molecule ID: {molecule_id}")
        db_molecule = await self.get_by_id(molecule_id)
        if not db_molecule:
            return False

        await self.db_session.execute(
            sqlalchemy_delete(Molecule).where(Molecule.id == molecule_id)
        )
        await self.db_session.commit()
        return True
