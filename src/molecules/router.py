from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.core.logger import get_logger
from src.core.database import get_db
from src.core.redis import get_redis
from src.molecules import schemas
from src.molecules.service import MoleculeService
from src.molecules.repository import MoleculeRepository
from src.molecules.exceptions import (
    MoleculeNotFoundException,
    InvalidSmilesStringException,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/molecules",
    tags=["Molecules"],
)


def get_molecule_service(
    db: AsyncSession = Depends(get_db), cache: Redis = Depends(get_redis)
) -> MoleculeService:
    """
    Dependency injector for the MoleculeService.
    """
    repo = MoleculeRepository(db)
    return MoleculeService(repository=repo, cache=cache)


@router.post(
    "/", response_model=schemas.MoleculeInDB, status_code=status.HTTP_201_CREATED
)
async def add_molecule(
    molecule: schemas.MoleculeCreate,
    service: MoleculeService = Depends(get_molecule_service),
):
    """
    Add a new molecule to the database.
    """
    try:
        new_molecule = await service.create_molecule(molecule)
        return new_molecule
    except InvalidSmilesStringException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating molecule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add molecule.",
        )


@router.get("/{molecule_id}", response_model=schemas.MoleculeInDB)
async def get_molecule(
    molecule_id: int, service: MoleculeService = Depends(get_molecule_service)
):
    """
    Retrieve a molecule by its ID.
    """
    try:
        molecule = await service.get_molecule_by_id(molecule_id)
        return molecule
    except MoleculeNotFoundException as e:
        logger.warning(f"Molecule not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting molecule {molecule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve molecule.",
        )


@router.get("/", response_model=List[schemas.MoleculeInDB])
async def list_molecules(
    skip: int = Query(0, ge=0, description="Offset to start from"),
    limit: int = Query(100, ge=1, le=1000, description="Number of molecules to return"),
    service: MoleculeService = Depends(get_molecule_service),
):
    """
    List all molecules with pagination.
    """
    try:
        molecules = await service.list_molecules(skip=skip, limit=limit)
        return molecules
    except Exception as e:
        logger.error(f"Error listing molecules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list molecules.",
        )


@router.put("/{molecule_id}", response_model=schemas.MoleculeInDB)
async def update_molecule(
    molecule_id: int,
    molecule: schemas.MoleculeUpdate,
    service: MoleculeService = Depends(get_molecule_service),
):
    """
    Update an existing molecule by its ID.
    """
    try:
        updated_molecule = await service.update_molecule(molecule_id, molecule)
        return updated_molecule
    except MoleculeNotFoundException as e:
        logger.warning(f"Molecule not found for update: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidSmilesStringException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating molecule {molecule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update molecule.",
        )


@router.delete("/{molecule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_molecule(
    molecule_id: int, service: MoleculeService = Depends(get_molecule_service)
):
    """
    Delete a molecule by its ID.
    """
    try:
        await service.delete_molecule(molecule_id)
        return None  # 204 No Content
    except MoleculeNotFoundException as e:
        logger.warning(f"Molecule not found for deletion: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting molecule {molecule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete molecule.",
        )


@router.post(
    "/search/start",
    response_model=schemas.SearchTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_substructure_search(
    request: schemas.SearchTaskRequest,
    service: MoleculeService = Depends(get_molecule_service),
):
    """
    Start an asynchronous substructure search.
    """
    try:
        task = await service.start_search_task(request.substructure_smiles)
        return task
    except InvalidSmilesStringException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting search task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start search task.",
        )


@router.get("/search/results/{task_id}", response_model=schemas.SearchResultResponse)
async def get_search_results(
    task_id: str, service: MoleculeService = Depends(get_molecule_service)
):
    """
    Retrieve the results of an asynchronous substructure search task.
    """
    try:
        results = await service.get_search_task_result(task_id)
        return results
    except Exception as e:
        logger.error(f"Error getting task results for {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve search results.",
        )
