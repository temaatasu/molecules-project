from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Molecule(Base):

    __tablename__ = "molecules"

    id = Column(Integer, primary_key=True, index=True)
    smiles_string = Column(Text, nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True, index=True)
