# app/routes/auth.py
"""
ParkLink - Rutas de autenticación pública y común.
Blueprint: auth_bp
Prefijo registrado: /api/auth
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.auth_controller import AuthController
from app.models.usuario import Usuario

auth_bp = Blueprint("auth", __name__)

# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """Autentica al usuario y devuelve un token JWT."""
    return AuthController.login()

# ── Perfil (ruta protegida) ───────────────────────────────────────────────────
@auth_bp.route("/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    """Devuelve los datos del usuario autenticado común."""
    usuario_id = get_jwt_identity()
    # Si guardaste la identidad como un diccionario, accede a su ID. Si guardaste solo el ID directamente:
    # usuario_id = get_jwt_identity().get('id') si es diccionario.
    usuario = Usuario.query.get(int(usuario_id))

    if not usuario or not usuario.activo:
        return jsonify({"mensaje": "Usuario no encontrado o sesión inválida."}), 404

    return jsonify({"usuario": usuario.to_dict()}), 200