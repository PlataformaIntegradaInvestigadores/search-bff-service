"""Suite C — Unitarias del agregado Consulta (Slice 1: validacion de contrato)."""
import pytest

from app.domain.value_objects import SearchQuery, ContractValidationError


class TestSearchQueryValida:
    def test_query_valida_pasa(self):
        assert SearchQuery("machine learning").value == "machine learning"

    def test_normaliza_espacios(self):
        assert SearchQuery("  deep   learning  ").value == "deep learning"

    def test_token_de_dos_letras_es_valido(self):
        assert SearchQuery("AI").value == "AI"

    def test_str_devuelve_el_valor_normalizado(self):
        assert str(SearchQuery("  deep learning ")) == "deep learning"


class TestSearchQueryInvalida:
    @pytest.mark.parametrize("texto", ["###", "12345", "a", "!!", "----", "   "])
    def test_consulta_sin_sentido_lanza_422(self, texto):
        with pytest.raises(ContractValidationError):
            SearchQuery(texto)

    def test_excede_longitud_maxima(self):
        with pytest.raises(ContractValidationError) as exc:
            SearchQuery("a" * (SearchQuery.MAX_LENGTH + 1))
        assert exc.value.details[0]["rule"] == "max_length"

    def test_error_incluye_detalles(self):
        with pytest.raises(ContractValidationError) as exc:
            SearchQuery("###")
        assert exc.value.details[0]["field"] == "query"
        assert exc.value.details[0]["rule"] == "meaningful_terms"
