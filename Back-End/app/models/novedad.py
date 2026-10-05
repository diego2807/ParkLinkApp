from app.database.database import db
from datetime import datetime

class Novedad(db.Model):
    __tablename__ = 'novedades'
    
    id = db.Column(db.Integer, primary_key=True)
    turno_id = db.Column(db.Integer, db.ForeignKey('turnos.id', ondelete='CASCADE'), nullable=False)
    
    # Captura las opciones exactas del select de tu frontend
    tipo_novedad = db.Column(db.String(50), nullable=False) 
    # Opciones: "Acceso Denegado", "Daño en Infraestructura", "Vehículo con Observación", "Problema de Reserva", "Otro"
    
    placa_relacionada = db.Column(db.String(10), nullable=True, index=True) # Campo opcional del formulario
    descripcion = db.Column(db.Text, nullable=False)
    
    # La fecha elegida por el vigilante en el input type="date"
    fecha_novedad = db.Column(db.Date, nullable=False)
    fecha_registro_sistema = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación para conectar con el turno
    turno = db.relationship('Turno', backref='novedades_registradas')

    def __repr__(self):
        return f"<Novedad {self.tipo_novedad} - Placa: {self.placa_relacionada}>"