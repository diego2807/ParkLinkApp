from datetime import datetime, timedelta
from flask import send_file, jsonify, current_app
from app.services.reportes_service import ReportesService

# Importaciones de los modelos de la aplicación
try:
    from app.models.usuario import Usuario
    from app.models.vehiculo import Vehiculo
    from app.models.acceso import Acceso
    from app.models.reserva import Reserva
except ImportError:
    pass


def _obtener_fecha_corte(rango):
    """
    Calcula la fecha de corte basada en el rango solicitado.
    Rida los períodos: 'semana', 'mes', 'anio', 'todos'.
    """
    ahora = datetime.now()
    rango_lower = str(rango).lower()

    if rango_lower == 'semana':
        return ahora - timedelta(days=7)
    elif rango_lower == 'mes':
        return ahora - timedelta(days=30)
    elif rango_lower == 'anio':
        return ahora - timedelta(days=365)
    elif rango_lower == 'todos':
        return None
    
    # Por defecto 'semana'
    return ahora - timedelta(days=7)


def _obtener_datos_consolidados(rango="semana"):
    """
    Función auxiliar privada para extraer el historial de la base de datos
    filtrado por fecha/rango y formatearlo en diccionarios Python.
    """
    datos = {
        'usuarios': [],
        'vehiculos': [],
        'accesos': [],
        'reservas': []
    }

    fecha_corte = _obtener_fecha_corte(rango)

    try:
        # 1. Consultar Usuarios
        if 'Usuario' in globals():
            query_u = Usuario.query
            if fecha_corte and hasattr(Usuario, 'created_at'):
                query_u = query_u.filter(Usuario.created_at >= fecha_corte)
            usuarios_db = query_u.all()
        else:
            usuarios_db = []

        for u in usuarios_db:
            datos['usuarios'].append({
                'id': getattr(u, 'id', 'N/A'),
                'nombre': getattr(u, 'nombre', getattr(u, 'nombre_completo', 'N/A')),
                'correo': getattr(u, 'correo', getattr(u, 'email', 'N/A')),
                'documento': getattr(u, 'documento', getattr(u, 'numero_documento', 'N/A')),
                'rol': getattr(u, 'rol', 'N/A'),
                'estado': 'Activo' if getattr(u, 'estado', True) else 'Inactivo'
            })

        # 2. Consultar Vehículos
        if 'Vehiculo' in globals():
            query_v = Vehiculo.query
            if fecha_corte and hasattr(Vehiculo, 'created_at'):
                query_v = query_v.filter(Vehiculo.created_at >= fecha_corte)
            vehiculos_db = query_v.all()
        else:
            vehiculos_db = []

        for v in vehiculos_db:
            propietario_nombre = 'N/A'
            propietario_doc = 'N/A'
            if hasattr(v, 'usuario') and v.usuario:
                propietario_nombre = getattr(v.usuario, 'nombre', 'N/A')
                propietario_doc = getattr(v.usuario, 'documento', 'N/A')

            datos['vehiculos'].append({
                'id': getattr(v, 'id', 'N/A'),
                'placa': getattr(v, 'placa', 'N/A'),
                'tipo': getattr(v, 'tipo', getattr(v, 'tipo_vehiculo', 'N/A')),
                'propietario': propietario_nombre,
                'documento_propietario': propietario_doc,
                'estado': getattr(v, 'estado', 'Registrado')
            })

        # 3. Consultar Historial de Accesos / Movimientos
        if 'Acceso' in globals():
            query_a = Acceso.query
            if fecha_corte:
                if hasattr(Acceso, 'fecha_entrada'):
                    query_a = query_a.filter(Acceso.fecha_entrada >= fecha_corte)
                elif hasattr(Acceso, 'hora_entrada'):
                    query_a = query_a.filter(Acceso.hora_entrada >= fecha_corte)
                elif hasattr(Acceso, 'created_at'):
                    query_a = query_a.filter(Acceso.created_at >= fecha_corte)
            accesos_db = query_a.order_by(Acceso.id.desc()).all()
        else:
            accesos_db = []

        for a in accesos_db:
            usuario_nombre = 'N/A'
            usuario_doc = 'N/A'
            if hasattr(a, 'usuario') and a.usuario:
                usuario_nombre = getattr(a.usuario, 'nombre', 'N/A')
                usuario_doc = getattr(a.usuario, 'documento', 'N/A')

            datos['accesos'].append({
                'id': getattr(a, 'id', 'N/A'),
                'usuario': usuario_nombre,
                'documento': usuario_doc,
                'placa': getattr(a, 'placa', 'N/A'),
                'tipo_vehiculo': getattr(a, 'tipo_vehiculo', getattr(a, 'tipo', 'N/A')),
                'fecha_entrada': getattr(a, 'fecha_entrada', getattr(a, 'hora_entrada', 'N/A')),
                'fecha_salida': getattr(a, 'fecha_salida', getattr(a, 'hora_salida', None)),
                'estado': getattr(a, 'estado', 'Completado')
            })

        # 4. Consultar Historial de Reservas
        if 'Reserva' in globals():
            query_r = Reserva.query
            if fecha_corte:
                if hasattr(Reserva, 'fecha_reserva'):
                    query_r = query_r.filter(Reserva.fecha_reserva >= fecha_corte)
                elif hasattr(Reserva, 'created_at'):
                    query_r = query_r.filter(Reserva.created_at >= fecha_corte)
            reservas_db = query_r.all()
        else:
            reservas_db = []

        for r in reservas_db:
            usuario_nombre = getattr(r.usuario, 'nombre', 'N/A') if hasattr(r, 'usuario') and r.usuario else 'N/A'
            
            datos['reservas'].append({
                'id': getattr(r, 'id', 'N/A'),
                'usuario': usuario_nombre,
                'placa': getattr(r, 'placa', 'N/A'),
                'celda': getattr(r, 'celda_id', getattr(r, 'numero_celda', 'N/A')),
                'fecha_reserva': getattr(r, 'fecha_reserva', getattr(r, 'created_at', 'N/A')),
                'estado': getattr(r, 'estado', 'N/A')
            })

    except Exception as e:
        current_app.logger.error(f"Error al extraer historial de la BD: {str(e)}")

    return datos


