from datetime import datetime


from app.database.database import db
from app.models.turno import Turno
from app.models.vehiculo import Vehiculo
from app.models.celda import Celda
from app.models.acceso import Acceso
from app.models.visitante import Visitante
from app.models.novedad_vigilante import NovedadVigilante
from app.models.log_auditoria import LogAuditoria
from app.models.reserva import Reserva


def registrar_log(nivel, modulo, descripcion, usuario_id=None, placa=None):
    try:
        log = LogAuditoria(
            nivel=nivel,
            modulo=modulo,
            descripcion=descripcion,
            usuario_id=usuario_id,
            placa=placa
        )

        db.session.add(log)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print("Error registrando log:", e)




def abrir_turno(usuario_id):

    turno_activo = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if turno_activo:
        return "Ya existe un turno activo"

    nuevo_turno = Turno(
        usuario_id=int(usuario_id),
        jornada="Mañana"
    )

    db.session.add(nuevo_turno)
    db.session.commit()

    registrar_log(
    "informativo",
    "Turnos",
    "Se abrió un turno",
    usuario_id
)

    return "Turno abierto correctamente"


def listar_turnos():

    turnos = Turno.query.all()

    return [
        {
            "id": turno.id,
            "usuario_id": turno.usuario_id,
            "jornada": turno.jornada,
            "estado": turno.estado
        }
        for turno in turnos
    ]


def cerrar_turno(usuario_id):

    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return None

    turno.estado = "Cerrado"
    turno.fecha_cierre = datetime.utcnow()

    db.session.commit()

    registrar_log(
    "informativo",
    "Turnos",
    "Se cerró un turno",
    usuario_id
)

    return "Turno cerrado correctamente"


def registrar_entrada(usuario_id, placa):

    vehiculo = Vehiculo.query.filter_by(
        placa=placa
    ).first()

    if not vehiculo:
        return {"error": "Vehículo no encontrado"}

    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return {"error": "No existe un turno activo"}

    celda = Celda.query.filter_by(
        ocupada=False
    ).first()

    if not celda:
        return {"error": "No hay celdas disponibles"}
    
    # Verificar último movimiento del vehículo
    ultimo_movimiento = Acceso.query.filter_by(
        vehiculo_id=vehiculo.id
    ).order_by(
        Acceso.fecha_hora.desc()
    ).first()

    if ultimo_movimiento and ultimo_movimiento.tipo_movimiento == "Entrada":
        return {
            "error": "El vehículo ya se encuentra dentro del parqueadero"
        }

    nuevo_acceso = Acceso(
        placa=vehiculo.placa,
        vehiculo_id=vehiculo.id,
        tipo_movimiento="Entrada",
        tipo_vehiculo=vehiculo.tipo_vehiculo,
        tipo_usuario="Funcionario",
        celda_id=celda.id,
        celda_asignada=celda.codigo_celda,
        turno_id=turno.id
    )

    celda.ocupada = True

    turno.total_entradas += 1

    db.session.add(nuevo_acceso)

    # ==========================
    # ACTIVAR RESERVA
    # ==========================

    reserva = Reserva.query.filter_by(
        vehiculo_id=vehiculo.id,
        estado="Pendiente"
    ).order_by(
        Reserva.fecha.desc(),
        Reserva.hora.desc()
    ).first()

    if reserva:
        reserva.estado = "Activa"

    db.session.commit()

    registrar_log(
    "informativo",
    "Accesos",
    f"Entrada registrada del vehículo {placa}",
    usuario_id,
    placa
)

    return {
        "mensaje": "Entrada registrada correctamente",
        "celda": celda.codigo_celda

    }


def registrar_salida(usuario_id, placa):

    # Buscar vehículo
    vehiculo = Vehiculo.query.filter_by(
        placa=placa
    ).first()

    if not vehiculo:
        return {"error": "Vehículo no encontrado"}

    # Verificar turno activo
    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return {"error": "No existe un turno activo"}

    # Obtener el ÚLTIMO movimiento del vehículo
    ultimo_movimiento = Acceso.query.filter_by(
        vehiculo_id=vehiculo.id
    ).order_by(
        Acceso.fecha_hora.desc()
    ).first()

    if not ultimo_movimiento:
        return {"error": "El vehículo nunca ha ingresado"}

    # Si el último movimiento ya fue una salida,
    # no puede volver a salir.
    if ultimo_movimiento.tipo_movimiento == "Salida":
        return {
            "error": "El vehículo ya salió del parqueadero"
        }

    # Liberar la celda
    celda = Celda.query.get(ultimo_movimiento.celda_id)

    if celda:
        celda.ocupada = False

    # Registrar la salida
    nueva_salida = Acceso(
        placa=vehiculo.placa,
        vehiculo_id=vehiculo.id,
        tipo_movimiento="Salida",
        tipo_vehiculo=vehiculo.tipo_vehiculo,
        tipo_usuario=ultimo_movimiento.tipo_usuario,
        celda_id=ultimo_movimiento.celda_id,
        celda_asignada=ultimo_movimiento.celda_asignada,
        turno_id=turno.id
    )

    turno.total_salidas += 1

    db.session.add(nueva_salida)

    # ==========================
    # FINALIZAR RESERVA
    # ==========================

    reserva = Reserva.query.filter_by(
        vehiculo_id=vehiculo.id,
        estado="Activa"
    ).order_by(
        Reserva.fecha.desc(),
        Reserva.hora.desc()
    ).first()

    if reserva:
        reserva.estado = "Finalizada"

    db.session.commit()

    registrar_log(
    "informativo",
    "Accesos",
    f"Salida registrada del vehículo {placa}",
    usuario_id,
    placa
)

    return {
        "mensaje": "Salida registrada correctamente",
        "celda_liberada": ultimo_movimiento.celda_asignada
    }


