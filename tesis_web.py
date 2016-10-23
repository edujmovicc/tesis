from flask import Flask, render_template, request
import json
from utilidades_tesis import buscar_parecidos
from tesis_orm import conectar_a_bd, Tesis, Alumno

app = Flask(__name__)
bd = conectar_a_bd()


@app.route("/", methods=["GET", "POST"])
def mostrar_homepage():
    if request.method == "GET":
        return render_template("home.html")
    elif request.method == "POST":
        return buscar_similares()

def buscar_similares():
    titulo = request.form["titulo"]

    parecidos = buscar_parecidos(titulo, margen=90)
    return render_template("resultados.html", parecidos=parecidos)


@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    if request.method == "GET":
        return render_template("ingresar.html")
    if request.method == "POST":
        return autentificar()


def autentificar():
    if "usuario" not in request.form:
        return "Provea un nombre de usuario", 400
    if "clave" not in request.form:
        return "Provea una contraseña", 400

    usuario, clave = "administrador", "administrador"

    if request.form["usuario"] == usuario:
        if request.form["clave"] == clave:
            return render_template("administracion.html", buscando_alumno="active")


@app.route("/buscar_alumnos", methods=["POST"])
def buscar_alumnos():
    if not "cedula_alumno" in request.form:
        return "Provea un número de cédula", 400

    alumnos = bd.query(Alumno).filter(
        Alumno.cedula.ilike("%{}%".format(request.form["cedula_alumno"]))).all()
    print(len(alumnos))
    return render_template(
        "administracion.html", alumnos=alumnos,
        buscando_alumnos="active"
        )


@app.route("/buscar_tesis", methods=["POST"])
def buscar_tesis():
    if not "cedula_tesis" in request.form:
        return "Provea un número de cédula", 400

    alumno = bd.query(Alumno).filter(
        Alumno.cedula.ilike(request.form["cedula_tesis"])
    ).first()
    
    if alumno:
        return render_template(
            "administracion.html", tesis=alumno._tesis,
            alumno=alumno, buscando_tesis="active"
            )
    else:
        return render_template("administracion.html", buscando_tesis="active")


@app.route("/editar_alumno/<indice>", methods=["GET", "POST"])
def editar_alumno(indice):
    alumno = bd.query(Alumno).get(indice)
    if alumno:
        if request.method == "GET":
            return render_template("editar_alumno.html", alumno=alumno)
        elif request.method == "POST":
            actualizar_alumno(alumno)
    else:
        return "No existe el alumno", 400

def actualizar_alumno(alumno):
    alumno.nombre = request.form["nombre"]
    alumno.apellido = request.form["apellido"]
    alumno.cedula = request.form["cedula"]
    alumno.carrera = request.form["carrera"]
    bd.update(alumno)
    bd.commit()

    
@app.route("/editar_tesis/<indice>", methods=["GET", "POST"])
def editar_tesis(indice):
    tesis = bd.query(Tesis).get(indice)
    if tesis:
        if request.method == "GET":
            return render_template("editar_tesis.html", tesis=tesis)
        elif request.method == "POST":
            print(request.__dict__)
            actualizar_tesis(tesis)
            return "ok"
            #return render_template("editar_tesis.html", tesis=tesis)
    else:
        return "No existe la tesis", 400

def actualizar_tesis(tesis):
    print("Entro actualizar tesis")
    print(request.form.__dict__)
    tesis.titulo = request.form["titulo"]
    tesis.linea_investigacion = request.form["linea_investigacion"]
    tesis.status = request.form["status"]

    print("consultando tutor...")
    tutor = bd.query(Tutor).filter(
        Tutor.nombre.ilike(request.form["tutor_nombre"]),
        Tutor.apellido.ilike(request.form["tutor_apellido"])
        ).first()

    if not tutor:
        print("Creando tutor...")
        tutor = Tutor(
            nombre=request.form["tutor_nombre"],
            apellido = request.form["tutor_apellido"]
        )
        bd.add(tutor)
        bd.commit()

    tesis.tutor = tutor
    print("actualizando tesis...")
    bd.update(tesis)
    bd.commit()
    print("salio actualizar tesis")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)