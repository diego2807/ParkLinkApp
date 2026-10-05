from app.database.database import db
from datetime import datetime

class Visitante(db.Model):
    __tablename__ = 'visitantes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(120), nullable=False)
    documento = db.Column(db.String(20), nullable=False, index=True)
    placa_vehiculo = db.Column(db.String(10), nullable=False, index=True)
    area_visitada = db.Column(db.String(100), nullable=False)  # Persona o área visitada
    motivo_visita = db.Column(db.Text, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Visitante {self.nombre_completo} - Placa: {self.placa_vehiculo}>"