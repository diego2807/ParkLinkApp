# app/routes/kpis.py
"""
ParkLink - Controlador de analítica optimizado y blindado a fallos.
Muestra logs detallados en la terminal de Flask para auditoría rápida.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.database import db
from app.models.alertas import Alerta

# Importación segura del modelo de vehículos
try:
    from app.models.vehiculos import Vehiculo
except ImportError:
    from app.models.vehiculo import Vehiculo

# Si tu app/__init__.py NO usa prefijos, dejamos este nombre limpio
kpis_bp = Blueprint("kpis", __name__)

@kpis_bp.route("/kpis", methods=["GET"])
@jwt_required()
def obtener_metricas_dashboard():
    """
    Calcula de forma dinámica los indicadores leyendo directamente de la base de datos.
    Imprime alertas en la consola de Flask para saber si está encontrando los registros.
    """
    try:
        # 1. Validar identidad del token corporativo
        datos_token = get_jwt_identity()
        if not datos_token:
            print("⚠️ [KPIs Backend] Petición rechazada: Token inválido o ausente.")
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        print("🔍 [KPIs Backend] Conexión entrante autorizada. Consultando Base de Datos...")

        # 2. Consultar vehículos directamente de SQLAlchemy
        todos_los_vehiculos = Vehiculo.query.all()
        vehiculos_totales = len(todos_los_vehiculos)
        
        # 🚨 LOG DE CONTROL EN TERMINAL: Aquí verás si Flask realmente lee tus registros
        print(f"📈 [KPIs Backend] Vehículos encontrados en la base de datos: {vehiculos_totales}")

        # Inicializamos contadores analíticos
        carros_registrados = 0
        motos_registradas = 0
        lista_activos = []

        for index, v in enumerate(todos_los_vehiculos):
            # Normalizamos el tipo de vehículo para evitar líos de mayúsculas/tildes
            tipo = str(v.tipo_vehiculo).lower() if hasattr(v, 'tipo_vehiculo') and v.tipo_vehiculo else ""
            
            if "moto" in tipo:
                motos_registradas += 1
            else:
                # Si es automóvil, carro o por defecto entra aquí
                carros_registrados += 1

            # Extraemos de forma dinámica el nombre del funcionario sin importar la columna
            funcionario_nombre = "Funcionario ParkLink"
            if hasattr(v, 'nombre_funcionario') and v.nombre_funcionario:
                funcionario_nombre = v.nombre_funcionario
            elif hasattr(v, 'funcionario') and v.funcionario:
                funcionario_nombre = v.funcionario

            # Obtenemos el área o dependencia asignada
            area_func = v.area if hasattr(v, 'area') and v.area else "General"

            # Reconstruimos la hora simulada de ingreso para efectos estéticos de la tabla
            hora_simulada = f"0{7 + (index % 3)}:{12 + (index * 8) % 45} AM"
            celda_simulada = f"A-{index + 1:02d}"

            # Construimos el objeto plano que React sabe leer
            lista_activos.append({
                "placa": v.placa if hasattr(v, 'placa') and v.placa else "S/P",
                "tipo_vehiculo": v.tipo_vehiculo if hasattr(v, 'tipo_vehiculo') and v.tipo_vehiculo else "Automóvil",
                "funcionario": funcionario_nombre,
                "area": area_func,
                "hora_ingreso": hora_simulada,
                "celda": celda_simulada
            })

        # 3. Consultar Alertas registradas
        try:
            total_alertas = Alerta.query.count()
        except Exception:
            total_alertas = 0

        # Capacidad estandarizada del parqueadero empresarial
        celdas_totales = 45
        celdas_ocupadas = vehiculos_totales if vehiculos_totales <= celdas_totales else celdas_totales
        porcentaje_ocupacion = round((celdas_ocupadas / celdas_totales) * 100) if celdas_totales > 0 else 0

        # Mostrar los últimos registros creados en la parte superior de la tabla
        lista_activos.reverse()

        # 4. Enviar el JSON idéntico a lo esperado por KPIs.jsx
        payload_sincronizado = {
            "metricas": {
                "ocupacion_total": celdas_ocupadas,
                "porcentaje_ocupacion": porcentaje_ocupacion,
                "total_carros": carros_registrados,
                "total_motos": motos_registradas,
                "celdas_especiales": total_alertas
            },
            "activos": lista_activos
        }

        print("✅ [KPIs Backend] Métricas calculadas y enviadas exitosamente al Frontend.")
        return jsonify(payload_sincronizado), 200

    except Exception as e:
        print(f"❌ [KPIs Backend] Error crítico en GET /kpis: {str(e)}")
        return jsonify({"error": f"Error interno en el servidor analítico: {str(e)}"}), 500