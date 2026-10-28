from unittest.mock import patch, MagicMock
from app.services.vehiculo_service import VehiculoService

@patch('app.services.vehiculo_service.Vehiculo.query')
@patch('app.services.vehiculo_service.Usuario.query')
@patch('app.services.vehiculo_service.db.session')
def test_normalizacion_y_vinculacion_de_placa(mock_db_session, mock_usuario_query, mock_vehiculo_query):
    
    # ==========================================
    # 1. ARRANGE (Preparar / Configurar el escenario)
    # ==========================================
    # Simulamos que el funcionario sí existe en la base de datos
    funcionario_falso = MagicMock()
    funcionario_falso.id = 1
    funcionario_falso.nombre = "Ana Pérez"
    mock_usuario_query.filter_by.return_value.first.return_value = funcionario_falso

    # Simulamos que la placa todavía NO está registrada (no hay duplicados)
    mock_vehiculo_query.filter_by.return_value.first.return_value = None

    # Datos de entrada "sucios" (con espacios y minúsculas que debemos limpiar)
    datos_entrada = {
        "documento_identidad": "12345678",
        "placa": "   abc-123   ", 
        "tipo_vehiculo": "Automóvil",
        "area": "Administración"
    }

    # ==========================================
    # 2. ACT (Acción / Ejecutar el código a probar)
    # ==========================================
    resultado = VehiculoService.vincular_nuevo_vehiculo(datos_entrada)

    # ==========================================
    # 3. ASSERT (Afirmar / Verificar los resultados)
    # ==========================================
    # A. Verificamos que la búsqueda de duplicados se hizo con la placa limpia y en mayúsculas
    mock_vehiculo_query.filter_by.assert_called_once_with(placa="ABC-123")

    # B. Verificamos que el vehículo que se guardó en la BD tiene la placa normalizada
    vehiculo_guardado = mock_db_session.add.call_args[0][0]
    assert vehiculo_guardado.placa == "ABC-123"

    # C. Verificamos que la respuesta final devuelta al usuario muestra la placa correcta
    assert resultado["vehiculo"]["placa"] == "ABC-123"