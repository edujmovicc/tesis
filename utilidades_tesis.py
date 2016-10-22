import re
from stop_words import get_stop_words
import unicodedata
from fuzzywuzzy import process, fuzz
from tesis_orm import Tesis, conectar_a_bd
bd = conectar_a_bd()

stop_words = get_stop_words("es")

def normalizar_titulo(titulo):
    titulo = titulo.lower()
    titulo = normalizar_digitos(titulo)
    titulo = quitar_stopwords(titulo)
    titulo = quitar_acentos(titulo)
    return titulo


def normalizar_digitos(titulo):
    return re.sub("\d","0", titulo)


def quitar_stopwords(titulo):
    titulo = titulo.split()
    titulo = [
        palabra for palabra in titulo
        if palabra not in stop_words
    ]

    return " ".join(titulo)


e_ascii = set([s for s in r'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,?!@#$%^&*()-_+=";:<>[]{}\|/'])
def quitar_acentos(titulo):
    return ''.join([s_char for s_char in unicodedata.normalize('NFD', titulo)
                    if s_char in e_ascii or unicodedata.category(s_char) != 'Mn'])


def comparar_difuso(s1, s2):
    return fuzz.token_set_ratio(s1,s2)


def buscar_parecidos(titulo, margen=70):
    titulo_limpio = normalizar_titulo(titulo)

    return [
        tesis for tesis in bd.query(Tesis).all()
        if fuzz.token_set_ratio(titulo_limpio, tesis.titulo_normalizado) >= margen
    ]


