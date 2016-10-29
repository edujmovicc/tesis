import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

class ClasificadorLineasInvestigacion(object):
    def __init__(self, ruta_bd="tesis.db"):
        bd = sqlite3.connect(ruta_bd)
        titulos = pd.read_sql(
            "select titulo_normalizado from tesis inner join lineas_de_investigacion on lineas_de_investigacion.indice = tesis.linea_investigacion_id",
            bd)
        lineas_investigacion = pd.read_sql(
            "select nombre from lineas_de_investigacion inner join tesis on lineas_de_investigacion.indice = tesis.linea_investigacion_id",
            bd)
        self.data_entrenamiento = pd.DataFrame()
        self.data_entrenamiento["titulo"]  = titulos
        self.data_entrenamiento["linea_investigacion"] = lineas_investigacion
        self.entrenar_clasificador()

    
    def vectorizar_titulos(self):
        self.vectorizador = CountVectorizer(analyzer="word", ngram_range=(1,2))
        return self.vectorizador.fit_transform(self.data_entrenamiento["titulo"])

    def entrenar_clasificador(self):
        self.clasificador = MultinomialNB()
        print("Entrenando el clasificador...")
        self.clasificador.fit(
            self.vectorizar_titulos(),
            self.data_entrenamiento["linea_investigacion"]
        )

    def clasificar_titulo(self, titulo):
        return self.clasificador.predict(
            self.vectorizador.transform([titulo])
        )