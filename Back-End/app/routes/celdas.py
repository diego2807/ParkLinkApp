"""
ParkLink - Rutas para la gestión, auditoría y control en tiempo real del estado de las celdas del parqueadero.
Blueprint: celdas_bp
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.database import db
from app.models.celda import Celda
from app.models.usuario import Usuario
from app import socketio  # Instancia global de Flask-SocketIO

celdas_bp = Blueprint("celdas", __name__)


def notificar_cambio_celda(celda):
    """
    Función auxiliar para emitir eventos WebSocket a todos los clientes conectados
    (Paneles de Administración y Vigilancia) cada vez que una celda cambia de estado.
    """
    try:
        estado_calculado = getattr(celda, "estado", None)
        if not estado_calculado:
            estado_calculado = "ocupado" if getattr(celda, "ocupada", False) else "libre"

        payload = {
            "id": celda.id,
            "codigo": getattr(celda, "codigo_celda", f"C-{celda.id}"),
            "puesto": getattr(celda, "codigo_celda", f"C-{celda.id}"),
            "planta": getattr(celda, "planta", 1),
            "estado": estado_calculado,
            "tipoVehiculo": getattr(celda, "tipo_celda", "carro"),
            "ocupada": getattr(celda, "ocupada", estado_calculado == "ocupado"),
            "placa": getattr(celda, "placa", None),
            "usuario": getattr(celda, "usuario", None),
            "marca": getattr(celda, "marca", None),
            "modelo": getattr(celda, "modelo", None),
            "colorHex": getattr(celda, "color_hex", "#2563eb"),
            "horaIngreso": getattr(celda, "hora_ingreso", None)
        }
        
        # Emisión del evento 'celda_actualizada' a todos los sockets conectados
        socketio.emit("celda_actualizada", payload)
        print(f"⚡ [WebSocket] Evento 'celda_actualizada' emitido para celda {payload['codigo']}")
    except Exception as err:
        print(f"⚠️ Error al emitir evento SocketIO: {str(err)}")


# ── 1. OBTENER MAPA DE CELDAS (Soporta filtrado por Planta / Sótano) ─────────
@celdas_bp.route("/celdas", methods=["GET"])
@jwt_required()
def obtener_mapa_celdas():
    """
    Retorna el estado actual de todas las celdas registradas en el sistema ParkLink.
    Query params opcionales: ?planta=1 o ?planta=2
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        # Filtrar opcionalmente por planta/sótano
        planta_param = request.args.get("planta", type=int)

        query = Celda.query
        if planta_param is not None and hasattr(Celda, "planta"):
            query = query.filter(Celda.planta == planta_param)

        celdas = query.order_by(Celda.codigo_celda.asc()).all()

        resultado = []
        for c in celdas:
            # Determinación flexible del estado dinámico (libre, ocupado, reservado)
            estado_calculado = getattr(c, "estado", None)
            if not estado_calculado:
                estado_calculado = "ocupado" if getattr(c, "ocupada", False) else "libre"

            resultado.append({
                "id": c.id,
                "codigo": getattr(c, "codigo_celda", f"C-{c.id}"),
                "puesto": getattr(c, "codigo_celda", f"C-{c.id}"),
                "planta": getattr(c, "planta", 1),
                "estado": estado_calculado,
                "tipoVehiculo": getattr(c, "tipo_celda", "carro"),
                "ocupada": getattr(c, "ocupada", estado_calculado == "ocupado"),
                "placa": getattr(c, "placa", None),
                "usuario": getattr(c, "usuario", None),
                "marca": getattr(c, "marca", None),
                "modelo": getattr(c, "modelo", None),
                "colorHex": getattr(c, "color_hex", "#2563eb"),
                "horaIngreso": getattr(c, "hora_ingreso", None)
            })

        return jsonify({
            "status": "success",
            "planta": planta_param if planta_param else "todas",
            "total": len(resultado),
            "data": resultado
        }), 200

    except Exception as e:
        print(f"❌ Error en GET /celdas: {str(e)}")
        return jsonify({"error": f"Error interno al recuperar el mapa de celdas: {str(e)}"}), 500


