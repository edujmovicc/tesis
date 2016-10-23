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
    nombre_tutor = Column(String, ForeignKey("tutores.nombre"))
    tutor = relationship("Tutor", backref="_tesis")
    nombre_autor = Column(String, ForeignKey("alumnos.nombre"))
    autor = relationship("Alumno", backref="_tesis")


class Alumno(Base):
    __tablename__ = "alumnos"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    apellido = Column(String, default="")
    cedula = Column(String)
    carrera = Column(String, default="")

 
class Tutor(Base):
    __tablename__ = "tutores"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    apellido = Column(String, default="")
    cedula = Column(String, default="")
    linea_investigacion = Column(String, default="")