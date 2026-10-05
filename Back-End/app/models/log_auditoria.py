from app.database.database import db
from datetime import datetime

class LogAuditoria(db.Model):
    __tablename__ = "logs_auditoria"

    id = db.Column(db.Integer, primary_key=True)

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    nivel = db.Column(
        db.String(20),
        nullable=False
    )

    modulo = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.String(255),
        nullable=False
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True
    )

    placa = db.Column(
        db.String(10),
        nullable=True
    )

    def __repr__(self):
        return f"<Log {self.nivel.upper()} - {self.modulo}>"