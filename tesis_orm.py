import uuid
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (create_engine, Column, Integer, String,
    ForeignKey)
from sqlalchemy.orm import sessionmaker, relationship, validates

Base = declarative_base()

def generar_identificador_unico():
    return str(uuid.uuid4())

def conectar_a_bd(ruta="tesis.db"):

    engine = create_engine("sqlite:///{}".format(ruta))

    Base.metadata.create_all(engine)
    Session = sessionmaker()
    Session.configure(bind = engine )
    return Session()

class LineaDeInvestigacion(Base):
    __tablename__ = "lineas_de_investigacion"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    tutores = relationship("Tutor", secondary="tutor_linea",
        backref="_lineas_investigacion")

    def __eq__(self, other):
        return self.nombre == other.nombre

    def __hash__(self):
        return hash(self.nombre)

    @validates('nombre')
    def convert_upper(self, key, value):
        return str(value).upper()


class Tesis(Base):
    __tablename__ = "tesis"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    titulo = Column(String)
    titulo_normalizado = Column(String)
    status = Column(String, default="PENDIENTE")

    tutor_indice = Column(String, ForeignKey("tutores.indice"))
    tutor = relationship("Tutor", backref="_tesis")

    autor_indice = Column(String, ForeignKey("alumnos.indice"))
    autor = relationship("Alumno", backref="_tesis")
    
    linea_investigacion_id = Column(String, ForeignKey("lineas_de_investigacion.indice"))
    linea_investigacion = relationship("LineaDeInvestigacion", backref="_tesis")


    def __eq__(self, other):
        return self.indice == other.indice

    @validates('titulo', "status")
    def convert_upper(self, key, value):
        return str(value).upper()


class Alumno(Base):
    __tablename__ = "alumnos"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    apellido = Column(String, default="")
    cedula = Column(String)
    carrera = Column(String, default="")

    def __eq__(self, other):
        return self.indice == other.indice

    @validates('nombre', "apellido", "carrera")
    def convert_upper(self, key, value):
        return str(value).upper()

 
class Tutor(Base):
    __tablename__ = "tutores"

    indice = Column(String, primary_key=True, default=generar_identificador_unico)
    nombre = Column(String)
    apellido = Column(String, default="")
    cedula = Column(String, default="")
    lineas_investigacion = relationship("LineaDeInvestigacion",
        secondary="tutor_linea", backref="_tutores")

    def __hash__(self):
        return hash(self.nombre)

    def __eq__(self, otro):
        return self.indice == otro.indice

    @validates('nombre', "apellido")
    def convert_upper(self, key, value):
        return str(value).upper()


class TutorLinea(Base):
    __tablename__ = "tutor_linea"
    tutor_id = Column(String, ForeignKey("tutores.indice"), primary_key=True)
    linea_id = Column(String, ForeignKey("lineas_de_investigacion.indice"), primary_key=True)




