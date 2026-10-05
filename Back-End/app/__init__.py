import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_mailman import Mail

from app.config.settings import Config
from app.database.database import db, bcrypt, jwt
from app.models.novedad import Novedad
from app.models.reserva import Reserva

# Instanciamos el objeto Mail de forma global
mail = Mail()

# ── Inicialización de la instancia global de Migrate ────────────────────────
migrate = Migrate()

# ── Inicialización global de SocketIO para WebSockets en Tiempo Real ─────────
socketio = SocketIO(
    cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    async_mode="gevent"  # o "eventlet" / "threading" según tu entorno de servidor
)


def create_app():
    """
    Crea y configura la aplicación Flask de ParkLink.
    Devuelve la instancia lista para ser ejecutada por run.py o Gunicorn/eventlet.
    """
    app = Flask(__name__)

    # ── 1. Configuración ──────────────────────────────────────────────────────
    app.config.from_object(Config)

    # ── 2. CORS (una sola vez) ────────────────────────────────────────────────
    # Permite solicitudes HTTP REST desde el frontend React en desarrollo.
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=True,
    )

    # ── 3. Inicialización de extensiones ──────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # 💥 EXTENSIÓN AGREGADA: Inicializa y vincula Flask-Mailman con el ciclo de vida de la App
    mail.init_app(app)

    # 🛠️ Inicializa y vincula Flask-Migrate con la App y SQLAlchemy
    migrate.init_app(app, db)

    # ⚡ Inicializa y vincula Flask-SocketIO para eventos en tiempo real
    socketio.init_app(app, cors_allowed_origins="*")

    # ── 4. Manejadores de errores JWT ─────────────────────────────────────────
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "mensaje": "El token ha expirado. Inicia sesión nuevamente.",
            "error": "token_expired"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "mensaje": "Token inválido o corrupto.",
            "error": "invalid_token"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "mensaje": "Se requiere autenticación. No se encontró un token de acceso.",
            "error": "authorization_required"
        }), 401

    # ── 5. Registro de Blueprints ─────────────────────────────────────────────
    # Se importan aquí dentro para prevenir referencias circulares en Python.
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.accesos import accesos_bp
    from app.routes.celdas import celdas_bp
    from app.routes.alertas import alertas_bp
    from app.routes.kpis import kpis_bp
    from app.routes.logs import logs_bp
    from app.routes.configuraciones import config_bp
    from app.routes.tendencias import tendencias_bp
    from app.routes.vigilante import vigilante_bp
    from app.routes.usuario import usuario_bp
    from app.routes.reportes import reportes_bp

    # Registro limpio y obligatorio de los controladores de ParkLink
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(accesos_bp, url_prefix="/api/admin")
    app.register_blueprint(celdas_bp, url_prefix="/api/admin")
    app.register_blueprint(alertas_bp, url_prefix="/api/admin")
    app.register_blueprint(kpis_bp, url_prefix="/api/admin")
    app.register_blueprint(logs_bp)
    app.register_blueprint(config_bp, url_prefix="/api/admin")
    app.register_blueprint(tendencias_bp)
    app.register_blueprint(vigilante_bp, url_prefix="/api/vigilante")
    app.register_blueprint(usuario_bp)
    app.register_blueprint(reportes_bp, url_prefix="/api/reportes")

    # ── 6. Eventos básicos de WebSockets ──────────────────────────────────────
    @socketio.on("connect")
    def handle_connect():
        print("⚡ Cliente conectado exitosamente vía WebSocket al servidor ParkLink")

    @socketio.on("disconnect")
    def handle_disconnect():
        print("🔌 Cliente desconectado del servicio WebSocket")

    # ── 7. Ruta de salud ──────────────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "online",
            "project": "ParkLink",
            "websocket": "enabled",
            "version": "1.0.0"
        }), 200

    return app