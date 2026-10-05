"""
ParkLink - Servicio para la gestión integral de reservas de estacionamiento.
Capa de negocio (Service Layer).
"""

from datetime import datetime, timedelta
from app.database.database import db
from app.models.reserva import Reserva
from app.models.vehiculo import Vehiculo
from app.models.celda import Celda


def crear_reserva(usuario_id, data):
    """
    Crea una nueva reserva asociando usuario, vehículo y opcionalmente celda específica.
    """
    try:
        vehiculo_id = data.get("vehiculo_id")
        fecha = data.get("fecha")
        hora = data.get("hora")
        celda_id = data.get("celda_id")  # Opcional: ID o código de la celda elegida en el mapa

        if not vehiculo_id or not fecha or not hora:
            return {"error": "Los campos vehículo, fecha y hora son obligatorios."}

        # ==========================
        # 1. Validar vehículo
        # ==========================
        vehiculo = Vehiculo.query.filter_by(
            id=vehiculo_id,
            usuario_id=int(usuario_id)
        ).first()

        if not vehiculo:
            return {"error": "Vehículo no encontrado o no pertenece al usuario."}

        # ==========================
        # 2. Validar formato de fecha
        # ==========================
        try:
            fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Formato de fecha inválido. Use YYYY-MM-DD."}

        hoy = datetime.now().date()

        if fecha_reserva < hoy:
            return {"error": "No puedes reservar en fechas pasadas."}

        if fecha_reserva > hoy + timedelta(days=7):
            return {"error": "Solo puedes reservar con un máximo de 7 días de anticipación."}

        # ==========================
        # 3. Validar formato de hora y horario laboral
        # ==========================
        try:
            hora_reserva = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return {"error": "Formato de hora inválido. Use HH:MM."}

        if hora_reserva.hour < 6 or hora_reserva.hour > 20:
            return {"error": "Las reservas solo están disponibles entre las 06:00 y las 20:00."}

        # ==========================
        # 4. Validar reservas pendientes existentes
        # ==========================
        reserva_existente = Reserva.query.filter_by(
            usuario_id=int(usuario_id),
            estado="Pendiente"
        ).first()

        if reserva_existente:
            return {"error": "Ya tienes una reserva activa o pendiente en el sistema."}

        vehiculo_reservado = Reserva.query.filter_by(
            vehiculo_id=vehiculo.id,
            estado="Pendiente"
        ).first()

        if vehiculo_reservado:
            return {"error": "Este vehículo ya cuenta con una reserva pendiente."}

        # ==========================
        # 5. Validar disponibilidad de Celda (si se especificó celda_id)
        # ==========================
        celda_obj = None
        if celda_id:
            celda_obj = Celda.query.filter(
                (Celda.id == celda_id) | (Celda.codigo_celda == str(celda_id).upper())
            ).first()

            if not celda_obj:
                return {"error": "La celda seleccionada no existe."}

            # Validar si la celda está libre o si ya tiene una reserva pendiente a esa fecha/hora
            if getattr(celda_obj, "ocupada", False) or getattr(celda_obj, "estado", "") == "ocupado":
                return {"error": f"La celda {celda_obj.codigo_celda} está actualmente ocupada."}

            reserva_celda_solape = Reserva.query.filter_by(
                celda_id=celda_obj.id,
                fecha=fecha_reserva,
                estado="Pendiente"
            ).first()

            if reserva_celda_solape:
                return {"error": f"La celda {celda_obj.codigo_celda} ya está reservada para la fecha seleccionada."}

        # ==========================
        # 6. Crear y Persistir Reserva
        # ==========================
        nueva_reserva = Reserva(
            usuario_id=int(usuario_id),
            vehiculo_id=vehiculo.id,
            fecha=fecha_reserva,
            hora=hora_reserva,
            estado="Pendiente"
        )

        if celda_obj and hasattr(nueva_reserva, "celda_id"):
            nueva_reserva.celda_id = celda_obj.id
            # Actualizar estado de la celda
            if hasattr(celda_obj, "estado"):
                celda_obj.estado = "reservado"

        db.session.add(nueva_reserva)
        db.session.commit()

        return {
            "mensaje": "Reserva creada correctamente.",
            "reserva": {
                "id": nueva_reserva.id,
                "placa": vehiculo.placa,
                "fecha": fecha_reserva.strftime("%Y-%m-%d"),
                "hora": hora_reserva.strftime("%H:%M"),
                "celda": celda_obj.codigo_celda if celda_obj else "Asignación Automática",
                "estado": nueva_reserva.estado
            }
        }

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en crear_reserva: {str(e)}")
        return {"error": f"Error interno al procesar la reserva: {str(e)}"}


