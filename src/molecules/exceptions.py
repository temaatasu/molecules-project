class MoleculeException(Exception):
    pass


class MoleculeNotFoundException(MoleculeException):
    def __init__(self, molecule_id: int | str):
        self.message = f"Molecule with ID/SMILES '{molecule_id}' not found."
        super().__init__(self.message)


class InvalidSmilesStringException(MoleculeException):
    def __init__(self, smiles: str):
        self.message = f"The SMILES string '{smiles}' is invalid."
        super().__init__(self.message)
