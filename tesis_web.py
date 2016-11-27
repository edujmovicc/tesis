import json
import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, logout_user
from flask.ext.security.forms import LoginForm
from utilidades_tesis import buscar_parecidos, normalizar_titulo
from tesis_orm import conectar_a_bd, Tesis, Alumno, Tutor, LineaDeInvestigacion
from clasificacion import ClasificadorLineasInvestigacion

app = Flask(__name__)
bd = conectar_a_bd()
clasificador = ClasificadorLineasInvestigacion()

BASE_DIR = os.path.dirname(__file__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}test.db'.format(BASE_DIR)
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_REGISTER_URL'] = '/crear_usuario'
app.config["SECURITY_LOGIN_URL"] = "/acceder"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/administrar"
app.config["SECURITY_LOGOUT_URL"] = "/cerrar_sesion"

auth_db = SQLAlchemy(app)
# Define models
roles_users = auth_db.Table('roles_users',
        auth_db.Column('user_id', auth_db.Integer(), auth_db.ForeignKey('user.id')),
        auth_db.Column('role_id', auth_db.Integer(), auth_db.ForeignKey('role.id')))

class Role(auth_db.Model, RoleMixin):
    id = auth_db.Column(auth_db.Integer(), primary_key=True)
    name = auth_db.Column(auth_db.String(80), unique=True)
    description = auth_db.Column(auth_db.String(255))

class User(auth_db.Model, UserMixin):
    id = auth_db.Column(auth_db.Integer, primary_key=True)
    email = auth_db.Column(auth_db.String(255), unique=True)
    password = auth_db.Column(auth_db.String(255))
    active = auth_db.Column(auth_db.Boolean())
    confirmed_at = auth_db.Column(auth_db.DateTime())
    roles = auth_db.relationship('Role', secondary=roles_users,
                            backref=auth_db.backref('users', lazy='dynamic'))
                            
