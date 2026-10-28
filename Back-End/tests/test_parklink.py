from app.services.auth_service import AuthService

def test_unit_01_validar_correo_valido():
    # 1. Arrange (Datos de Entrada de tu Excel)
    correo = "admin@redeban.com"
    
    # 2. Act (Pasos de Ejecución)
    resultado = AuthService.validar_formato_correo(correo)
    
    # 3. Assert (Resultado Esperado)
    assert resultado is True


def test_unit_02_password_limite_inferior_valido():
    # UNIT-02: Límite exacto válido de 8 caracteres
    es_valido, error = AuthService.validar_password("Park2026")
    assert es_valido is True
    assert error is None

def test_unit_03_password_longitud_invalida():
    # UNIT-03: Límite inválido de 7 caracteres
    es_valido, error = AuthService.validar_password("Park123")
    assert es_valido is False
    assert error == "La contraseña debe tener un mínimo de 8 caracteres."

def test_unit_04_determinar_rol_correo():
    pass

def test_unit_05_determinar_rol_correo():
    pass

def test_unit_06_determinar_rol_correo():
    pass