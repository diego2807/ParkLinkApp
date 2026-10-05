# app/services/vehiculo_service.py
from app.database.database import db
from app.models.vehiculo import Vehiculo
# Asumiendo que tu modelo de Usuario se encuentra en esta ruta, ajústalo si varía
from app.models.usuario import Usuario 

class VehiculoService:
    
    @staticmethod
    def obtener_todos_los_vehiculos():
        """
        Consulta todos los vehículos registrados y realiza un JOIN con la tabla 
        de usuarios para traer el nombre del funcionario asignado.
        Retorna una lista de diccionarios con el formato que espera el frontend.
        """
        try:
            # Realizamos una consulta uniendo Vehiculo con Usuario
            resultados = db.session.query(Vehiculo, Usuario).join(
                Usuario, Vehiculo.usuario_id == Usuario.id
            ).all()
            
            lista_vehiculos = []
            for vehiculo, usuario in resultados:
                lista_vehiculos.append({
                    "id": vehiculo.id,
                    "placa": vehiculo.placa,
                    "tipo_vehiculo": vehiculo.tipo_vehiculo,
                    "area": vehiculo.area,
                    "nombre_funcionario": usuario.nombre, # Vincula el nombre real del dueño
                    "documento_identidad": usuario.documento # Por si necesitas mapearlo
                })
                
            return lista_vehiculos
        except Exception as e:
            print(f"Error en VehiculoService.obtener_todos_los_vehiculos: {str(e)}")
            raise e

    @staticmethod
    def vincular_nuevo_vehiculo(datos):
        """
        Procesa la lógica de negocio para asociar un vehículo a un funcionario.
        Valida que el funcionario exista mediante su documento de identidad y
        evita duplicidad de placas en el sistema corporativo.
        """
        documento = datos.get("documento_identidad")
        placa = datos.get("placa", "").strip().upper()
        tipo_vehiculo = datos.get("tipo_vehiculo")
        area = datos.get("area")
        
        if not documento or not placa:
            raise ValueError("El documento de identidad y la placa son campos obligatorios.")

        # 1. Verificar si el usuario/funcionario existe en la base de datos por su documento
        usuario = Usuario.query.filter_by(documento=documento).first()
        if not usuario:
            raise ValueError(f"No se encontró ningún funcionario registrado con el documento {documento}.")

        # 2. Verificar si la placa ya se encuentra registrada en el sistema ParkLink
        vehiculo_existente = Vehiculo.query.filter_by(placa=placa).first()
        if vehiculo_existente:
            raise ValueError(f"La placa {placa} ya se encuentra vinculada a otro funcionario en el sistema.")

        try:
            # 3. Crear la nueva instancia del modelo Vehiculo mapeando los datos del JSON
            nuevo_vehiculo = Vehiculo(
                placa=placa,
                usuario_id=usuario.id, # Asocia la llave foránea con el ID hallado
                tipo_vehiculo=tipo_vehiculo,
                area=area
            )
            
            # 4. Persistir el registro de forma segura en la base de datos
            db.session.add(nuevo_vehiculo)
            db.session.commit()
            
            return {
                "mensaje": f"Vehículo con placa {placa} vinculado exitosamente al funcionario {usuario.nombre}.",
                "vehiculo": {
                    "id": nuevo_vehiculo.id,
                    "placa": nuevo_vehiculo.placa,
                    "nombre_funcionario": usuario.nombre,
                    "area": nuevo_vehiculo.area
                }
            }
        except Exception as e:
            db.session.rollback() # Revierte los cambios si ocurre un fallo en el commit
            print(f"Error en VehiculoService.vincular_nuevo_vehiculo: {str(e)}")
            raise e