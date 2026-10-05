from flask_jwt_extended import get_jwt_identity
from app.models.usuario import Usuario
from app.models.reserva import Reserva
from app.models.vehiculo import Vehiculo
from app.models.acceso import Acceso
from app.database.database import db


def obtener_mis_vehiculos(usuario_id):

    vehiculos = Vehiculo.query.filter_by(
        usuario_id=int(usuario_id)
    ).all()

    return [
        {
            "id": v.id,
            "placa": v.placa,
            "tipo_vehiculo": v.tipo_vehiculo,
            "marca": v.marca,
            "color": v.color,
            "area": v.area
        }
        for v in vehiculos
    ]


def registrar_mi_vehiculo(usuario_id, data):

    placa = data["placa"].upper()

    existe = Vehiculo.query.filter_by(
        placa=placa
    ).first()

    if existe:
        return {
            "error": "La placa ya está registrada."
        }

    vehiculo = Vehiculo(
        placa=placa,
        usuario_id=int(usuario_id),
        tipo_vehiculo=data["tipo_vehiculo"],
        marca=data.get("marca"),
        color=data.get("color"),
        area="Funcionario"
    )

    db.session.add(vehiculo)
    db.session.commit()

    return {
        "mensaje": "Vehículo registrado correctamente."
    }


# ==============================
# HISTORIAL DEL USUARIO
# ==============================

def obtener_historial_usuario(usuario_id):

    vehiculos = Vehiculo.query.filter_by(
        usuario_id=int(usuario_id)
    ).all()

    historial = []

    for vehiculo in vehiculos:

        movimientos = Acceso.query.filter_by(
            vehiculo_id=vehiculo.id
        ).order_by(
            Acceso.fecha_hora.desc()
        ).all()

        entrada = None

        for movimiento in reversed(movimientos):

            if movimiento.tipo_movimiento == "Entrada":
                entrada = movimiento.fecha_hora

            elif movimiento.tipo_movimiento == "Salida":

                historial.append({

                    "fecha": movimiento.fecha_hora.strftime("%Y-%m-%d"),

                    "hora_entrada": entrada.strftime("%H:%M") if entrada else "--",

                    "hora_salida": movimiento.fecha_hora.strftime("%H:%M"),

                    "placa": vehiculo.placa

                })

                entrada = None

        # Si quedó un ingreso sin salida

        if entrada:

            historial.append({

                "fecha": entrada.strftime("%Y-%m-%d"),

                "hora_entrada": entrada.strftime("%H:%M"),

                "hora_salida": "--",

                "placa": vehiculo.placa

            })

    historial.sort(
        key=lambda x: (x["fecha"], x["hora_entrada"]),
        reverse=True
    )

    return historial



def obtener_historial(usuario_id):

    historial = (
        db.session.query(Acceso)
        .join(Vehiculo, Vehiculo.id == Acceso.vehiculo_id)
        .filter(Vehiculo.usuario_id == int(usuario_id))
        .order_by(Acceso.fecha_hora.desc())
        .all()
    )

    return [
        {
            "fecha": acceso.fecha_hora.strftime("%Y-%m-%d"),
            "hora": acceso.fecha_hora.strftime("%H:%M"),
            "placa": acceso.placa,
            "movimiento": acceso.tipo_movimiento
        }
        for acceso in historial
    ]

from app.models.novedad_vigilante import NovedadVigilante


def obtener_notificaciones():

    novedades = NovedadVigilante.query.order_by(
        NovedadVigilante.fecha.desc()
    ).all()

    return [
        {
            "id": n.id,
            "descripcion": n.descripcion,
            "fecha": n.fecha.strftime("%d/%m/%Y %H:%M")
        }
        for n in novedades
    ]


def obtener_perfil():

    usuario_id = get_jwt_identity()

    usuario = Usuario.query.get(usuario_id)

    if not usuario:

        return {"error": "Usuario no encontrado"}, 404

    total_vehiculos = Vehiculo.query.filter_by(
        usuario_id=usuario.id
    ).count()

    total_reservas = Reserva.query.filter_by(
        usuario_id=usuario.id
    ).count()

    return {

        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "rol": usuario.rol.value,
        "vehiculos": total_vehiculos,
        "reservas": total_reservas

    }

def cambiar_password(password_actual, password_nueva):

    usuario_id = get_jwt_identity()

    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return {
            "error": "Usuario no encontrado"
        }, 404

    # Verificar contraseña actual
    if not usuario.verificar_password(password_actual):
        return {
            "error": "La contraseña actual es incorrecta"
        }, 400

    # Validar longitud mínima
    if len(password_nueva) < 8:
        return {
            "error": "La nueva contraseña debe tener al menos 8 caracteres"
        }, 400

    # Evitar reutilizar la misma contraseña
    if usuario.verificar_password(password_nueva):
        return {
            "error": "La nueva contraseña no puede ser igual a la actual"
        }, 400

    # Cambiar contraseña
    usuario.password = password_nueva

    db.session.commit()

    return {
        "mensaje": "Contraseña actualizada correctamente"
    }, 200