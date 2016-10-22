from flask import Flask, render_template, request
import json
from utilidades_tesis import buscar_parecidos

app = Flask(__name__)


@app.route("/")
def mostrar_homepage():
    return render_template("home.html")


@app.route("/buscar_similares", methods=["POST"])
def buscar_similares():
    titulo = request.form["titulo"]

    parecidos = buscar_parecidos(titulo, margen=90)
    return render_template("resultados.html", parecidos=parecidos)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)