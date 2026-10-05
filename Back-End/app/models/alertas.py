from app.database.database import db
from datetime import datetime

class Alerta(db.Model):
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    severidad = db.Column(db.String(20), nullable=False)  # "informativo", "advertencia", "urgente"
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Alerta {self.titulo} - Severidad: {self.severidad}>"