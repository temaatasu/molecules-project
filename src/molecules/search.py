from rdkit import Chem
from typing import List


def substructure_search(molecules: List[str], substructure: str) -> List[str]:
    """
    Find molecules that contain a given substructure.

    Args:
        molecules (List[str]): A list of molecules as SMILES strings.
        substructure (str): A substructure as SMILES string.

    Returns:
        List[str]: A list of SMILES strings from 'molecules' that contain the specified
        substructure.
    """
    substructure_mol = Chem.MolFromSmiles(substructure)
    if substructure_mol is None:
        raise ValueError("Invalid substructure")

    matches: List[str] = []
    for molecule in molecules:
        mol = Chem.MolFromSmiles(molecule)
        if mol is not None and mol.HasSubstructMatch(substructure_mol):
            matches.append(molecule)
    return matches
