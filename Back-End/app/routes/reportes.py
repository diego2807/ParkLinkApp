from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.controllers import reportes_controller
from app.middlewares.roles import rol_requerido

# Declaración del Blueprint para los reportes
reportes_bp = Blueprint("reportes_bp", __name__)


@reportes_bp.route("/exportar", methods=["GET", "OPTIONS"])
def exportar_reporte_historial():
    """Ruta unificada para la descarga de informes del sistema en Excel (.xlsx) o PDF (.pdf).

    Acepta parámetros de consulta:
    - formato: 'excel' | 'pdf' (default: 'excel')
    - rango: 'semana' | 'mes' | 'anio' | 'todos' (default: 'semana')
    """
    # Manejo del Preflight CORS (soluciona el error 404 en peticiones OPTIONS)
    if request.method == "OPTIONS":
        return "", 200

    # Para peticiones GET ejecutamos la autenticación y autorización
    @jwt_required()
    @rol_requerido("administrador")
    def procesar_descarga():
        try:
            # Obtención de parámetros enviados desde el Frontend (reportesService.js)
            formato = request.args.get("formato", "excel").lower()
            rango = request.args.get("rango", "semana").lower()

            # Validación básica de formato
            if formato not in ["excel", "pdf"]:
                return jsonify({
                    "estado": "Error",
                    "mensaje": "Formato no válido. Debe ser 'excel' o 'pdf'."
                }), 400

            # Pasa tanto el formato como el rango al controlador
            return reportes_controller.generar_reporte_historial(formato=formato, rango=rango)

        except Exception as e:
            return jsonify({
                "estado": "Error",
                "mensaje": f"No se pudo procesar la solicitud de reporte en {formato.upper()}.",
                "detalle": str(e)
            }), 500

    return procesar_descarga()


# Mantener compatibilidad con endpoints antiguos por si se requieren en otros módulos
@reportes_bp.route("/historial/excel", methods=["GET", "OPTIONS"])
def descargar_excel_historial():
    if request.method == "OPTIONS":
        return "", 200

    @jwt_required()
    @rol_requerido("administrador")
    def ejecutar():
        try:
            rango = request.args.get("rango", "semana").lower()
            return reportes_controller.generar_reporte_historial(formato="excel", rango=rango)
        except Exception as e:
            return jsonify({
                "estado": "Error",
                "mensaje": "No se pudo procesar la solicitud de reporte en Excel.",
                "detalle": str(e)
            }), 500

    return ejecutar()


@reportes_bp.route("/historial/pdf", methods=["GET", "OPTIONS"])
def descargar_pdf_historial():
    if request.method == "OPTIONS":
        return "", 200

    @jwt_required()
    @rol_requerido("administrador")
    def ejecutar():
        try:
            rango = request.args.get("rango", "semana").lower()
            return reportes_controller.generar_reporte_historial(formato="pdf", rango=rango)
        except Exception as e:
            return jsonify({
                "estado": "Error",
                "mensaje": "No se pudo procesar la solicitud de reporte en PDF.",
                "detalle": str(e)
            }), 500

    return ejecutar()