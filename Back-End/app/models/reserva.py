from datetime import datetime
from app.database.database import db

class Reserva(db.Model):

    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    vehiculo_id = db.Column(
        db.Integer,
        db.ForeignKey("vehiculos.id"),
        nullable=False
    )

    fecha = db.Column(
        db.Date,
        nullable=False
    )

    hora = db.Column(
        db.Time,
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        default="Pendiente"
    )

    fecha_creacion = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Reserva {self.id}>"