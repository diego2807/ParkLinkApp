# app/routes/alertas.py
"""
ParkLink - Controlador de rutas para la gestión y auditoría de alertas del sistema.
Blueprint: alertas_bp
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.database import db
from app.models.alertas import Alerta  # 💡 Importación correcta de la clase Alerta en singular
from datetime import datetime, timezone

alertas_bp = Blueprint("alertas", __name__)

# ── 1. OBTENER TODAS LAS ALERTAS (GET) ──────────────────────────────────────
@alertas_bp.route("/alertas", methods=["GET"])
@jwt_required()
def obtener_alertas():
    """
    Retorna el listado cronológico de alertas activas en el parqueadero corporativo.
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        # Traer todas las alertas de la más reciente a la más vieja
        registros = Alerta.query.order_by(Alerta.fecha_publicacion.desc()).all()
        
        resultado = []
        for a in registros:
            # Formatear la fecha a un string limpio para React
            fecha_str = a.fecha_publicacion.strftime("%Y-%m-%d %H:%M:%S") if a.fecha_publicacion else "Sin fecha"
            
            resultado.append({
                "id": a.id,
                "titulo": a.titulo,
                "severidad": a.severidad.lower().strip(),  # Aseguramos minúsculas para los filtros en React
                "contenido": a.contenido,
                "fecha_publicacion": fecha_str
            })

        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Error en GET /alertas: {str(e)}")
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500


# ── 2. EMITIR NUEVA ALERTA / COMUNICADO (POST) ──────────────────────────────
@alertas_bp.route("/alertas", methods=["POST"])
@jwt_required()
def publicar_alerta():
    """
    Permite al administrador publicar un comunicado manual en la bitácora corporativa.
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        data = request.get_json(silent=True) or {}
        titulo = data.get('titulo')
        severidad = data.get('severidad', 'informativo')
        contenido = data.get('contenido')

        # Validaciones de campos obligatorios
        if not titulo or not contenido:
            return jsonify({"error": "El título y el contenido son campos obligatorios."}), 400

        # Crear la instancia mapeada usando tu modelo de SQLAlchemy
        nueva_novedad = Alerta(
            titulo=titulo.strip(),
            severidad=severidad.strip().lower(),
            contenido=contenido.strip()
        )

        db.session.add(nueva_novedad)
        db.session.commit()

        return jsonify({
            "message": f"Comunicado '{titulo.strip()}' publicado y propagado con éxito."
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /alertas: {str(e)}")
        return jsonify({"error": f"Error interno al propagar el aviso: {str(e)}"}), 500


# ── 3. DESCARTAR / ELIMINAR UNA ALERTA (DELETE) ─────────────────────────────
@alertas_bp.route("/alertas/<int:alerta_id>", methods=["DELETE"])
@jwt_required()
def eliminar_alerta(alerta_id):
    """
    Permite al administrador o vigilante descartar una alerta de la interfaz.
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        alerta = Alerta.query.get(alerta_id)
        if not alerta:
            return jsonify({"error": "La alerta especificada no existe en el sistema."}), 404

        # Eliminar físicamente el registro de la bitácora
        db.session.delete(alerta)
        db.session.commit()

        return jsonify({"message": "La alerta ha sido descartada del panel de control con éxito."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en DELETE /alertas: {str(e)}")
        return jsonify({"error": f"Error interno al eliminar la alerta: {str(e)}"}), 500