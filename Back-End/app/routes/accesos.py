# app/routes/accesos.py
"""
ParkLink - Controlador independiente para el historial y registro de Accesos.
Blueprint: accesos_bp
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.database import db
from app.models.acceso import Acceso
from app.models.usuario import Usuario
from app.models.log_auditoria import LogAuditoria  # 🌟 Importamos tu modelo de logs
from datetime import datetime, timezone

accesos_bp = Blueprint("accesos", __name__)

# ── 1. OBTENER HISTORIAL (Para la barra lateral de Accesos.jsx) ──────────────
@accesos_bp.route("/historial", methods=["GET"])
@jwt_required()
def obtener_historial():
    """
    Retorna el listado cronológico de entradas y salidas de ParkLink.
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        # Validar el rol de manera elástica
        rol_actual = datos_token.get('rol') if isinstance(datos_token, dict) else None
        if not rol_actual:
            user_jwt_id = datos_token.get('id') if isinstance(datos_token, dict) else datos_token
            current_user = Usuario.query.get(int(user_jwt_id))
            if current_user:
                rol_actual = current_user.rol.value

        # Consultar accesos ordenados cronológicamente
        registros = Acceso.query.order_by(Acceso.fecha_hora.desc()).all()
        
        resultado = []
        for reg in registros:
            fecha_str = reg.fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if reg.fecha_hora else "Sin fecha"
            resultado.append({
                "id": reg.id,
                "placa": reg.placa,
                "tipo_movimiento": reg.tipo_movimiento,
                "tipo_vehiculo": reg.tipo_vehiculo,
                "tipo_usuario": reg.tipo_usuario,
                "celda_asignada": reg.celda_asignada or "N/A",
                "fecha_hora": fecha_str
            })

        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Error en GET /historial: {str(e)}")
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500


# ── 2. REGISTRAR ENTRADA/SALIDA (Mantiene tu ruta exacta con Auditoría) ──
@accesos_bp.route("/registrar-acceso", methods=["POST"])  # 🌟 Sincronizado con el Front anterior
@jwt_required()
def registrar_acceso():
    """
    Guarda un nuevo registro de portería en la base de datos y genera la traza en la Bitácora.
    """
    try:
        # Extraer quién es el operador/guarda autenticado desde el JWT
        datos_token = get_jwt_identity()
        usuario_id_operador = None
        if isinstance(datos_token, dict):
            usuario_id_operador = datos_token.get('id')
        else:
            usuario_id_operador = int(datos_token) if datos_token else None

        data = request.get_json(silent=True) or {}
        placa = data.get('placa', '').strip().upper()
        tipo_movimiento = data.get('tipo_movimiento')  # "Entrada" o "Salida"
        tipo_vehiculo = data.get('tipo_vehiculo', 'Automóvil')
        tipo_usuario = data.get('tipo_usuario', 'Funcionario')
        celda_asignada = data.get('celda_assigned') or data.get('celda_asignada')

        if not placa or not tipo_movimiento:
            return jsonify({"error": "Placa y tipo de movimiento son campos obligatorios."}), 400

        nuevo_acceso = Acceso(
            placa=placa,
            tipo_movimiento=tipo_movimiento,
            tipo_vehiculo=tipo_vehiculo,
            tipo_usuario=tipo_usuario,
            celda_asignada=celda_asignada if celda_asignada else "N/A",
            fecha_hora=datetime.now(timezone.utc)
        )
        db.session.add(nuevo_acceso)

        # 🌟 2. DISPARADOR DE AUDITORÍA AUTOMÁTICA (Inyecta el log para la bitácora)
        # Construimos un mensaje descriptivo que incluya el tipo de usuario y el espacio
        if tipo_movimiento.lower() == "salida":
            descripcion_log = f"Salida confirmada para vehículo tipo {tipo_vehiculo}."
        else:
            descripcion_log = f"Ingreso autorizado para {tipo_usuario} en la celda {nuevo_acceso.celda_asignada}."

        nuevo_log = LogAuditoria(
            nivel="informativo",
            modulo="Accesos",
            descripcion=descripcion_log,
            usuario_id=usuario_id_operador,
            placa=placa  # Esto permite enlazar tu barra de búsqueda instantánea
        )
        db.session.add(nuevo_log)

        # Confirmamos ambas transacciones juntas de forma segura
        db.session.commit()

        return jsonify({
            "message": f"Registro de {tipo_movimiento} completado con éxito para la placa {placa}.",
            "acceso_id": nuevo_acceso.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /registrar-acceso: {str(e)}")
        return jsonify({"error": f"Error interno al guardar: {str(e)}"}), 500