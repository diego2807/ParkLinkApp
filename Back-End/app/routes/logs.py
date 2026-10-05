# app/routes/logs.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.log_auditoria import LogAuditoria  
from app.database.database import db

logs_bp = Blueprint("logs", __name__, url_prefix="/api/admin")

@logs_bp.route("/logs", methods=["GET"])
@jwt_required()
def obtener_historial_logs():
    try:
        usuario_actual = get_jwt_identity()
        if not usuario_actual:
            return jsonify({"error": "Sesión no autorizada o expirada."}), 401
            
        # Capturar query params
        termino = request.args.get('termino', '').strip()
        severidad = request.args.get('severidad', 'todos').strip().lower()

        query = LogAuditoria.query

        # 1. Filtrar por nivel de severidad
        if severidad and severidad != 'todos' and severidad != 'todos los eventos':
            query = query.filter(LogAuditoria.nivel.ilike(severidad))

        # 2. BÚSQUEDA ROBUSTA letra por letra:
        if termino:
            # Buscamos coincidencias parciales usando ilike en placa, módulo o descripción
            filtro_busqueda = f"%{termino}%"
            query = query.filter(
                (LogAuditoria.placa.ilike(filtro_busqueda)) |
                (LogAuditoria.modulo.ilike(filtro_busqueda)) |
                (LogAuditoria.descripcion.ilike(filtro_busqueda))
            )
            
        # Ordenar cronológicamente (más recientes primero)
        historial = query.order_by(LogAuditoria.fecha.desc()).all()
        
        # 3. Serializar con claves estables y consistentes
        lista_logs = []
        for log in historial:
            lista_logs.append({
                "id": log.id,
                "fecha_hora": log.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "modulo": log.modulo,
                "nivel": log.nivel.lower() if log.nivel else "informativo", # Forzamos minúsculas para el Front
                "descripcion": log.descripcion,
                "usuario_id": log.usuario_id,
                "placa": log.placa if log.placa else "N/A"
            })
            
        return jsonify(lista_logs), 200

    except Exception as e:
        print(f"❌ Error crítico en GET /api/admin/logs: {str(e)}")
        return jsonify({"error": f"Error al recuperar auditoría: {str(e)}"}), 500