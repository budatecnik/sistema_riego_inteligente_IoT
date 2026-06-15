from sqlalchemy import Column, Integer, Float, Boolean, String


# Por esto:
from backend.database import Base

class Lectura(Base):

    __tablename__ = "lecturas"

    id = Column(Integer, primary_key=True, index=True)

    temperatura = Column(Float)

    humedad = Column(Float)

    humedad_suelo = Column(Integer)

    luz = Column(Boolean)

    timestamp = Column(String)
