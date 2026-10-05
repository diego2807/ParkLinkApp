"""
Decorador reutilizable para proteger rutas según el rol del usuario autenticado.

Uso:
    from app.middlewares.roles import rol_requerido

    @admin_bp.route('/kpis', methods=['GET'])
    @jwt_required()
    @rol_requerido('administrador')
    def obtener_kpis():
        ...

El rol se compara siempre en minúsculas para evitar bugs por mayúsculas
inconsistentes entre el frontend, el JWT y el modelo (RolEnum usa minúsculas).
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def rol_requerido(*roles_permitidos):
    roles_normalizados = {r.lower() for r in roles_permitidos}

    def decorador(funcion_vista):
        @wraps(funcion_vista)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            rol_usuario = str(claims.get('rol', '')).lower()

            if rol_usuario not in roles_normalizados:
                return jsonify({
                    "mensaje": f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(roles_permitidos)}."
                }), 403

            return funcion_vista(*args, **kwargs)
        return wrapper
    return decorador
