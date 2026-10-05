from app.database.database import db

class Configuracion(db.Model):
    __tablename__ = 'configuraciones'
    
    id = db.Column(db.Integer, primary_key=True)
    hora_apertura = db.Column(db.String(5), nullable=False, default="06:00")
    hora_cierre = db.Column(db.String(5), nullable=False, default="22:00")
    permitir_festivos = db.Column(db.Boolean, nullable=False, default=True)
    tiempo_maximo = db.Column(db.Integer, nullable=False, default=14) # Horas máximas
    accion_exceso = db.Column(db.String(30), nullable=False, default="notificar") # "notificar", "bloquear"
    
    # Capacidades parametrizadas
    celdas_admin = db.Column(db.Integer, nullable=False, default=40)
    celdas_operativas = db.Column(db.Integer, nullable=False, default=60)
    celdas_movilidad = db.Column(db.Integer, nullable=False, default=10)

    def __repr__(self):
        return f"<Configuracion Global - Max Tiempo: {self.tiempo_maximo}h>"