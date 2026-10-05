# app/routes/admin.py
"""
ParkLink - Rutas de control exclusivo del Administrador.
Blueprint: admin_bp
Prefijo registrado: /api/admin
"""

# app/routes/admin.py

import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.database import db
from app.models.usuario import Usuario, RolEnum  
from app.models.vehiculo import Vehiculo
from app.models.configuracion import Configuracion  

# 💥 NUEVA IMPORTACIÓN: Traemos el servicio de correo recién creado
from app.services.email_service import EmailService

admin_bp = Blueprint("admin", __name__)


# ── 1. REGISTRAR PERSONAL ───────────────────────────────────────────────────
@admin_bp.route("/registrar-usuario", methods=["POST"])
@jwt_required()
def registrar_usuario_por_admin():
    """
    Endpoint para que el administrador dé de alta a un empleado (usuario o vigilante).
    """
    identity = get_jwt_identity()
    rol_actual = identity.get('rol') if isinstance(identity, dict) else None
    
    if not rol_actual:
        user_jwt_id = identity.get('id') if isinstance(identity, dict) else identity
        current_user = Usuario.query.get(int(user_jwt_id))
        if current_user:
            rol_actual = current_user.rol.value

    if rol_actual != 'administrador':
        return jsonify({"error": "Acceso denegado. Se requieren privilegios de administrador."}), 403

    data = request.get_json(silent=True) or {}
    nombre_completo = data.get('nombre') or data.get('nombre_completo')
    correo = data.get('correo') or data.get('email')
    rol_solicitado = data.get('rol', 'usuario')

    if not nombre_completo or not correo:
        return jsonify({"error": "Nombre completo y correo son campos obligatorios."}), 400

    try:
        if isinstance(rol_solicitado, str):
            try:
                rol_enum = RolEnum(rol_solicitado.strip())
            except ValueError:
                rol_enum = RolEnum[rol_solicitado.strip().upper()]
        else:
            rol_enum = RolEnum(rol_solicitado)
    except (KeyError, ValueError): # Corregido keyError a KeyError
        return jsonify({"error": f"El rol '{rol_solicitado}' no es válido en ParkLink."}), 400

    if Usuario.query.filter_by(correo=correo.strip()).first():
        return jsonify({"error": "Este correo electrónico ya está registrado."}), 400

    # 🔑 Tu generador seguro que ya tenías implementado
    password_temporal = secrets.token_urlsafe(8)

    try:
        nuevo_usuario = Usuario(
            nombre_completo=nombre_completo.strip(),
            correo=correo.strip(),
            rol=rol_enum,
            activo=True
        )
        nuevo_usuario.password = password_temporal 

        db.session.add(nuevo_usuario)
        db.session.commit() # Confirmamos en la Base de Datos

        # 📧 ACCIÓN INCORPORADA: Despachamos el correo usando la info guardada
        EmailService.enviar_correo_bienvenida(
            correo_destino=nuevo_usuario.correo,
            nombre_usuario=nuevo_usuario.nombre_completo,
            contrasena_plana=password_temporal
        )

        usuario_dict = nuevo_usuario.to_dict()
        if 'rol' in usuario_dict and hasattr(nuevo_usuario.rol, 'value'):
            usuario_dict['rol'] = nuevo_usuario.rol.value

        return jsonify({
            "message": "Usuario creado con éxito y credenciales enviadas por correo electrónico.",
            "usuario": usuario_dict
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500


# ── 2. VINCULAR VEHÍCULOS (CORREGIDO Y BLINDADO DE RAÍZ) ──────────────────────
@admin_bp.route("/vehiculos", methods=["POST"])
@jwt_required()
def vincular_vehiculo():
    """
    Endpoint para asociar un vehículo a un funcionario corporativo.
    Soporta múltiples estructuras de payloads y resuelve dinámicamente el RolEnum.
    """
    identity = get_jwt_identity()
    rol_actual = identity.get('rol') if isinstance(identity, dict) else None
    
    if not rol_actual:
        user_jwt_id = identity.get('id') if isinstance(identity, dict) else identity
        current_user = Usuario.query.get(int(user_jwt_id))
        if current_user:
            rol_actual = current_user.rol.value

    if rol_actual != 'administrador':
        return jsonify({"error": "Acceso denegado. Se requieren privilegios de administrador."}), 403

    data = request.get_json(silent=True) or {}
    
    # 🛠️ FLEXIBILIDAD: Captura variaciones de nombres de propiedades del Front-End
    nombre_funcionario = data.get('nombre_funcionario') or data.get('nombre')
    placa_recibida = data.get('placa')
    tipo_vehiculo = data.get('tipo_vehiculo', 'Automóvil')
    area = data.get('area', 'Tecnología')

    if not nombre_funcionario or not placa_recibida:
        return jsonify({"error": "El nombre del funcionario y la placa son campos requeridos del sistema."}), 400

    placa_limpia = placa_recibida.strip().upper()

    try:
        # Verificar duplicados de la placa en el modelo Vehiculo
        vehiculo_existente = Vehiculo.query.filter_by(placa=placa_limpia).first()
        if vehiculo_existente:
            return jsonify({"error": f"La placa '{placa_limpia}' ya se encuentra registrada."}), 400

        # Buscar si el usuario ya existe por su nombre exacto
        usuario = Usuario.query.filter_by(nombre_completo=nombre_funcionario.strip()).first()

        # Si el usuario no existe en el sistema, lo creamos dinámicamente de forma segura
        if not usuario:
            username_limpio = nombre_funcionario.lower().replace(" ", "")
            correo_automatico = f"{username_limpio}@parklink.local"
            
            if Usuario.query.filter_by(correo=correo_automatico).first():
                correo_automatico = f"{username_limpio}_{secrets.token_hex(2)}@parklink.local"

            # 🛠️ RESOLUCIÓN ROBUSTA DE ENUM: Busca el rol 'usuario' dinámicamente sin importar mayúsculas/minúsculas
            rol_defecto = None
            for miembro in RolEnum:
                if miembro.value == "usuario" or miembro.name.lower() == "usuario":
                    rol_defecto = miembro
                    break
            
            # Si el bucle falla por diferencias de configuración, usamos el constructor como fallback
            if not rol_defecto:
                try:
                    rol_defecto = RolEnum("usuario")
                except ValueError:
                    rol_defecto = RolEnum["USUARIO"]

            usuario = Usuario(
                nombre_completo=nombre_funcionario.strip(),
                correo=correo_automatico,
                rol=rol_defecto,  # <--- Asignación dinámica libre de fallas de atributo
                activo=True
            )
            usuario.password = "ParkLinkTemp2026*"
            
            db.session.add(usuario)
            db.session.flush()  # Sincroniza para obtener el ID asignado por la BD sin cerrar la sesión

        # Crear y persistir el vehículo usando las columnas mapeadas de vehiculo.py
        nuevo_vehiculo = Vehiculo(
            placa=placa_limpia,
            usuario_id=usuario.id,
            tipo_vehiculo=tipo_vehiculo,
            area=area
        )

        db.session.add(nuevo_vehiculo)
        db.session.commit()

        return jsonify({
            "message": "Vehículo vinculado y autorizado con éxito.",
            "vehiculo": {
                "id": nuevo_vehiculo.id,
                "placa": nuevo_vehiculo.placa,
                "nombre_funcionario": usuario.nombre_completo,
                "area": nuevo_vehiculo.area
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en POST /vehiculos: {str(e)}")
        return jsonify({"error": f"Error interno en el servidor al vincular: {str(e)}"}), 500


# ── 3. LISTAR VEHÍCULOS REGISTRADOS ──────────────────────────────────────────
@admin_bp.route("/vehiculos", methods=["GET"])
@jwt_required()
def listar_vehiculos():
    """
    Retorna la lista global de vehículos autorizados mapeando los datos de forma limpia.
    """
    try:
        datos_token = get_jwt_identity()
        if not datos_token:
            return jsonify({"error": "No se pudo validar la identidad corporativa."}), 401

        rol_actual = datos_token.get('rol') if isinstance(datos_token, dict) else None
        if not rol_actual:
            user_jwt_id = datos_token.get('id') if isinstance(datos_token, dict) else datos_token
            current_user = Usuario.query.get(int(user_jwt_id))
            if current_user:
                rol_actual = current_user.rol.value

        if rol_actual != 'administrador':
            return jsonify({"error": "Acceso denegado. Se requieren privilegios de administrador."}), 403

        vehiculos = Vehiculo.query.all()
        resultado = []
        
        for v in vehiculos:
            usuario_asociado = db.session.get(Usuario, v.usuario_id)
            nombre = usuario_asociado.nombre_completo if usuario_asociado else "Funcionario Desconocido"
            
            resultado.append({
                "id": v.id,
                "placa": v.placa,
                "nombre_funcionario": nombre,
                "area": v.area,
                "tipo_vehiculo": v.tipo_vehiculo
            })
            
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"❌ Error en GET /vehiculos: {str(e)}")
        return jsonify({"error": f"No se pudo conocer la lista: {str(e)}"}), 500
    
    # Al final de app/routes/admin.py

# ── 4. DAR DE BAJA / ELIMINAR VEHÍCULO ──────────────────────────────────────
@admin_bp.route("/vehiculos/<int:vehiculo_id>", methods=["DELETE"])
@jwt_required()
def eliminar_vehiculo(vehiculo_id):
    """
    Endpoint para que el administrador dé de baja (elimine) un vehículo autorizado.
    """
    try:
        datos_token = get_jwt_identity()
        rol_actual = datos_token.get('rol') if isinstance(datos_token, dict) else None
        
        if not rol_actual:
            user_jwt_id = datos_token.get('id') if isinstance(datos_token, dict) else datos_token
            current_user = Usuario.query.get(int(user_jwt_id))
            if current_user:
                rol_actual = current_user.rol.value

        if rol_actual != 'administrador':
            return jsonify({"error": "Acceso denegado. Solo los administradores pueden dar de baja vehículos."}), 403

        # Buscar el vehículo en la base de datos corporativa
        vehiculo = Vehiculo.query.get(vehiculo_id)
        if not vehiculo:
            return jsonify({"error": "El vehículo que intenta eliminar no existe en el sistema."}), 404

        placa_eliminada = vehiculo.placa

        # Eliminar de la sesión y confirmar en la BD
        db.session.delete(vehiculo)
        db.session.commit()

        return jsonify({
            "message": f"El vehículo con placas '{placa_eliminada}' ha sido dado de baja correctamente."
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en DELETE /vehiculos/: {str(e)}")
        return jsonify({"error": f"Error interno en el servidor al eliminar: {str(e)}"}), 500
    
@admin_bp.route("/ingresos/validar-cupo", methods=["POST"])
@jwt_required()
def validar_cupo_parqueo():
    """
    Endpoint intermedio para verificar si el perfil del vehículo cuenta con celdas 
    disponibles configuradas por el administrador antes de efectuar un ingreso activo.
    """
    try:
        datos_token = get_jwt_identity()
        # Puedes remover esta validación de rol si los vigilantes también registran ingresos
        
        data = request.get_json(silent=True) or {}
        tipo_usuario = data.get('tipo_usuario') # Espera: 'admin', 'operativo', 'movilidad'
        
        if not tipo_usuario:
            return jsonify({"error": "El tipo de usuario/perfil es requerido para validar el cupo."}), 400
            
        # 1. Obtener los límites vigentes guardados desde la vista Config.jsx
        config = Configuracion.query.first()
        if not config:
            return jsonify({"error": "No se ha establecido una configuración maestra de celdas en el sistema."}), 404

        # 2. Contar cuántos vehículos de ese tipo se encuentran dentro del parqueadero actualmente
        # Reemplaza 'Vehiculo' por tu modelo de ingresos/celdas activas si tienes una tabla intermedia
        # Ejemplo simulado usando SQLAlchemy:
        # ocupados = RegistroIngreso.query.filter_by(tipo_usuario=tipo_usuario, estado='activo').count()
        ocupados = 0  # <--- Vincula aquí tu consulta de conteo real en tu base de datos

        # 3. Cruzar datos con los parámetros globales guardados
        if tipo_usuario == 'admin':
            limite_maximo = config.celdas_admin
            categoria_nombre = "Administrativos"
        elif tipo_usuario == 'operativo':
            limite_maximo = config.celdas_operativas
            categoria_nombre = "Operativos / Técnicos"
        elif tipo_usuario == 'movilidad':
            limite_maximo = config.celdas_movilidad
            categoria_nombre = "Movilidad Reducida / Eléctricos"
        else:
            return jsonify({"error": f"El perfil '{tipo_usuario}' no pertenece a una categoría válida."}), 400

        # 4. Respuesta lógica del estado del cupo
        if ocupados >= limite_maximo:
            return jsonify({
                "status": "denegado",
                "message": f"Acceso denegado: Los cupos para el personal de tipo [{categoria_nombre}] están agotados ({ocupados}/{limite_maximo})."
            }), 403

        return jsonify({
            "status": "autorizado",
            "message": f"Cupo disponible para [{categoria_nombre}]. Ocupación actual: {ocupados}/{limite_maximo}."
        }), 200

    except Exception as e:
        print(f"❌ Error en validar-cupo: {str(e)}")
        return jsonify({"error": f"Error interno al verificar capacidades: {str(e)}"}), 500
    
@admin_bp.route("/kpis-ocupacion", methods=["GET"])
@jwt_required()
def obtener_kpis_ocupacion():
    """
    Retorna la ocupación actual y los límites máximos configurados
    para calcular los porcentajes en tiempo real dentro del Dashboard.
    """
    try:
        # 1. Obtener capacidades parametrizadas desde Config
        config = Configuracion.query.first()
        if not config:
            # Límites por defecto si la base de datos está limpia
            celdas_admin_max = 40
            celdas_operativas_max = 60
            celdas_movilidad_max = 10
        else:
            celdas_admin_max = config.celdas_admin
            celdas_operativas_max = config.celdas_operativas
            celdas_movilidad_max = config.celdas_movilidad

        # Total global de celdas habilitadas en ParkLink
        total_celdas_sistema = celdas_admin_max + celdas_operativas_max + celdas_movilidad_max

        # 2. Contar cuántos vehículos están dentro del parqueadero actualmente (estado activo)
        # Reemplaza estas líneas por tus consultas de conteo reales (SQLAlchemy .count())
        # Ejemplo: Vehiculo.query.filter_by(en_parqueadero=True, tipo_perfil='admin').count()
        autos_admin_dentro = 15      # <--- Simulado para pruebas
        autos_operativos_dentro = 35 # <--- Simulado para pruebas
        autos_movilidad_dentro = 3   # <--- Simulado para pruebas

        total_vehiculos_dentro = autos_admin_dentro + autos_operativos_dentro + autos_movilidad_dentro

        # 3. Calcular porcentajes de forma segura evitando división por cero
        porcentaje_global = round((total_vehiculos_dentro / total_celdas_sistema) * 100, 1) if total_celdas_sistema > 0 else 0
        porcentaje_admin = round((autos_admin_dentro / celdas_admin_max) * 100, 1) if celdas_admin_max > 0 else 0
        porcentaje_operativo = round((autos_operativos_dentro / celdas_operativas_max) * 100, 1) if celdas_operativas_max > 0 else 0
        porcentaje_movilidad = round((autos_movilidad_dentro / celdas_movilidad_max) * 100, 1) if celdas_movilidad_max > 0 else 0

        return jsonify({
            "status": "success",
            "totales": {
                "capacidad_maxima": total_celdas_sistema,
                "ocupacion_actual": total_vehiculos_dentro,
                "porcentaje_uso_global": porcentaje_global
            },
            "detalles_por_perfil": {
                "administrativo": {
                    "dentro": autos_admin_dentro,
                    "maximo": celdas_admin_max,
                    "porcentaje": porcentaje_admin
                },
                "operativo": {
                    "dentro": autos_operativos_dentro,
                    "maximo": celdas_operativas_max,
                    "porcentaje": porcentaje_operativo
                },
                "movilidad": {
                    "dentro": autos_movilidad_dentro,
                    "maximo": celdas_movilidad_max,
                    "porcentaje": porcentaje_movilidad
                }
            }
        }), 200

    except Exception as e:
        print(f"❌ Error en GET /api/admin/kpis-ocupacion: {str(e)}")
        return jsonify({"error": f"Error al compilar métricas: {str(e)}"}), 500
    
    # ── ENPOINT COMPLETO PARA KPIs (CONEXIÓN DIRECTA CON TU FRONTEND) ───────────
@admin_bp.route("/kpis", methods=["GET"])
@jwt_required()
def obtener_metricas_dashboard_reales():
    """
    Endpoint requerido por KPIs.jsx para renderizar los porcentajes de cupos,
    conteos por tipo de vehículo y el listado en tiempo real de ParkLink.
    """
    try:
        from app.models.configuracion import Configuracion # Mapeo de capacidades
        
        # 1. Traer los límites configurados desde el formulario (Config.jsx)
        config = Configuracion.query.first()
        limite_admin = config.celdas_admin if config else 40
        limite_operativas = config.celdas_operativas if config else 60
        limite_movilidad = config.celdas_movilidad if config else 10
        
        capacidad_maxima_total = limite_admin + limite_operativas + limite_movilidad

        # 2. CONSULTAS REALES A LA BASE DE DATOS (Módulo Vehículos)
        # Contamos cuántos vehículos están ACTIVOS en el parqueadero actualmente
        # (Ajusta los filtros 'estado' o 'en_parqueadero' según las columnas de tu modelo)
        vehiculos_en_plantel = Vehiculo.query.all() # Trae los registros para mapear la tabla inferior
        
        # Clasificación y conteo automatizado basado en lo que registras
        total_carros = Vehiculo.query.filter(Vehiculo.tipo_vehiculo.like('%carro%')).count()
        total_motos = Vehiculo.query.filter(Vehiculo.tipo_vehiculo.like('%moto%')).count()
        
        # Simulamos o contamos las celdas especiales ocupadas
        celdas_especiales_ocupadas = Vehiculo.query.filter_by(tipo_perfil='movilidad').count() if hasattr(Vehiculo, 'tipo_perfil') else 2
        
        ocupacion_total = len(vehiculos_en_plantel)

        # 3. Cálculo matemático del porcentaje real de cupos ocupados
        porcentaje_calculado = 0
        if capacidad_maxima_total > 0:
            porcentaje_calculado = round((ocupacion_total / capacidad_maxima_total) * 100, 1)

        # 4. Estructurar el mapeo de la tabla de visualización inferior de KPIs.jsx
        lista_activos_response = []
        for v in vehiculos_en_plantel:
            lista_activos_response.append({
                "placa": v.placa,
                "tipo_vehiculo": v.tipo_vehiculo or "Particular",
                "funcionario": getattr(v, 'funcionario', 'Funcionario ParkLink'), # Evita caídas si no existe el campo
                "area": getattr(v, 'area', 'Área Operativa'),
                "hora_ingreso": getattr(v, 'hora_ingreso', 'Reciente'),
                "celda": getattr(v, 'celda', 'Asignada')
            })

        # 5. RETORNO EN LA ESTRUCTURA EXACTA QUE ESPERA TU FRONTEND
        return jsonify({
            "ocupacion_total": ocupacion_total,
            "porcentaje_ocupacion": porcentaje_calculado,
            "total_carros": total_carros,
            "total_motos": total_motos,
            "celdas_especiales": celdas_especiales_ocupadas,
            "limite_admin": limite_admin,
            "limite_operativas": limite_operativas,
            "limite_movilidad": limite_movilidad,
            "vehiculos_activos": lista_activos_response
        }), 200

    except Exception as e:
        print(f"❌ Error crítico en compilación de KPIs: {str(e)}")
        return jsonify({"error": f"Error interno del servidor en ParkLink: {str(e)}"}), 500