def obtener_mis_reservas(usuario_id):
    """
    Obtiene el historial de reservas de un usuario específico.
    """
    try:
        reservas = Reserva.query.filter_by(
            usuario_id=int(usuario_id)
        ).order_by(
            Reserva.fecha.desc(),
            Reserva.hora.desc()
        ).all()

        resultado = []

        for r in reservas:
            vehiculo = Vehiculo.query.get(r.vehiculo_id)
            celda = Celda.query.get(r.celda_id) if hasattr(r, "celda_id") and r.celda_id else None

            resultado.append({
                "id": r.id,
                "placa": vehiculo.placa if vehiculo else "N/A",
                "vehiculo_info": f"{getattr(vehiculo, 'marca', '')} {getattr(vehiculo, 'modelo', '')}".strip() if vehiculo else "N/A",
                "celda": celda.codigo_celda if celda else "Sin asignar",
                "fecha": r.fecha.strftime("%Y-%m-%d") if r.fecha else "N/A",
                "hora": r.hora.strftime("%H:%M") if r.hora else "N/A",
                "estado": getattr(r, "estado", "Pendiente")
            })

        return resultado

    except Exception as e:
        print(f"❌ Error en obtener_mis_reservas: {str(e)}")
        return []


def cancelar_reserva(usuario_id, reserva_id):
    """
    Permite a un usuario cancelar una reserva pendiente y liberar la celda asociada.
    """
    try:
        reserva = Reserva.query.filter_by(
            id=reserva_id,
            usuario_id=int(usuario_id)
        ).first()

        if not reserva:
            return {"error": "Reserva no encontrada."}

        if reserva.estado != "Pendiente":
            return {"error": f"No se puede cancelar una reserva con estado '{reserva.estado}'."}

        reserva.estado = "Cancelada"

        # Liberar celda asociada si existía
        if hasattr(reserva, "celda_id") and reserva.celda_id:
            celda = Celda.query.get(reserva.celda_id)
            if celda:
                if hasattr(celda, "estado"):
                    celda.estado = "libre"
                if hasattr(celda, "ocupada"):
                    celda.ocupada = False

        db.session.commit()

        return {"mensaje": "Reserva cancelada exitosamente."}

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en cancelar_reserva: {str(e)}")
        return {"error": f"Error al cancelar la reserva: {str(e)}"}


def listar_todas_las_reservas_admin():
    """
    Retorna el listado completo de reservas para el mapa de control y administradores.
    """
    try:
        reservas = Reserva.query.order_by(Reserva.fecha.desc(), Reserva.hora.desc()).all()
        resultado = []

        for r in reservas:
            vehiculo = Vehiculo.query.get(r.vehiculo_id)
            celda = Celda.query.get(r.celda_id) if hasattr(r, "celda_id") and r.celda_id else None

            resultado.append({
                "id": r.id,
                "usuario_id": r.usuario_id,
                "placa": vehiculo.placa if vehiculo else "N/A",
                "celda_codigo": celda.codigo_celda if celda else "N/A",
                "fecha": r.fecha.strftime("%Y-%m-%d") if r.fecha else "N/A",
                "hora": r.hora.strftime("%H:%M") if r.hora else "N/A",
                "estado": r.estado
            })

        return resultado

    except Exception as e:
        print(f"❌ Error en listar_todas_las_reservas_admin: {str(e)}")
        return []