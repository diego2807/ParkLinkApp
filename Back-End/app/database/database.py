"""
Instancias únicas de las extensiones de Flask usadas en todo ParkLink.

IMPORTANTE: este es el ÚNICO lugar donde se crean SQLAlchemy(), Bcrypt() y
JWTManager(). Tanto app/__init__.py como los modelos y servicios deben
importar estas mismas instancias para evitar tener dos "bases de datos"
desincronizadas dentro de la misma aplicación.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()