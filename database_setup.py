import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class GrupoAlimentar(Base):
    __tablename__ = 'grupo_alimentar'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    addedby = Column(String(250))

    @property
    def serialize(self):
        return{
            'name': self.name,
            'id': self.id,
        }


class Alimento(Base):
    __tablename__ = 'alimento'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    calories = Column(String(8))
    weight = Column(String(8))
    food_group_id = Column(Integer, ForeignKey('grupo_alimentar.id'))
    grupo_alimentar = relationship(GrupoAlimentar)
    addedby = Column(String(250))

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'calories': self.calories,
            'weight': self.weight,
        }

engine = create_engine('sqlite:///gruposalimentares.db')
Base.metadata.create_all(engine)
