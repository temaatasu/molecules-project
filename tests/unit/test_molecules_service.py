import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.molecules.service import MoleculeService
from src.molecules.repository import MoleculeRepository
from src.molecules.schemas import MoleculeCreate, MoleculeUpdate, MoleculeInDB
from src.molecules.exceptions import (
    MoleculeNotFoundException,
    InvalidSmilesStringException,
)
from src.molecules.models import Molecule
from redis.asyncio import Redis
from celery.result import AsyncResult


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=MoleculeRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=Redis)


@pytest.fixture
def service(mock_repo: AsyncMock, mock_cache: AsyncMock) -> MoleculeService:
    return MoleculeService(repository=mock_repo, cache=mock_cache)


@pytest.mark.asyncio
async def test_get_molecule_by_id_cache_miss(
    service: MoleculeService, mock_repo: AsyncMock, mock_cache: AsyncMock
):
    mock_cache.get.return_value = None

    db_mol = Molecule(id=1, smiles_string="CCO", name="Ethanol")
    mock_repo.get_by_id.return_value = db_mol

    result = await service.get_molecule_by_id(1)

    assert result.id == 1
    assert result.smiles_string == "CCO"

    mock_cache.get.assert_called_with("molecule:1")

    mock_repo.get_by_id.assert_called_with(1)

    expected_cache_data = MoleculeInDB.model_validate(db_mol).model_dump_json()
    mock_cache.set.assert_called_with("molecule:1", expected_cache_data, ex=3600)


@pytest.mark.asyncio
async def test_get_molecule_by_id_cache_hit(
    service: MoleculeService, mock_repo: AsyncMock, mock_cache: AsyncMock
):

    cached_mol = MoleculeInDB(id=2, smiles_string="CC", name="Ethane")
    mock_cache.get.return_value = cached_mol.model_dump_json()

    result = await service.get_molecule_by_id(2)

    assert result.id == 2
    assert result.smiles_string == "CC"

    mock_cache.get.assert_called_with("molecule:2")
    mock_repo.get_by_id.assert_not_called()
    mock_cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_molecule_not_found(
    service: MoleculeService, mock_repo: AsyncMock, mock_cache: AsyncMock
):
    mock_cache.get.return_value = None
    mock_repo.get_by_id.return_value = None

    with pytest.raises(MoleculeNotFoundException):
        await service.get_molecule_by_id(999)


@pytest.mark.asyncio
async def test_create_molecule_success(service: MoleculeService, mock_repo: AsyncMock):
    mol_create = MoleculeCreate(smiles_string="CCO", name="Ethanol")
    db_mol = Molecule(id=1, smiles_string="CCO", name="Ethanol")
    mock_repo.add.return_value = db_mol

    result = await service.create_molecule(mol_create)

    mock_repo.add.assert_called_once_with(mol_create)
    assert result.id == 1
    assert result.smiles_string == "CCO"


@pytest.mark.asyncio
async def test_create_molecule_invalid_smiles(
    service: MoleculeService, mock_repo: AsyncMock
):
    invalid_mol_create = MoleculeCreate(smiles_string="invalid-smiles", name="Invalid")

    with pytest.raises(InvalidSmilesStringException):
        await service.create_molecule(invalid_mol_create)

    mock_repo.add.assert_not_called()


@pytest.mark.asyncio
async def test_update_molecule_success(
    service: MoleculeService, mock_repo: AsyncMock, mock_cache: AsyncMock
):
    mol_update = MoleculeUpdate(name="Ethanol Updated")
    db_mol_updated = Molecule(id=1, smiles_string="CCO", name="Ethanol Updated")
    mock_repo.update.return_value = db_mol_updated

    result = await service.update_molecule(1, mol_update)

    mock_repo.update.assert_called_once_with(1, mol_update)
    assert result.name == "Ethanol Updated"

    mock_cache.delete.assert_called_once_with("molecule:1")


@pytest.mark.asyncio
async def test_update_molecule_not_found(
    service: MoleculeService, mock_repo: AsyncMock
):
    mol_update = MoleculeUpdate(name="Test")
    mock_repo.update.return_value = None

    with pytest.raises(MoleculeNotFoundException):
        await service.update_molecule(999, mol_update)


@pytest.mark.asyncio
async def test_delete_molecule_success(
    service: MoleculeService, mock_repo: AsyncMock, mock_cache: AsyncMock
):
    mock_repo.delete.return_value = True

    result = await service.delete_molecule(1)

    mock_repo.delete.assert_called_once_with(1)
    assert result == {"message": "Molecule 1 deleted successfully."}

    mock_cache.delete.assert_called_once_with("molecule:1")


@pytest.mark.asyncio
async def test_delete_molecule_not_found(
    service: MoleculeService, mock_repo: AsyncMock
):
    mock_repo.delete.return_value = False  # Simulate not found

    with pytest.raises(MoleculeNotFoundException):
        await service.delete_molecule(999)


@pytest.mark.asyncio
@patch("src.molecules.service.run_substructure_search")  # Patch the task
async def test_start_search_task_success(
    mock_task: MagicMock, service: MoleculeService
):
    mock_task.delay.return_value = MagicMock(id="test-task-id", status="PENDING")

    result = await service.start_search_task("CCO")

    mock_task.delay.assert_called_once_with("CCO")
    assert result["task_id"] == "test-task-id"
    assert result["status"] == "PENDING"


@pytest.mark.asyncio
async def test_start_search_task_invalid_smiles(service: MoleculeService):
    # --- Act & Assert ---
    with pytest.raises(InvalidSmilesStringException):
        await service.start_search_task("invalid")


@pytest.mark.asyncio
@patch("src.molecules.service.AsyncResult")
async def test_get_search_task_result_success(
    mock_async_result: MagicMock, service: MoleculeService
):
    mock_task = MagicMock(spec=AsyncResult)
    mock_task.status = "SUCCESS"
    mock_task.ready.return_value = True
    mock_task.result = ["CCO", "CC"]
    mock_task.failed.return_value = False

    mock_async_result.return_value = mock_task

    result = await service.get_search_task_result("test-task-id")

    mock_async_result.assert_called_once_with("test-task-id")
    assert result["status"] == "SUCCESS"
    assert result["result"] == ["CCO", "CC"]


@pytest.mark.asyncio
@patch("src.molecules.service.AsyncResult")
async def test_get_search_task_result_failed(
    mock_async_result: MagicMock, service: MoleculeService
):
    mock_task = MagicMock(spec=AsyncResult)
    mock_task.status = "FAILURE"
    mock_task.ready.return_value = True
    mock_task.result = "SomeError"
    mock_task.failed.return_value = True

    mock_async_result.return_value = mock_task

    result = await service.get_search_task_result("failed-task-id")

    assert result["status"] == "FAILURE"
    assert result["result"] == "SomeError"
