import pytest
from molecules.search import substructure_search

# Test data
MOLECULES = [
    "CCO",  # Ethanol
    "c1ccccc1",  # Benzene
    "CC(=O)O",  # Acetic Acid
    "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
    "C[C@H](O)C(=O)O",  # L-Lactic Acid
    "invalid-smiles-string",  # Invalid
]


def test_search_success_benzene_ring():
    """
    Test a successful search for the benzene ring.
    """
    substructure = "c1ccccc1"
    matches = substructure_search(MOLECULES, substructure)

    assert "c1ccccc1" in matches
    assert "CC(=O)Oc1ccccc1C(=O)O" in matches
    assert len(matches) == 2


def test_search_success_carboxylic_acid():
    """
    Test a successful search for the carboxylic acid group.
    """
    substructure = "C(=O)O"
    matches = substructure_search(MOLECULES, substructure)

    assert "CC(=O)O" in matches
    assert "CC(=O)Oc1ccccc1C(=O)O" in matches
    assert "C[C@H](O)C(=O)O" in matches
    assert len(matches) == 3


def test_search_no_matches():
    """
    Test a search that should return no results.
    """
    substructure = "F"
    matches = substructure_search(MOLECULES, substructure)
    assert len(matches) == 0


def test_search_invalid_substructure():
    """
    Test that an invalid substructure SMILES raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid substructure"):
        substructure_search(MOLECULES, "invalid-substructure")


def test_search_skips_invalid_molecules():
    """
    Test that the search runs successfully and just skips
    any invalid SMILES in the main molecule list.
    """
    substructure = "CCO"  # Ethanol
    matches = substructure_search(MOLECULES, substructure)

    assert "CCO" in matches
    assert len(matches) == 1


def test_search_with_empty_molecule_list():
    """
    Test that searching an empty list returns an empty list.
    """
    matches = substructure_search([], "c1ccccc1")
    assert len(matches) == 0
    assert matches == []
