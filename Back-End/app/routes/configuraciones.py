# app/routes/configuraciones.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.database.database import db
from app.models.configuracion import Configuracion

config_bp = Blueprint('config_bp', __name__)

@config_bp.route('/config', methods=['GET'])
@jwt_required()
def obtener_configuracion():
    try:
        # Intentamos obtener el único registro de configuración global
        config = Configuracion.query.first()
        
        # Si la base de datos está vacía (primera ejecución), creamos la inicial por defecto
        if not config:
            config = Configuracion()
            db.session.add(config)
            db.session.commit()
            
        # Construimos el diccionario plano con los tipos de datos nativos correctos
        respuesta_estructurada = {
            "id": config.id,
            "hora_apertura": str(config.hora_apertura),
            "hora_cierre": str(config.hora_cierre),
            "permitir_festivos": bool(config.permitir_festivos),
            "tiempo_maximo": int(config.tiempo_maximo),
            "accion_exceso": str(config.accion_exceso),
            "celdas_admin": int(config.celdas_admin),
            "celdas_operativas": int(config.celdas_operativas),
            "celdas_movilidad": int(config.celdas_movilidad)
        }
            
        return jsonify({
            "status": "success",
            "data": respuesta_estructurada
        }), 200

    except Exception as e:
        print(f"❌ Error crítico en GET /api/admin/config: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Error interno del servidor al leer parámetros: {str(e)}"
        }), 500


@config_bp.route('/config', methods=['PUT', 'POST'])
@jwt_required()
def actualizar_configuracion():
    try:
        config = Configuracion.query.first()
        if not config:
            config = Configuracion()
            db.session.add(config)

        datos = request.get_json()
        if not datos:
            return jsonify({"status": "error", "message": "No se proporcionaron datos para actualizar"}), 400

        # Mapeo estricto y actualización del modelo basándonos en el payload de React
        if 'hora_apertura' in datos:
            config.hora_apertura = str(datos['hora_apertura'])
            
        if 'hora_cierre' in datos:
            config.hora_cierre = str(datos['hora_cierre'])
            
        if 'permitir_festivos' in datos:
            config.permitir_festivos = bool(datos['permitir_festivos'])
            
        if 'tiempo_maximo' in datos:
            config.tiempo_maximo = int(datos['tiempo_maximo'])
            
        if 'accion_exceso' in datos:
            config.accion_exceso = str(datos['accion_exceso'])
            
        # Actualización de la distribución de cupos y celdas
        if 'celdas_admin' in datos:
            config.celdas_admin = int(datos['celdas_admin'])
            
        if 'celdas_operativas' in datos:
            config.celdas_operativas = int(datos['celdas_operativas'])
            
        if 'celdas_movilidad' in datos:
            config.celdas_movilidad = int(datos['celdas_movilidad'])

        db.session.commit()

        # Retornamos la data fresca actualizada para que React refresque sus estados sin parpadeos
        return jsonify({
            "status": "success",
            "message": "Parámetros del sistema ParkLink actualizados con éxito",
            "data": {
                "hora_apertura": config.hora_apertura,
                "hora_cierre": config.hora_cierre,
                "permitir_festivos": config.permitir_festivos,
                "tiempo_maximo": config.tiempo_maximo,
                "accion_exceso": config.accion_exceso,
                "celdas_admin": config.celdas_admin,
                "celdas_operativas": config.celdas_operativas,
                "celdas_movilidad": config.celdas_movilidad
            }
        }), 200

    except ValueError:
        return jsonify({
            "status": "error", 
            "message": "Formato inválido: Las celdas y tiempos deben ser valores numéricos enteros."
        }), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error crítico en PUT /api/admin/config: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"No se pudo guardar la configuración: {str(e)}"
        }), 500