# ── 2. REGISTRAR INGRESO MANUAL A UNA CELDA (POST /celdas/<id>/ocupar) ──────
@celdas_bp.route("/celdas/<int:celda_id>/ocupar", methods=["POST"])
@jwt_required()
def ocupar_celda(celda_id):
    """
    Registra el ingreso manual de un vehículo asignándolo a una celda disponible.
    Payload esperado: { "placa": "ABC123", "usuario": "Diego Plazas", "marca": "Toyota", "modelo": "Corolla", "color": "#2563eb" }
    """
    try:
        data = request.get_json(silent=True) or {}
        placa = data.get("placa")

        if not placa:
            return jsonify({"error": "La placa del vehículo es obligatoria."}), 400

        celda = Celda.query.get(celda_id)
        if not celda:
            return jsonify({"error": "La celda especificada no existe."}), 404

        estado_actual = getattr(celda, "estado", "ocupado" if getattr(celda, "ocupada", False) else "libre")
        if estado_actual == "ocupado":
            return jsonify({"error": f"La celda {getattr(celda, 'codigo_celda', celda_id)} ya se encuentra ocupada."}), 400

        hora_actual = datetime.now().strftime("%I:%M %p")

        # Actualizar atributos según esquema del modelo
        if hasattr(celda, "ocupada"):
            celda.ocupada = True
        if hasattr(celda, "estado"):
            celda.estado = "ocupado"

        if hasattr(celda, "placa"):
            celda.placa = placa.strip().upper()
        if hasattr(celda, "usuario"):
            celda.usuario = data.get("usuario", "Visitante / Sin Registro").strip()
        if hasattr(celda, "marca"):
            celda.marca = data.get("marca", "").strip()
        if hasattr(celda, "modelo"):
            celda.modelo = data.get("modelo", "").strip()
        if hasattr(celda, "color_hex"):
            celda.color_hex = data.get("color", "#2563eb")
        if hasattr(celda, "hora_ingreso"):
            celda.hora_ingreso = hora_actual

        db.session.commit()

        # ⚡ Emisión de evento WebSocket en tiempo real
        notificar_cambio_celda(celda)

        return jsonify({
            "status": "success",
            "message": f"Vehículo {placa.upper()} asignado con éxito a la celda {getattr(celda, 'codigo_celda', celda_id)}.",
            "celda": {
                "id": celda.id,
                "codigo": getattr(celda, "codigo_celda", f"C-{celda.id}"),
                "estado": "ocupado",
                "placa": getattr(celda, "placa", placa),
                "horaIngreso": hora_actual
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /celdas/{celda_id}/ocupar: {str(e)}")
        return jsonify({"error": f"Error al registrar el ingreso en la celda: {str(e)}"}), 500


# ── 3. LIBERAR CELDA / REGISTRAR SALIDA (POST /celdas/<id>/liberar) ────────
@celdas_bp.route("/celdas/<int:celda_id>/liberar", methods=["POST"])
@jwt_required()
def liberar_celda(celda_id):
    """
    Registra la salida de un vehículo y resetea la celda al estado 'libre'.
    """
    try:
        celda = Celda.query.get(celda_id)
        if not celda:
            return jsonify({"error": "La celda especificada no existe."}), 404

        # Limpieza de asignaciones
        if hasattr(celda, "ocupada"):
            celda.ocupada = False
        if hasattr(celda, "estado"):
            celda.estado = "libre"

        if hasattr(celda, "placa"):
            celda.placa = None
        if hasattr(celda, "usuario"):
            celda.usuario = None
        if hasattr(celda, "marca"):
            celda.marca = None
        if hasattr(celda, "modelo"):
            celda.modelo = None
        if hasattr(celda, "color_hex"):
            celda.color_hex = None
        if hasattr(celda, "hora_ingreso"):
            celda.hora_ingreso = None

        db.session.commit()

        # ⚡ Emisión de evento WebSocket en tiempo real
        notificar_cambio_celda(celda)

        return jsonify({
            "status": "success",
            "message": f"La celda {getattr(celda, 'codigo_celda', celda_id)} ha sido liberada correctamente.",
            "celda_id": celda_id,
            "nuevo_estado": "libre"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /celdas/{celda_id}/liberar: {str(e)}")
        return jsonify({"error": f"Error interno al liberar la celda: {str(e)}"}), 500


# ── 4. GESTIONAR RESERVA DE CELDA (PATCH /celdas/<id>/reserva) ──────────────
@celdas_bp.route("/celdas/<int:celda_id>/reserva", methods=["PATCH"])
@jwt_required()
def toggle_reserva_celda(celda_id):
    """
    Alterna el estado de una celda entre 'libre' y 'reservado'.
    """
    try:
        celda = Celda.query.get(celda_id)
        if not celda:
            return jsonify({"error": "La celda especificada no existe."}), 404

        estado_actual = getattr(celda, "estado", "libre")
        nuevo_estado = "libre" if estado_actual == "reservado" else "reservado"

        if hasattr(celda, "estado"):
            celda.estado = nuevo_estado
        if hasattr(celda, "ocupada"):
            celda.ocupada = (nuevo_estado == "reservado")

        if hasattr(celda, "hora_ingreso"):
            celda.hora_ingreso = "Reserva Activa" if nuevo_estado == "reservado" else None

        db.session.commit()

        # ⚡ Emisión de evento WebSocket en tiempo real
        notificar_cambio_celda(celda)

        return jsonify({
            "status": "success",
            "message": f"Celda {getattr(celda, 'codigo_celda', celda_id)} marcada como {nuevo_estado}.",
            "celda_id": celda_id,
            "estado": nuevo_estado
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en PATCH /celdas/{celda_id}/reserva: {str(e)}")
        return jsonify({"error": f"Error al gestionar la reserva de la celda: {str(e)}"}), 500


# ── 5. CAMBIAR ESTADO GENÉRICO (PUT /celdas/<id>/estado) ────────────────────
@celdas_bp.route("/celdas/<int:celda_id>/estado", methods=["PUT"])
@jwt_required()
def cambiar_estado_celda(celda_id):
    """
    Permite al administrador o vigilante conmutar genéricamente la ocupación de una celda.
    """
    try:
        data = request.get_json(silent=True) or {}
        nuevo_estado = data.get("ocupada")

        if nuevo_estado is None:
            return jsonify({"error": "El campo 'ocupada' (booleano) es obligatorio."}), 400

        celda = Celda.query.get(celda_id)
        if not celda:
            return jsonify({"error": "La celda especificada no existe."}), 404

        celda.ocupada = bool(nuevo_estado)
        if hasattr(celda, "estado"):
            celda.estado = "ocupado" if celda.ocupada else "libre"

        db.session.commit()

        # ⚡ Emisión de evento WebSocket en tiempo real
        notificar_cambio_celda(celda)

        accion = "ocupada" if celda.ocupada else "liberada"
        return jsonify({
            "message": f"La celda {getattr(celda, 'codigo_celda', celda_id)} ha sido {accion} con éxito.",
            "celda": {
                "id": celda.id,
                "codigo_celda": getattr(celda, "codigo_celda", f"C-{celda.id}"),
                "ocupada": celda.ocupada
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en PUT /celdas/estado: {str(e)}")
        return jsonify({"error": f"Error al actualizar la celda: {str(e)}"}), 500


# ── 6. REGISTRAR NUEVA CELDA (POST /celdas) ─────────────────────────────────
@celdas_bp.route("/celdas", methods=["POST"])
@jwt_required()
def registrar_celda():
    """
    Permite al administrador dar de alta una nueva celda en el plano del parqueadero.
    """
    try:
        data = request.get_json(silent=True) or {}
        codigo_celda = data.get("codigo_celda") or data.get("codigo")
        tipo_celda = data.get("tipo_celda") or data.get("tipoVehiculo", "carro")
        planta = data.get("planta", 1)

        if not codigo_celda:
            return jsonify({"error": "El código de la celda es obligatorio."}), 400

        codigo_limpio = codigo_celda.strip().upper()
        tipo_limpio = tipo_celda.strip().lower()

        existe = Celda.query.filter_by(codigo_celda=codigo_limpio).first()
        if existe:
            return jsonify({"error": f"La celda {codigo_limpio} ya se encuentra registrada."}), 400

        nueva_celda = Celda(
            codigo_celda=codigo_limpio,
            tipo_celda=tipo_limpio,
            ocupada=False
        )

        if hasattr(nueva_celda, "planta"):
            nueva_celda.planta = planta
        if hasattr(nueva_celda, "estado"):
            nueva_celda.estado = "libre"

        db.session.add(nueva_celda)
        db.session.commit()

        # ⚡ Emisión de evento WebSocket en tiempo real
        notificar_cambio_celda(nueva_celda)

        return jsonify({
            "message": f"Celda {codigo_limpio} registrada con éxito.",
            "celda": {
                "id": nueva_celda.id,
                "codigo_celda": nueva_celda.codigo_celda,
                "tipo_celda": nueva_celda.tipo_celda
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /celdas: {str(e)}")
        return jsonify({"error": f"Error interno al registrar la celda: {str(e)}"}), 500


# ── 7. ELIMINAR CELDA (DELETE /celdas/<id>) ──────────────────────────────────
@celdas_bp.route("/celdas/<int:celda_id>", methods=["DELETE"])
@jwt_required()
def eliminar_celda(celda_id):
    """
    Elimina físicamente una celda de la base de datos ParkLink.
    """
    try:
        celda = Celda.query.get(celda_id)
        if not celda:
            return jsonify({"error": "La celda especificada no existe."}), 404

        codigo = getattr(celda, "codigo_celda", celda_id)
        db.session.delete(celda)
        db.session.commit()

        # Emisión de eliminación mediante SocketIO
        socketio.emit("celda_eliminada", {"id": celda_id, "codigo": codigo})

        return jsonify({"message": f"Celda {codigo} eliminada correctamente del sistema."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en DELETE /celdas/{celda_id}: {str(e)}")
        return jsonify({"error": f"Error al eliminar la celda: {str(e)}"}), 500