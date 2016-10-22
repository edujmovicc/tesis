import uuid
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (create_engine, Column, Integer, String,
    ForeignKey)
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

def generar_identificador_unico():
    return str(uuid.uuid4())

def conectar_a_bd(ruta="tesis.db"):

    engine = create_engine("sqlite:///{}".format(ruta))

    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind = engine )
    return Session()


class Tesis(Base):
    __tablename__ = "tesis"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    titulo = Column(String)
    titulo_normalizado = Column(String)
    tutor = Column(String)
    nombre_autor = Column(String, ForeignKey("alumnos.indice"))
    autor = relationship("Alumno", backref="_tesis")


class Alumno(Base):
    __tablename__ = "alumnos"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    apellido = Column(String)
    cedula = Column(String)
    carrera = Column(String)

