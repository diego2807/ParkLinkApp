from app.database.database import db
from datetime import datetime


class NovedadVigilante(db.Model):
    __tablename__ = "novedades_vigilante"

    id = db.Column(db.Integer, primary_key=True)

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )