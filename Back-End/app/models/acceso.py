from app.database.database import db
from datetime import datetime

class Acceso(db.Model):
    __tablename__ = 'accesos'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), nullable=False, index=True)
    
    # RELACIÓN REQUERIDA POR VEHICULO.PY
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id', ondelete='SET NULL'), nullable=True)
    
    tipo_movimiento = db.Column(db.String(15), nullable=False) # "Entrada", "Salida"
    tipo_vehiculo = db.Column(db.String(25), nullable=False)   # "Automóvil", "Motocicleta", "Camioneta"
    tipo_usuario = db.Column(db.String(20), nullable=False, default="Funcionario") # "Funcionario", "Invitado"
    
    celda_id = db.Column(db.Integer, db.ForeignKey('celdas.id'), nullable=True)
    celda_asignada = db.Column(db.String(10), nullable=True) 
    
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    observaciones_salida = db.Column(db.String(255), nullable=True)
    turno_id = db.Column(db.Integer, db.ForeignKey('turnos.id', ondelete='RESTRICT'), nullable=True)

    def __repr__(self):
        return f"<Acceso {self.placa} - Movimiento: {self.tipo_movimiento}>"