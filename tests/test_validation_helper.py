"""Unitarias de app/api/v2/_validation.py (traduccion de invariantes a HTTP 422)."""

from app.api.v2._validation import validate_query
from app.domain.value_objects import SearchQuery


class TestValidateQuery:
    def test_query_valida_retorna_search_query_sin_error(self):
        result, error = validate_query("machine learning", "trace-1")
        assert isinstance(result, SearchQuery)
        assert result.value == "machine learning"
        assert error is None

    def test_query_invalida_retorna_none_y_json_response_422(self):
        result, error = validate_query("###", "trace-2")
        assert result is None
        assert error is not None
        assert error.status_code == 422

    def test_error_incluye_trace_id_en_el_body(self):
        _, error = validate_query("###", "trace-abc")
        import json

        body = json.loads(error.body)
        assert body["trace_id"] == "trace-abc"
        assert body["error"]["code"] == "CONTRACT_VALIDATION"
