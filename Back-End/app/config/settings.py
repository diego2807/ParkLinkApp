# app/config/settings.py
"""
ParkLink - Configuración centralizada de la aplicación.

Carga variables de entorno desde el archivo .env (python-dotenv).
Si no existe .env, usa valores por defecto seguros para desarrollo local con XAMPP.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carga el archivo .env ubicado junto a este archivo (o en la raíz del proyecto)
load_dotenv()


class Config:
    # ── Claves secretas ───────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "parklink_secret_key_cambia_esto_en_produccion")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "parklink_jwt_key_cambia_esto_en_produccion")

    # Tiempo de vida del token JWT (8 horas de sesión de trabajo)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # ── Conexión MySQL / XAMPP ────────────────────────────────────────────────
    MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")        # Sin contraseña en XAMPP por defecto
    MYSQL_HOST     = os.getenv("MYSQL_HOST",     "localhost")
    MYSQL_PORT     = os.getenv("MYSQL_PORT",     "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "parklink")

    # URI de SQLAlchemy con el driver PyMySQL
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        "?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Opciones del pool de conexiones ──────────────────────────────────────
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {
            "connect_timeout": 10,
        },
    }

    # ── Configuración para Flask-Mailman (Servicio de Mensajería) ──────────────
    # ── Configuración para Flask-Mailman (Servicio de Mensajería) ──────────────
    MAIL_SERVER   = os.getenv("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT     = int(os.getenv("MAIL_PORT", 465))
    MAIL_USE_TLS  = False  # 💥 Lo dejamos quemado en False para que no choque nunca
    MAIL_USE_SSL  = True   # 💥 Forzamos que use SSL para el puerto 465
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # ── Configuración de roles por correo ────────────────────────────────────
    EMAIL_VIGILANTE_DOMINIO = os.getenv("EMAIL_VIGILANTE_DOMINIO", "guardia1@gmail.com")

    EMAIL_ADMIN_EXACTOS = [
        correo.strip().lower()
        for correo in os.getenv("ADMIN_EMAILS", "admin@gmail.com").split(",")
        if correo.strip()
    ]