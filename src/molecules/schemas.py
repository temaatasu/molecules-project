from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class MoleculeBase(BaseModel):
    smiles_string: str
    name: Optional[str] = None


class MoleculeCreate(MoleculeBase):
    pass


class MoleculeUpdate(MoleculeBase):
    smiles_string: Optional[str] = None
    name: Optional[str] = None


class MoleculeInDB(MoleculeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SearchTaskRequest(BaseModel):
    substructure_smiles: str


class SearchTaskResponse(BaseModel):
    task_id: str
    status: str


class SearchResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[List[str]] = None
