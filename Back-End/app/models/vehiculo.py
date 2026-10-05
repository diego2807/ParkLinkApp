# app/models/vehiculo.py
from app.database.database import db
from datetime import datetime, timezone

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Índice optimizado para búsquedas rápidas en portería (lectura de placas)
    placa = db.Column(db.String(10), unique=True, nullable=False, index=True)
    
    # Conexión directa con el usuario dueño del carro/moto
    usuario_id = db.Column(
        db.Integer, db.ForeignKey
        ('usuarios.id', 
         ondelete='CASCADE'), 
         nullable=False)

    usuario = db.relationship(
    "Usuario",
    backref="vehiculos"
)
    
    # "Automóvil" o "Motocicleta" (Consistente con los select de tu Vehiculos.jsx)
    tipo_vehiculo = db.Column(db.String(20), nullable=False) 
    
    marca = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(30), nullable=True)
    
    # Área de la empresa (Ej: Tecnología e Innovación, Operaciones y Logística)
    area = db.Column(db.String(100), nullable=False) 
    
    # datetime.now(timezone.utc) evita los warnings de obsolescencia en Python 3.10+
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Historial de entradas y salidas de este vehículo específico
    movimientos = db.relationship('Acceso', backref='vehiculo_relacionado', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vehiculo {self.placa}>"