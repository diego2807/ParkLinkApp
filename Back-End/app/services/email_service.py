# app/services/email_service.py
from flask_mailman import EmailMessage
from flask import current_app

class EmailService:
    """
    Servicio encargado de la construcción y despacho de correos corporativos
    en el ecosistema ParkLink.
    """
    @staticmethod
    def enviar_correo_bienvenida(correo_destino, nombre_usuario, contrasena_plana):
        """
        Construye y envía el correo electrónico con las credenciales de acceso.
        """
        asunto = "🚗 ¡Bienvenido a ParkLink! - Credenciales de Acceso"
        
        # Cuerpo estructurado de manera profesional, claro y directo
        cuerpo = (
            f"Hola, {nombre_usuario}.\n\n"
            f"Te damos la bienvenida a ParkLink, el sistema de gestión de parqueaderos corporativos.\n"
            f"Un administrador ha creado tu cuenta con éxito. A continuación, encontrarás tus credenciales temporales:\n\n"
            f"----------------------------------------\n"
            f"📧 Correo: {correo_destino}\n"
            f"🔑 Contraseña Temporal: {contrasena_plana}\n"
            f"----------------------------------------\n\n"
            f"Por tu seguridad, te recomendamos cambiar esta contraseña en tu primer ingreso al sistema.\n\n"
            f"Saludos cordiales,\n"
            f"Equipo de Soporte ParkLink."
        )

        try:
            # Instanciamos el mensaje usando Flask-Mailman
            msg = EmailMessage(
                subject=asunto,
                body=cuerpo,
                from_email=current_app.config.get('MAIL_USERNAME'),
                to=[correo_destino]
            )
            msg.send()
            print(f"📧 Correo de bienvenida enviado con éxito a: {correo_destino}")
            return True
        except Exception as e:
            # Capturamos el error en consola para debugging pero no rompemos el flujo principal
            print(f"❌ Error al enviar el correo a {correo_destino}: {str(e)}")
            return False