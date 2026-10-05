#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de inicialización (Seed) para ParkLink.
Crea las cuentas por defecto para el Administrador y el Vigilante
si no existen previamente en la base de datos MySQL.
"""

from app import create_app
from app.database.database import db
from app.models.usuario import Usuario
from app.services.auth_service import AuthService

app = create_app()

def poblar_base_de_datos():
    print("=" * 60)
    print(" INICIANDO EL PROCESO DE POBLADO DE DATOS (SEEDING)...")
    print("=" * 60)


    usuarios_iniciales = [
        {
            "nombre_completo": "Administrador Principal",
            "correo": "admin@gmail.com", 
            "password": "AdminPassword123*"
        },
        {
            "nombre_completo": "Vigilante Técnico",
            "correo": "guardia1@gmail.com", 
            "password": "VigilantePassword123*"
        }
    ]

    usuarios_creados = 0

    for datos in usuarios_iniciales:
        correo_normalizado = datos["correo"].strip().lower()
        
        # Verificar si el usuario ya existe para evitar duplicados en la base de datos
        usuario_existente = Usuario.query.filter_by(correo=correo_normalizado).first()
        
        if not usuario_existente:
            rol_asignado = AuthService.determinar_rol_por_correo(correo_normalizado)
            
            # Instanciar el modelo de usuario con los campos requeridos por tu Base de Datos
            nuevo_usuario = Usuario(
                nombre_completo=datos["nombre_completo"].strip(),
                correo=correo_normalizado,
                rol=rol_asignado,
                activo=True
            )
            
            # El setter del modelo 'Usuario' se encarga de aplicar automáticamente 
            # el hash Bcrypt a la contraseña en texto plano
            nuevo_usuario.password = datos["password"]
            
            try:
                db.session.add(nuevo_usuario)
                print(f" Registrando: {correo_normalizado} -> Rol asignado: [{rol_asignado.value}]")
                usuarios_creados += 1
            except Exception as e:
                print(f" Error al preparar el usuario {correo_normalizado}: {str(e)}")
        else:
            print(f"⚠️  El usuario '{correo_normalizado}' ya se encuentra registrado. Saltando...")

    # 3. Confirmar y guardar de manera persistente en MySQL
    if usuarios_creados > 0:
        try:
            db.session.commit()
            print("=" * 60)
            print(f" SEED EXITOSO: Se crearon e indexaron {usuarios_creados} usuarios correctamente.")
            print("=" * 60)
        except Exception as e:
            db.session.rollback()
            print("=" * 60)
            print(f" ERROR CRÍTICO al hacer commit en la base de datos: {str(e)}")
            print("=" * 60)
    else:
        print("=" * 60)
        print("ℹ  No se realizaron cambios. Todos los usuarios ya existían en el sistema.")
        print("=" * 60)

if __name__ == "__main__":
    # Ejecutar dentro del contexto de Flask para que reconozca la conexión de SQLAlchemy
    with app.app_context():
        poblar_base_de_datos()