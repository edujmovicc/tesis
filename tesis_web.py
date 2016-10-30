from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import json
from utilidades_tesis import buscar_parecidos, normalizar_titulo
from tesis_orm import conectar_a_bd, Tesis, Alumno, Tutor, LineaDeInvestigacion
from clasificacion import ClasificadorLineasInvestigacion

app = Flask(__name__)
bd = conectar_a_bd()
clasificador = ClasificadorLineasInvestigacion()


@app.route("/", methods=["GET", "POST"])
def mostrar_homepage():
    if request.method == "GET":
        return render_template("home.html", sin_identificar=True)
    elif request.method == "POST":
        return buscar_similares()

def buscar_similares():
    titulo = request.form["titulo"]

    parecidos = buscar_parecidos(titulo, margen=90)
    return render_template("resultados.html", parecidos=parecidos, sin_identificar=True)


@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    if request.method == "GET":
        return render_template("ingresar.html", sin_identificar=True)
    if request.method == "POST":
        return autentificar()


@app.route("/administrar", methods=["GET"])
def administrar():
    if "buscando_tutores" in request.args:
        return renderizar_panel(buscando_tutores="active")
    elif "buscando_lineas" in request.args:
        return renderizar_panel(buscando_lineas="active")
    else:
        return renderizar_panel(buscando_alumnos="active")  


def autentificar():
    if "usuario" not in request.form:
        return "Provea un nombre de usuario", 400
    if "clave" not in request.form:
        return "Provea una contraseña", 400

    usuario, clave = "administrador", "administrador"

    if request.form["usuario"] == usuario:
        if request.form["clave"] == clave:
            return redirect(url_for("administrar"))


def renderizar_panel(**activo):
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    return render_template(
        "administracion.html", 
        lineas_investigacion_select=lineas_investigacion,
        **activo
    )


@app.route("/buscar_alumnos", methods=["POST"])
def buscar_alumnos():
    if not "cedula_alumno" in request.form:
        return "Provea un número de cédula", 400

    alumnos = bd.query(Alumno).filter(
        Alumno.cedula.ilike("%{}%".format(request.form["cedula_alumno"]))).all()
    
    return renderizar_panel(buscando_alumnos="active", alumnos=alumnos)


@app.route("/agregar_alumno", methods=["POST"])
def agregar_alumno():
    campos_obligatorios = [
        "agregar_alumno_cedula", "agregar_alumno_nombre",
        "agregar_alumno_apellido", "agregar_alumno_carrera"
    ]

    if not all([campo in request.form and request.form[campo] for campo in campos_obligatorios]):
        return "Complete el campo faltante", 400
    else:
        alumno = bd.query(Alumno).filter_by(cedula = request.form["agregar_alumno_cedula"]).first()
        if alumno:
            return "El alumno ya existe", 400
        else:
            alumno = Alumno(
                nombre = request.form["agregar_alumno_nombre"],
                apellido = request.form["agregar_alumno_apellido"],
                cedula = request.form["agregar_alumno_cedula"],
                carrera = request.form["agregar_alumno_carrera"]
            )
            
            bd.add(alumno)
            bd.commit()
            #return renderizar_panel(buscando_alumnos="active")
            return redirect(url_for("administrar", buscando_alumnos="active"))


@app.route("/buscar_tesis", methods=["POST"])
def buscar_tesis():
    if not "cedula_tesis" in request.form:
        return "Provea un número de cédula", 400

    alumno = bd.query(Alumno).filter(
        Alumno.cedula.ilike(request.form["cedula_tesis"])
    ).first()
    
    if alumno:
        return renderizar_panel(
            tesis=alumno._tesis,
            alumno=alumno,
            buscando_tesis="active"
        )
    else:
        return renderizar_panel(buscando_tesis="active")


@app.route("/buscar_tutores", methods=["POST"])
def buscar_tutores():
    if not "cedula_tutor" in request.form:
        return "Provea un número de cédula", 400

    tutores = bd.query(Tutor).filter(
        Tutor.cedula.ilike("%{}%".format(request.form["cedula_tutor"]))).all()

    return renderizar_panel(
        tutores=tutores,
        buscando_tutores="active"
    )

