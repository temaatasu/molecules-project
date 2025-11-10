import json
from typing import List
from redis.asyncio import Redis
from celery.result import AsyncResult
from rdkit import Chem

from src.core.logger import get_logger

from src.molecules.repository import MoleculeRepository
from src.molecules.schemas import MoleculeCreate, MoleculeUpdate, MoleculeInDB
from src.molecules.exceptions import (
    MoleculeNotFoundException,
    InvalidSmilesStringException,
)
from src.molecules.tasks import run_substructure_search

logger = get_logger(__name__)


class MoleculeService:

    def __init__(self, repository: MoleculeRepository, cache: Redis):
        self.repository = repository
        self.cache = cache
        self.rdkit_cache = {}

    def _validate_smiles(self, smiles: str) -> bool:
        """
        Validates a SMILES string using RDKit.
        Uses an in-memory cache for performance.
        """
        if smiles in self.rdkit_cache:
            return self.rdkit_cache[smiles]

        mol = Chem.MolFromSmiles(smiles)
        is_valid = mol is not None

        if is_valid:
            self.rdkit_cache[smiles] = True
            logger.debug(f"Validated SMILES: {smiles}")
        else:
            logger.warning(f"Invalid SMILES string: {smiles}")

        return is_valid

    async def create_molecule(self, molecule_create: MoleculeCreate) -> MoleculeInDB:
        """
        Creates a new molecule.
        """
        if not self._validate_smiles(molecule_create.smiles_string):
            raise InvalidSmilesStringException(molecule_create.smiles_string)

        db_molecule = await self.repository.add(molecule_create)
        return MoleculeInDB.model_validate(db_molecule)

    async def get_molecule_by_id(self, molecule_id: int) -> MoleculeInDB:
        """
        Gets a single molecule by ID, using Redis for caching.
        """
        cache_key = f"molecule:{molecule_id}"

        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT for molecule ID: {molecule_id}")
                return MoleculeInDB.model_validate(json.loads(cached_data))
        except Exception as e:
            logger.error(f"Redis cache read error: {e}")

        logger.info(f"Cache MISS for molecule ID: {molecule_id}")

        db_molecule = await self.repository.get_by_id(molecule_id)
        if not db_molecule:
            logger.warning(f"Molecule not found, ID: {molecule_id}")
            raise MoleculeNotFoundException(molecule_id=molecule_id)

        molecule_data = MoleculeInDB.model_validate(db_molecule)

        try:
            await self.cache.set(cache_key, molecule_data.model_dump_json(), ex=3600)
        except Exception as e:
            logger.error(f"Redis cache write error: {e}")

        return molecule_data

    async def list_molecules(self, skip: int, limit: int) -> List[MoleculeInDB]:
        """
        Lists molecules with pagination.
        """
        db_molecules = await self.repository.list_all(skip=skip, limit=limit)
        return [MoleculeInDB.model_validate(mol) for mol in db_molecules]

    async def update_molecule(
        self, molecule_id: int, molecule_update: MoleculeUpdate
    ) -> MoleculeInDB:
        """
        Updates a molecule.
        """
        if molecule_update.smiles_string and not self._validate_smiles(
            molecule_update.smiles_string
        ):
            raise InvalidSmilesStringException(molecule_update.smiles_string)

        db_molecule = await self.repository.update(molecule_id, molecule_update)
        if not db_molecule:
            logger.warning(f"Molecule not found for update, ID: {molecule_id}")
            raise MoleculeNotFoundException(molecule_id=molecule_id)

        cache_key = f"molecule:{molecule_id}"
        try:
            await self.cache.delete(cache_key)
            logger.info(f"Invalidated cache for molecule ID: {molecule_id}")
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")

        return MoleculeInDB.model_validate(db_molecule)

    async def delete_molecule(self, molecule_id: int) -> dict:
        """
        Deletes a molecule.
        """
        success = await self.repository.delete(molecule_id)
        if not success:
            logger.warning(f"Molecule not found for delete, ID: {molecule_id}")
            raise MoleculeNotFoundException(molecule_id=molecule_id)

        cache_key = f"molecule:{molecule_id}"
        try:
            await self.cache.delete(cache_key)
            logger.info(f"Invalidated cache for molecule ID: {molecule_id}")
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")

        return {"message": f"Molecule {molecule_id} deleted successfully."}

    async def start_search_task(self, substructure_smiles: str) -> dict:
        """
        Starts an asynchronous substructure search task.
        """
        if not self._validate_smiles(substructure_smiles):
            raise InvalidSmilesStringException(substructure_smiles)

        logger.info(f"Starting substructure search task for: {substructure_smiles}")
        task = run_substructure_search.delay(substructure_smiles)

        return {"task_id": task.id, "status": task.status}

    async def get_search_task_result(self, task_id: str) -> dict:
        """
        Gets the result of an asynchronous search task.
        """
        logger.debug(f"Checking task result for: {task_id}")
        task_result = AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
        }

        if task_result.failed():
            logger.error(f"Task {task_id} failed: {task_result.result}")
            response["result"] = str(task_result.result)  # Include error message

        return response
