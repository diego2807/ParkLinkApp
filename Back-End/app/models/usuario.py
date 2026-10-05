import enum
from app.database.database import db, bcrypt
from datetime import datetime

# 1. Definición estricta de los únicos 3 roles del sistema
class RolEnum(str, enum.Enum):
    USUARIO = 'usuario'
    VIGILANTE = 'vigilante'
    ADMINISTRADOR = 'administrador'

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # 2. Mapeo seguro en la Base de Datos
    # Al pasarle el RolEnum, SQLAlchemy crea un constraint CHECK automático en SQL
    rol = db.Column(db.Enum(RolEnum), nullable=False, default=RolEnum.USUARIO)
    
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ==========================================
    # MANEJO DE BCRYPT / CONTRASEÑAS SEGURAS
    # ==========================================
    @property
    def password(self):
        raise AttributeError('La contraseña no es un atributo legible.')

    @password.setter
    def password(self, password_en_texto_plano):
        # bcrypt.generate_password_hash retorna bytes; se decodifica a string para guardar en la BD
        self.password_hash = bcrypt.generate_password_hash(password_en_texto_plano).decode('utf-8')

    def verificar_password(self, password_en_texto_plano):
        return bcrypt.check_password_hash(self.password_hash, password_en_texto_plano)

    # ==========================================
    # SERIALIZACIÓN COMPATIBLE CON TU FRONTEND
    # ==========================================
    def to_dict(self):
        return {
            "id": self.id,
            "nombre_completo": self.nombre_completo,
            "correo": self.correo,
            # .value asegura que al frontend (React) le llegue el texto plano 'usuario', 'vigilante', etc.
            "rol": self.rol.value if isinstance(self.rol, enum.Enum) else self.rol,
            "activo": self.activo,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }