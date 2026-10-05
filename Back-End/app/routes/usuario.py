from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.usuario_service import (
    obtener_mis_vehiculos,
    registrar_mi_vehiculo,
    obtener_historial,
    obtener_notificaciones,
    obtener_perfil,
    cambiar_password
)

from app.services.reserva_service import (
    crear_reserva,
    obtener_mis_reservas
)

from app.models.vehiculo import Vehiculo
from app.models.celda import Celda
from app.models.acceso import Acceso

usuario_bp = Blueprint(
    "usuario",
    __name__,
    url_prefix="/api/usuario"
)


@usuario_bp.route("/panel", methods=["GET"])
@jwt_required()
def panel():

    usuario_id = get_jwt_identity()

    total_vehiculos = Vehiculo.query.count()

    total_celdas = Celda.query.count()

    ocupadas = Celda.query.filter_by(ocupada=True).count()

    disponibles = total_celdas - ocupadas

    accesos = (
        Acceso.query
        .order_by(Acceso.fecha_hora.desc())
        .limit(5)
        .all()
    )

    actividad = []

    for acceso in accesos:

        actividad.append({
            "hora": acceso.fecha_hora.strftime("%H:%M"),
            "evento": f"{acceso.tipo_movimiento} - {acceso.placa}",
            "estado": "Correcto"
        })

    return jsonify({

        "usuario_id": usuario_id,

        "totalVehiculos": total_vehiculos,

        "cuposDisponibles": disponibles,

        "cuposOcupados": ocupadas,

        "estadoParqueadero":
            "Disponible" if disponibles > 0 else "Lleno",

        "ocupacion":
            round((ocupadas / total_celdas) * 100)
            if total_celdas > 0 else 0,

        "actividad": actividad

    }), 200

@usuario_bp.route("/vehiculos", methods=["GET"])
@jwt_required()
def mis_vehiculos():

    usuario_id = get_jwt_identity()

    return jsonify(
        obtener_mis_vehiculos(usuario_id)
    ), 200


@usuario_bp.route("/vehiculos", methods=["POST"])
@jwt_required()
def registrar_vehiculo():

    usuario_id = get_jwt_identity()

    data = request.get_json()

    resultado = registrar_mi_vehiculo(
        usuario_id,
        data
    )

    if "error" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado), 201

@usuario_bp.route("/historial", methods=["GET"])
@jwt_required()
def historial():

    usuario_id = get_jwt_identity()

    return jsonify(
        obtener_historial(usuario_id)
    ), 200

@usuario_bp.route("/notificaciones", methods=["GET"])
@jwt_required()
def notificaciones():

    return jsonify(
        obtener_notificaciones()
    ), 200


# ===============================
# RESERVAS
# ===============================

@usuario_bp.route("/reservas", methods=["POST"])
@jwt_required()
def registrar_reserva():

    usuario_id = get_jwt_identity()

    data = request.get_json()

    respuesta = crear_reserva(usuario_id, data)

    if "error" in respuesta:
        return jsonify(respuesta), 400

    return jsonify(respuesta), 201


@usuario_bp.route("/reservas", methods=["GET"])
@jwt_required()
def listar_reservas():

    usuario_id = get_jwt_identity()

    return jsonify(
        obtener_mis_reservas(usuario_id)
    )

@usuario_bp.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():

    return jsonify(
        obtener_perfil()
    )

@usuario_bp.route("/cambiar-password", methods=["PUT"])
@jwt_required()
def actualizar_password():

    data = request.get_json()

    return cambiar_password(
        data.get("password_actual"),
        data.get("password_nueva")
    )