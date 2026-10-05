import re
from flask import current_app
from app.database.database import db
from app.models.usuario import Usuario, RolEnum


class AuthService:
    """
    Toda la lógica de negocio del flujo de autenticación:
    validaciones, asignación de rol por correo, registro y login.
    Las rutas/controladores NO deben hablar directo con el modelo;
    siempre pasan por aquí.
    """

    # ==========================================
    # VALIDACIONES
    # ==========================================
    PATRON_CORREO = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    @staticmethod
    def validar_formato_correo(correo):
        return bool(re.match(AuthService.PATRON_CORREO, correo or ''))

    @staticmethod
    def validar_password(password):
        """Retorna (es_valido, mensaje_error)."""
        if not password or len(password) < 8:
            return False, "La contraseña debe tener un mínimo de 8 caracteres."
        return True, None

    # ==========================================
    # ASIGNACIÓN DE ROL SEGÚN EL CORREO
    # ==========================================
    @staticmethod
    def determinar_rol_por_correo(correo):
        """
        Decide el rol del usuario según su correo:
        - Termina en el dominio de vigilancia -> VIGILANTE
        - Coincide exactamente con un correo de administración -> ADMINISTRADOR
        - Cualquier otro caso -> USUARIO (rol estándar)
        """
        correo_normalizado = (correo or '').strip().lower()

        dominio_vigilante = current_app.config.get('EMAIL_VIGILANTE_DOMINIO', '').lower()
        correos_admin = current_app.config.get('EMAIL_ADMIN_EXACTOS', [])

        if correo_normalizado in correos_admin:
            return RolEnum.ADMINISTRADOR

        if dominio_vigilante and correo_normalizado.endswith(dominio_vigilante.lower()):
            return RolEnum.VIGILANTE

        return RolEnum.USUARIO

    # ==========================================
    # REGISTRO
    # ==========================================
    @staticmethod
    def registrar_usuario(nombre_completo, correo, password):
        """
        Crea un nuevo usuario validando todos los campos.
        Retorna (usuario, error). Si error no es None, el registro falló
        y usuario será None.
        """
        nombre_completo = (nombre_completo or '').strip()
        correo = (correo or '').strip().lower()

        if not nombre_completo or not correo or not password:
            return None, "Todos los campos son obligatorios."

        if len(nombre_completo) < 3:
            return None, "El nombre completo debe tener al menos 3 caracteres."

        if not AuthService.validar_formato_correo(correo):
            return None, "Ingresa un formato de correo válido."

        es_valido, error_password = AuthService.validar_password(password)
        if not es_valido:
            return None, error_password

        if Usuario.query.filter_by(correo=correo).first():
            return None, "El correo ya se encuentra registrado."

        rol_asignado = AuthService.determinar_rol_por_correo(correo)

        nuevo_usuario = Usuario(
            nombre_completo=nombre_completo,
            correo=correo,
            rol=rol_asignado,
            activo=True,
        )
        # El setter de "password" se encarga de aplicar el hash con Bcrypt
        nuevo_usuario.password = password

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            return nuevo_usuario, None
        except Exception:
            db.session.rollback()
            return None, "Error interno al guardar el usuario en la base de datos."

    # ==========================================
    # LOGIN
    # ==========================================
    @staticmethod
    def login(correo, password):
        """
        Verifica credenciales contra la base de datos.
        Retorna (usuario, error). Por seguridad, el mensaje de error es
        genérico tanto si el usuario no existe como si la contraseña es incorrecta.
        """
        correo = (correo or '').strip().lower()

        if not correo or not password:
            return None, "Correo y contraseña son requeridos."

        usuario = Usuario.query.filter_by(correo=correo).first()

        if not usuario or not usuario.verificar_password(password):
            return None, "Usuario o contraseña incorrectos."

        if not usuario.activo:
            return None, "Esta cuenta está inactiva. Contacta al administrador."

        return usuario, None
