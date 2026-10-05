# app/controllers/auth_controller.py
from flask import request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app.services.auth_service import AuthService


class AuthController:
    """
    Controlador encargado de gestionar las operaciones de autenticación pública
    y el ciclo de vida de las sesiones (Tokens JWT) en ParkLink.
    """
    @staticmethod
    def login():
        """
        Procesa el inicio de sesión de los usuarios.
        Valida credenciales y genera un token JWT seguro válido por 8 horas.
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"mensaje": "No se proporcionaron credenciales."}), 400

        # Captura tanto 'correo' como 'email' para prevenir fallos en el formulario React
        correo = data.get("correo") or data.get("email")
        password = data.get("password")

        if not correo or not password:
            return jsonify({"mensaje": "Correo y contraseña requeridos."}), 400

        # Delegación de la validación al servicio de negocio
        usuario, error = AuthService.login(correo, password)

        if error:
            # Si la cuenta está inactiva devuelve 403 (Prohibido); si están mal los datos, 401 (No autorizado)
            codigo = 403 if "inactiva" in error else 401
            return jsonify({"mensaje": error}), codigo

        # Extrae el valor en texto plano del Enum ('usuario', 'vigilante', 'administrador')
        rol_valor = usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol

        # Flask-JWT-Extended exige que el 'identity' (sub) sea una cadena de texto.
        # Guardamos el ID del usuario allí, y metemos el correo y el rol en las claims adicionales.
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={"correo": usuario.correo, "rol": rol_valor},
            expires_delta=timedelta(hours=8)
        )

        # Respuesta estructurada limpia compatible con api_auth.jsx y Login.jsx
        return jsonify({
            "mensaje": "Autenticación exitosa.",
            "token": token,
            "usuario": usuario.to_dict()
        }), 200