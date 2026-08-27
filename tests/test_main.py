"""Smoke tests de app/main.py: construccion de la app, middlewares y rutas."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestApp:
    def test_ruta_desconocida_retorna_404(self):
        r = client.get("/no-existe")
        assert r.status_code == 404

    def test_respuesta_incluye_header_de_trace_id(self):
        r = client.get("/api-se/v2/cache/stats")
        assert "X-Trace-ID" in r.headers

    def test_validation_error_de_fastapi_retorna_400_con_codigo_invalid_input(self):
        # falta 'query', dispara RequestValidationError -> validation_exception_handler
        r = client.post("/api-se/v2/search", json={})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "INVALID_INPUT"