def historial_turno(usuario_id):

    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return {"error": "No existe un turno activo"}

    accesos = Acceso.query.filter_by(
        turno_id=turno.id
    ).order_by(
        Acceso.fecha_hora.desc()
    ).all()

    return [
        {
            "id": acceso.id,
            "placa": acceso.placa,
            "movimiento": acceso.tipo_movimiento,
            "celda": acceso.celda_asignada,
            "fecha_hora": acceso.fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
        }
        for acceso in accesos
    ]

def vehiculos_activos(usuario_id):

    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return {"error": "No existe un turno activo"}

    # Obtener todas las placas que tuvieron movimientos en este turno
    placas = db.session.query(
        Acceso.placa
    ).filter_by(
        turno_id=turno.id
    ).distinct().all()

    activos = []

    for (placa,) in placas:

        ultimo_movimiento = Acceso.query.filter_by(
            turno_id=turno.id,
            placa=placa
        ).order_by(
            Acceso.fecha_hora.desc()
        ).first()

        if ultimo_movimiento and ultimo_movimiento.tipo_movimiento == "Entrada":

            activos.append({
                "placa": ultimo_movimiento.placa,
                "celda": ultimo_movimiento.celda_asignada,
                "fecha_entrada": ultimo_movimiento.fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
                "tipo_vehiculo": ultimo_movimiento.tipo_vehiculo
            })

    return activos

def resumen_turno(usuario_id):

    turno = Turno.query.filter_by(
        usuario_id=int(usuario_id),
        estado="Activo"
    ).first()

    if not turno:
        return {"error": "No existe un turno activo"}

    entradas = Acceso.query.filter_by(
        turno_id=turno.id,
        tipo_movimiento="Entrada"
    ).count()

    salidas = Acceso.query.filter_by(
        turno_id=turno.id,
        tipo_movimiento="Salida"
    ).count()

    total_celdas = Celda.query.count()

    celdas_ocupadas = Celda.query.filter_by(
        ocupada=True
    ).count()

    celdas_libres = total_celdas - celdas_ocupadas

    activos = vehiculos_activos(usuario_id)

    visitantes = Visitante.query.count()

    novedades = NovedadVigilante.query.count()

    ultimos = Acceso.query.order_by(
    Acceso.fecha_hora.desc()
    ).limit(5).all()

    actividad = []

    for acceso in ultimos:

        actividad.append({

            "placa": acceso.placa,

            "movimiento": acceso.tipo_movimiento,

            "hora": acceso.fecha_hora.strftime("%H:%M")

        })

    # ==========================
    # ACTIVIDAD RECIENTE
    # ==========================

    ultimos_movimientos = Acceso.query.order_by(
        Acceso.fecha_hora.desc()
    ).limit(5).all()

    actividad = []

    for movimiento in ultimos_movimientos:

        actividad.append({

            "placa": movimiento.placa,

            "movimiento": movimiento.tipo_movimiento,

            "hora": movimiento.fecha_hora.strftime("%H:%M"),

            "celda": movimiento.celda_asignada

        })

    return {

        "entradas": entradas,

        "salidas": salidas,

        "vehiculos_activos": len(activos),

        "celdas_ocupadas": celdas_ocupadas,

        "celdas_libres": celdas_libres,

        "total_celdas": total_celdas,

        "visitantes": visitantes,

        "novedades": novedades,

        "actividad": actividad

    }

def registrar_visitante(data):

    nuevo_visitante = Visitante(
        nombre_completo=data.get("nombre_completo"),
        documento=data.get("documento"),
        placa_vehiculo=data.get("placa_vehiculo"),
        area_visitada=data.get("area_visitada"),
        motivo_visita=data.get("motivo_visita")
    )

    db.session.add(nuevo_visitante)
    db.session.commit()

    return {
        "mensaje": "Visitante registrado correctamente"
    }


def listar_visitantes():

    visitantes = Visitante.query.order_by(
        Visitante.fecha_registro.desc()
    ).all()

    return [
        {
            "id": visitante.id,
            "nombre_completo": visitante.nombre_completo,
            "documento": visitante.documento,
            "placa_vehiculo": visitante.placa_vehiculo,
            "area_visitada": visitante.area_visitada,
            "motivo_visita": visitante.motivo_visita,
            "fecha_registro": visitante.fecha_registro.strftime("%Y-%m-%d %H:%M:%S")
        }
        for visitante in visitantes
    ]


def crear_novedad(usuario_id, descripcion):

    nueva_novedad = NovedadVigilante(
        descripcion=descripcion,
        usuario_id=int(usuario_id)
    )

    db.session.add(nueva_novedad)
    db.session.commit()

    registrar_log(
    "advertencia",
    "Novedades",
    descripcion,
    usuario_id
)

    return {
        "mensaje": "Novedad registrada correctamente"
    }

def listar_novedades():

    novedades = NovedadVigilante.query.order_by(
        NovedadVigilante.fecha.desc()
    ).all()

    return [
        {
            "id": novedad.id,
            "descripcion": novedad.descripcion,
            "fecha": novedad.fecha.strftime("%Y-%m-%d %H:%M:%S")
        }
        for novedad in novedades
    ]

def consultar_vehiculo(placa):

    vehiculo = Vehiculo.query.filter_by(
        placa=placa.upper()
    ).first()

    if not vehiculo:
        return {
            "error": "Vehículo no registrado."
        }

    return {

        "placa": vehiculo.placa,
        "tipo": vehiculo.tipo_vehiculo,
        "marca": vehiculo.marca,
        "color": vehiculo.color,
        "area": vehiculo.area,
        "propietario": vehiculo.usuario.nombre_completo

    }