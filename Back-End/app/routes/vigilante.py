from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.vigilante_service import (
    abrir_turno,
    listar_turnos,
    cerrar_turno,
    registrar_entrada,
    registrar_salida,
    historial_turno,
    vehiculos_activos,
    resumen_turno,
    registrar_visitante,
    listar_visitantes,
    crear_novedad,
    listar_novedades,
    consultar_vehiculo
)

vigilante_bp = Blueprint(
    "vigilante",
    __name__
)


@vigilante_bp.route("/apertura-turno", methods=["POST"])
@jwt_required()
def apertura_turno():

    usuario_id = get_jwt_identity()

    resultado = abrir_turno(usuario_id)

    return jsonify({
        "mensaje": resultado
    }), 201


@vigilante_bp.route("/turnos", methods=["GET"])
@jwt_required()
def obtener_turnos():

    return jsonify(listar_turnos())


@vigilante_bp.route("/cierre-turno", methods=["POST"])
@jwt_required()
def cierre_turno():

    usuario_id = get_jwt_identity()

    resultado = cerrar_turno(usuario_id)

    if resultado is None:
        return jsonify({
            "error": "No existe un turno activo"
        }), 404

    return jsonify({
        "mensaje": resultado
    }), 200


@vigilante_bp.route("/entrada", methods=["POST"])
@jwt_required()
def entrada():

    usuario_id = get_jwt_identity()

    data = request.get_json()
    placa = data.get("placa")

    resultado = registrar_entrada(usuario_id, placa)

    if "error" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado), 201


@vigilante_bp.route("/salida", methods=["POST"])
@jwt_required()
def salida():

    usuario_id = get_jwt_identity()

    data = request.get_json()
    placa = data.get("placa")

    resultado = registrar_salida(usuario_id, placa)

    if "error" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado), 201


@vigilante_bp.route("/historial-turno", methods=["GET"])
@jwt_required()
def obtener_historial_turno():

    usuario_id = get_jwt_identity()

    resultado = historial_turno(usuario_id)

    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify(resultado), 404

    return jsonify(resultado), 200

@vigilante_bp.route("/vehiculos-activos", methods=["GET"])
@jwt_required()
def obtener_vehiculos_activos():

    usuario_id = get_jwt_identity()

    resultado = vehiculos_activos(usuario_id)

    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify(resultado), 404

    return jsonify(resultado), 200

@vigilante_bp.route("/resumen-turno", methods=["GET"])
@jwt_required()
def obtener_resumen_turno():

    usuario_id = get_jwt_identity()

    resultado = resumen_turno(usuario_id)

    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify(resultado), 404

    return jsonify(resultado), 200

@vigilante_bp.route("/visitantes", methods=["POST"])
@jwt_required()
def crear_visitante():

    data = request.get_json()

    resultado = registrar_visitante(data)

    return jsonify(resultado), 201


@vigilante_bp.route("/visitantes", methods=["GET"])
@jwt_required()
def obtener_visitantes():

    resultado = listar_visitantes()

    return jsonify(resultado), 200

@vigilante_bp.route("/novedades", methods=["POST"])
@jwt_required()
def registrar_novedad():

    usuario_id = get_jwt_identity()

    data = request.get_json()

    descripcion = data.get("descripcion")

    if not descripcion:
        return jsonify({
            "error": "La descripción es obligatoria"
        }), 400

    resultado = crear_novedad(
        usuario_id,
        descripcion
    )

    return jsonify(resultado), 201

@vigilante_bp.route("/novedades", methods=["GET"])
@jwt_required()
def obtener_novedades():

    return jsonify(
        listar_novedades()
    ), 200

@vigilante_bp.route("/vehiculo/<placa>", methods=["GET"])
@jwt_required()
def obtener_vehiculo(placa):

    resultado = consultar_vehiculo(placa)

    if "error" in resultado:
        return jsonify(resultado), 404

    return jsonify(resultado), 200