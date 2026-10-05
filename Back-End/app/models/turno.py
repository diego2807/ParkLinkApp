from app.database.database import db
from datetime import datetime

class Turno(db.Model):
    __tablename__ = 'turnos'
    
    id = db.Column(db.Integer, primary_key=True)
    # Llave foránea que conecta directamente con la cuenta del vigilante en sesión
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=False)
    
    jornada = db.Column(db.String(20), nullable=False, default="Mañana") # Mañana, Tarde, Noche
    fecha_apertura = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_cierre = db.Column(db.DateTime, nullable=True)
    
    # Acumulados métricos requeridos por CierreTurno.jsx
    total_entradas = db.Column(db.Integer, default=0)
    total_salidas = db.Column(db.Integer, default=0)
    total_visitantes = db.Column(db.Integer, default=0)
    total_novedades = db.Column(db.Integer, default=0)
    
    observaciones_finales = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(15), default="Activo", nullable=False) # Activo, Cerrado

    # Relación inversa para auditorías directas
    usuario = db.relationship('Usuario', backref='turnos_realizados')

    def __repr__(self):
        return f"<Turno ID: {self.id} - Usuario: {self.usuario_id} - Estado: {self.estado}>"