@app.route("/agregar_tutor", methods=["POST"])
def agregar_tutor():
    campos_obligatorios = [
        "agregar_tutor_cedula", "agregar_tutor_nombre",
        "agregar_tutor_apellido", "agregar_tutor_linea"
    ]

    if not all([campo in request.form and request.form[campo] for campo in campos_obligatorios]):
        return "Complete el campo {}".format(campo), 400
    else:
        tutor = bd.query(Tutor).filter_by(cedula = request.form["agregar_tutor_cedula"]).first()
        if tutor:
            return "El tutor ya existe", 400
        else:
            lineas = request.form.getlist("agregar_tutor_linea")
            lineas = [
                bd.query(LineaDeInvestigacion).get(linea)
                for linea in lineas
                ]

            tutor = Tutor(
                nombre = request.form["agregar_tutor_nombre"],
                apellido = request.form["agregar_tutor_apellido"],
                cedula = request.form["agregar_tutor_cedula"],
            )
            for linea in lineas:
                if linea not in tutor.lineas_investigacion:
                    tutor.lineas_investigacion.append(linea)

            bd.add(tutor)
            bd.commit()
            return renderizar_panel(buscando_tutores="active")

@app.route("/editar_tutor/<indice>", methods=["GET", "POST"])
def editar_tutor(indice):
    tutor = bd.query(Tutor).get(indice)
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    if tutor:
        if request.method == "GET":
            return render_template("editar_tutor.html", tutor=tutor, lineas_investigacion_select=lineas_investigacion)
        elif request.method == "POST":
            actualizar_tutor(tutor)
            return render_template("editar_tutor.html", tutor=tutor, lineas_investigacion_select = lineas_investigacion)
    else:
        return "No existe el tutor", 400

def actualizar_tutor(tutor):
    tutor.nombre = request.form["nombre"]
    tutor.apellido = request.form["apellido"]
    tutor.cedula = request.form["cedula"]
    lineas = request.form.getlist("lineas_investigacion")
    lineas = [
        bd.query(LineaDeInvestigacion).get(linea)
        for linea in lineas
    ]
    print(lineas)
    tutor.lineas_investigacion = lineas

    bd.merge(tutor)
    bd.commit()

@app.route("/buscar_lineas_investigacion", methods=["POST"])
def buscar_lineas_investigacion():
    if not "linea_investigacion" in request.form:
        return "Provea parte del nombre, de una línea de investigación", 400

    l_inv = bd.query(LineaDeInvestigacion).filter(
        LineaDeInvestigacion.nombre.ilike("%{}%".format(request.form["linea_investigacion"]))).all()

    return renderizar_panel(
        lineas_investigacion=l_inv,
        buscando_lineas_investigacion="active"
    )


@app.route("/agregar_linea_investigacion", methods=["POST"])
def agregar_linea_investigacion():
    if "linea_investigacion" in request.form:
        l_inv = LineaDeInvestigacion(nombre=request.form["linea_investigacion"])
        bd.add(l_inv)
        bd.commit()

        return renderizar_panel(buscando_lineas_investigacion="active")
    else:
        return "Provea una nueva línea de investigación", 400


@app.route("/borrar_linea_investigacion/<indice>")
def borrar_linea_investigacion(indice):
    l_inv = bd.query(LineaDeInvestigacion).get(indice)
    if l_inv:
        bd.delete(l_inv)
        bd.commit()
        return renderizar_panel(buscando_lineas_investigacion="active")
    else:
        return "No existe esa línea de investigación", 400



@app.route("/editar_alumno/<indice>", methods=["GET", "POST"])
def editar_alumno(indice):
    alumno = bd.query(Alumno).get(indice)
    lineas = bd.query(LineaDeInvestigacion).all()
    tutores = bd.query(Tutor).all()
    if alumno:
        if request.method == "GET":
            return render_template("editar_alumno.html", alumno=alumno, lineas=lineas, tutores=tutores)
        elif request.method == "POST":
            actualizar_alumno(alumno)
            return render_template("editar_alumno.html", alumno=alumno, lineas=lineas, tutores=tutores)
    else:
        return "No existe el alumno", 400

def actualizar_alumno(alumno):
    alumno.nombre = request.form["nombre"]
    alumno.apellido = request.form["apellido"]
    alumno.cedula = request.form["cedula"]
    alumno.carrera = request.form["carrera"]
    bd.merge(alumno)
    bd.commit()

@app.route("/borrar_alumno/<indice>", methods=["GET"])
def borrar_alumno(indice):
    alumno = bd.query(Alumno).get(indice)
    if alumno:
        bd.delete(alumno)
        bd.commit()
        return renderizar_panel(buscando_alumnos="active")