def generar_reporte_historial(formato="excel", rango="semana"):
    """
    Controlador principal invocado por el Blueprint de reportes.
    
    Parámetros:
        formato (str): 'excel' o 'pdf'
        rango (str): 'semana', 'mes', 'anio' o 'todos'
    """
    try:
        # 1. Obtener información filtrada por el rango solicitado desde la Base de Datos
        datos_consolidados = _obtener_datos_consolidados(rango=rango)

        formato_clean = str(formato).lower()
        rango_clean = str(rango).lower()
        fecha_actual = datetime.now().strftime("%Y-%m-%d")

        # 2. Validar y procesar según el formato
        if formato_clean == 'excel':
            buffer_excel = ReportesService.generar_excel_completo(datos_consolidados)
            
            if hasattr(buffer_excel, 'seek'):
                buffer_excel.seek(0)

            return send_file(
                buffer_excel,
                as_attachment=True,
                download_name=f"reporte_parklink_{rango_clean}_{fecha_actual}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        elif formato_clean == 'pdf':
            buffer_pdf = ReportesService.generar_pdf_completo(datos_consolidados)
            
            if hasattr(buffer_pdf, 'seek'):
                buffer_pdf.seek(0)

            return send_file(
                buffer_pdf,
                as_attachment=True,
                download_name=f"reporte_parklink_{rango_clean}_{fecha_actual}.pdf",
                mimetype='application/pdf'
            )

        else:
            return jsonify({
                'estado': 'Error',
                'mensaje': f'El formato "{formato}" no es válido. Utilice "pdf" o "excel".'
            }), 400

    except Exception as e:
        current_app.logger.error(f"Error en generar_reporte_historial ({formato}, {rango}): {str(e)}")
        return jsonify({
            'estado': 'Error',
            'mensaje': 'Ocurrió un fallo interno al generar el reporte solicitado.',
            'detalle': str(e)
        }), 500