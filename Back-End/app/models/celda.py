from app.database.database import db

class Celda(db.Model):
    __tablename__ = 'celdas'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_celda = db.Column(db.String(10), unique=True, nullable=False, index=True) # Ej: EL-01, MR-05
    tipo_celda = db.Column(db.String(30), nullable=False)  # "administrativas", "operativas", "movilidad", "eléctricos"
    ocupada = db.Column(db.Boolean, default=False, nullable=False)

    # Relación con accesos activos
    movimientos = db.relationship('Acceso', backref='celda', lazy=True)

    def __repr__(self):
        return f"<Celda {self.codigo_celda} - Ocupada: {self.ocupada}>"