@app.route("/borrar_titulo/<indice>", methods=["GET"])
def borrar_titulo(indice):
    titulo = bd.query(Tesis).get(indice)
    lineas = bd.query(LineaDeInvestigacion).all()
    tutores = bd.query(Tutor).all()
    autor = titulo.autor
    if indice:
        bd.delete(titulo)
        bd.commit()
    return render_template("editar_alumno.html", alumno=autor, lineas=lineas, tutores=tutores)


@app.route("/agregar_titulo/<indice>", methods=["GET", "POST"])
def agregar_titulo(indice):
    campos_obligatorios = ["nuevo_tutor", "nuevo_titulo", "nuevo_status"]
    if any([campo not in request.form for campo in campos_obligatorios]):
        return "Complete el campo faltante", 400
    alumno = bd.query(Alumno).get(indice)
    lineas = bd.query(LineaDeInvestigacion).all()
    tutores = bd.query(Tutor).all()
    if any([tesis.status == "aprobado" for tesis in alumno._tesis]):
        return render_template(
            "editar_alumno.html", alumno=alumno,
            lineas=lineas, tutores=tutores, error="Ya tiene un título aprobado")
    else:
        tutor = bd.query(Tutor).get(request.form["nuevo_tutor"])
        linea = obtener_linea_investigacion(request.form["nuevo_titulo"])
        linea = bd.query(LineaDeInvestigacion).filter_by(nombre=linea).first()

        tesis = Tesis(
            titulo = request.form["nuevo_titulo"],
            tutor = tutor, 
            linea_investigacion = linea,
            autor = alumno,
            titulo_normalizado = normalizar_titulo(request.form["nuevo_titulo"]),
            status = request.form["nuevo_status"]
        )
        bd.add(tesis)
        bd.commit()
        #return render_template("editar_alumno.html", alumno=alumno, lineas=lineas, tutores=tutores)"
        return redirect("/editar_alumno/{}".format(alumno.indice))

def obtener_linea_investigacion(titulo):
    linea = clasificador.clasificar_titulo(titulo)[0]
    print(linea)
    return linea

    
@app.route("/editar_tesis/<indice>", methods=["GET", "POST"])
def editar_tesis(indice):
    tesis = bd.query(Tesis).get(indice)
    lineas = bd.query(LineaDeInvestigacion).all()
    tutores = bd.query(Tutor).all()
    if tesis:
        if request.method == "GET":
            return render_template("editar_tesis.html", tesis=tesis, lineas_investigacion=lineas, tutores=tutores)
        elif request.method == "POST":
            status = actualizar_tesis(tesis)
            if status != True:
                return render_template("editar_tesis.html", tesis=tesis, lineas_investigacion=lineas, tutores=tutores, error=status)
            else:
                return render_template("editar_tesis.html", tesis=tesis, lineas_investigacion=lineas, tutores=tutores)
    else:
        return "No existe la tesis", 400

def actualizar_tesis(tesis):
    tesis.titulo = request.form["titulo"]
 
    tesis.linea_investigacion = bd.query(LineaDeInvestigacion).get(request.form["linea_investigacion"])

    for titulo in tesis.autor._tesis:
        if titulo.status.lower() == "aprobado" and titulo != tesis:
            return "El alumno ya tiene un título aprobado"
    else:
        tesis.status = request.form["status"]

    tutor = bd.query(Tutor).get(request.form["tutor"])
    tesis.tutor = tutor
    bd.merge(tesis)
    bd.commit()
    return True


@app.route("/editar_linea/<indice>", methods=["GET", "POST"])
def editar_linea(indice):
    linea = bd.query(LineaDeInvestigacion).get(indice)
    if linea:
        if request.method == "GET":
            return render_template("editar_linea_investigacion.html", linea=linea)
        elif request.method == "POST":

            status = actualizar_linea(linea)
            if status == True:
                return render_template("editar_linea_investigacion.html", linea=linea)
            else:
                return render_template("editar_linea_investigacion.html", linea=linea, error=status)
    else:
        return "La línea de investigación no existe", 400


def actualizar_linea(linea):
    if "nombre" in request.form and request.form["nombre"]:
        linea.nombre = request.form["nombre"]
        bd.merge(linea)
        bd.commit()
        return True
    else:
        return "Por favor ingrese un nombre de línea de investigación."





@app.route('/static/<path>')
def serve_static(path):
    return send_from_directory('static/', path)

@app.route('/fonts/<path>')
def serve_fonts(path):
    return send_from_directory('static/fonts/', path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)