user_datastore = SQLAlchemyUserDatastore(auth_db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def create_user():
    auth_db.create_all()
    auth_db.session.commit()                            
                            


@app.route("/", methods=["GET", "POST"])
def mostrar_homepage():
    if request.method == "GET":
        return render_template("home.html", sin_identificar=True)
    elif request.method == "POST":
        print("es una busqueda")
        return buscar_similares()

def buscar_similares():
    titulo = request.form["titulo"]
    print(titulo)
    parecidos = buscar_parecidos(titulo, margen=90)
    print(len(parecidos))
    return render_template("home.html", parecidos=parecidos, sin_identificar=True)


@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    if request.method == "GET":
        return render_template("ingresar.html", sin_identificar=True)
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
            return redirect(url_for("administrar"))


def renderizar_panel(**activo):
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    return render_template(
        "administracion.html", 
        lineas_investigacion_select=lineas_investigacion,
        **activo
    )



# ALUMNOS
@app.route("/administrar", methods=["GET"])
def administrar():
    return render_template("administrar_alumnos.html", active_menu="alumnos")
    
@app.route("/buscar_alumnos", methods=["POST"])
def buscar_alumnos():
    if not "cedula_alumno" in request.form:
        return "Provea un número de cédula", 400

    alumnos = bd.query(Alumno).filter(
        Alumno.cedula.ilike("%{}%".format(request.form["cedula_alumno"]))).all()
    
    #return renderizar_panel(buscando_alumnos="active", alumnos=alumnos)
    return render_template("administrar_alumnos.html", alumnos=alumnos)
    
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
            
        
@app.route("/obtener_linea_y_tutores", methods=["POST"])
def obtener_linea_y_tutores():
    data = json.loads(request.data.decode("utf8"))
    print(data)
    if not "nuevo_titulo" in data or not data["nuevo_titulo"]:
        return "Se require el titulo", 400
    
    nombre_linea = obtener_linea_investigacion(data["nuevo_titulo"])
    if nombre_linea:
        linea = bd.query(LineaDeInvestigacion).filter_by(nombre=nombre_linea).first()
        if linea:
            print(linea.__dict__)
            tutores = linea.tutores
            return json.dumps({
                "linea": nombre_linea,
                "tutores": [
                    [tutor.indice, "{} {}".format(tutor.nombre, tutor.apellido)]
                    for tutor in tutores
                ]
            })
    return "", 400
    
    
    
    
    


# TUTORES    
@app.route("/administrar_tutores", methods=["GET"])
def administrar_tutores():
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    return render_template("administrar_tutores.html",
        lineas_investigacion_select=lineas_investigacion, 
        active_menu="tutores")
    
    
@app.route("/buscar_tutores", methods=["POST"])
def buscar_tutores():
    if not "cedula_tutor" in request.form:
        return "Provea un número de cédula", 400
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    tutores = bd.query(Tutor).filter(
        Tutor.cedula.ilike("%{}%".format(request.form["cedula_tutor"]))).all()

    # return renderizar_panel(
    #     tutores=tutores,
    #     buscando_tutores="active"
    # )
    return render_template("administrar_tutores.html", tutores=tutores, lineas_investigacion_select=lineas_investigacion)
    
    
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
        lineas_investigacion = bd.query(LineaDeInvestigacion).all()
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
            #return renderizar_panel(buscando_tutores="active")
            return render_template("administrar_tutores.html", lineas_investigacion_select=lineas_investigacion)


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

@app.route("/borrar_tutor/<indice>", methods=["GET"])
def borrar_tutor(indice):
    tutor = bd.query(Tutor).get(indice)
    lineas_investigacion = bd.query(LineaDeInvestigacion).all()
    if tutor:
        bd.delete(tutor)
        bd.commit()
    #return renderizar_panel(buscando_tutores="active")
    return render_template("administrar_tutor.html", lineas_investigacion_select = lineas_investigacion)

    
    
# LINEAS INVESTIGACION
    
@app.route("/administrar_lineas_investigacion", methods=["GET"])
def administrar_lineas_investigacion():
    return render_template("administrar_lineas_investigacion.html", active_menu="lineas")


@app.route("/buscar_lineas_investigacion", methods=["POST"])
def buscar_lineas_investigacion():
    if not "linea_investigacion" in request.form:
        return "Provea parte del nombre, de una línea de investigación", 400

    l_inv = bd.query(LineaDeInvestigacion).filter(
        LineaDeInvestigacion.nombre.ilike("%{}%".format(request.form["linea_investigacion"]))).all()

    return render_template("administrar_lineas_investigacion.html", lineas_investigacion=l_inv)


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
    campos_obligatorios = ["tutor_nuevo_titulo", "nuevo_titulo",
    "status_nuevo_titulo", "linea_nuevo_titulo"]
    if any([campo not in request.form for campo in campos_obligatorios]):
        return "Complete el campo faltante", 400
    alumno = bd.query(Alumno).get(indice)
    if any([tesis.status == "aprobado" for tesis in alumno._tesis]):
        return render_template(
            "editar_alumno.html", alumno=alumno, error="Ya tiene un título aprobado")
    else:
        tutor = bd.query(Tutor).get(request.form["tutor_nuevo_titulo"])
        linea = request.form["linea_nuevo_titulo"]
        linea = bd.query(LineaDeInvestigacion).filter_by(nombre=linea).first()

        tesis = Tesis(
            titulo = request.form["nuevo_titulo"],
            tutor = tutor, 
            linea_investigacion = linea,
            autor = alumno,
            titulo_normalizado = normalizar_titulo(request.form["nuevo_titulo"]),
            status = request.form["status_nuevo_titulo"]
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


    
def serve_static(path):
    return send_from_directory('static/', path)

@app.route('/fonts/<path>')
def serve_fonts(path):
    return send_from_directory('static/fonts/', path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)