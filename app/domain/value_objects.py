"""Value objects del Bounded Context de busqueda.

Aqui vive la invariante del agregado Consulta (tesis, Tabla 3.4): el
microservicio v2 es DUENO de la validacion de contrato/negocio de la consulta,
responsabilidad que el monolito Django (v1) no implementa. Esto materializa el
codigo HTTP 422 CONTRACT_VALIDATION definido en el contrato US6 (Tabla 3.9) y
cierra el defecto TC-03 de Fase 1 (una consulta sin sentido devolvia resultados).

Nota de alcance: la validacion es un guard heuristico de la capa intermediaria,
no comprension semantica via NLP/ML (ese modelo vive en v1 y no es parte de
este componente).
"""
import re


class ContractValidationError(Exception):
    """La consulta esta bien formada pero viola una regla de negocio/contrato (HTTP 422)."""

    def __init__(self, message, details=None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class SearchQuery:
    """Agregado Consulta: texto de busqueda con sus invariantes de dominio.

    Reglas (capa intermediaria, no NLP/ML):
      - longitud maxima acotada por contrato
      - debe contener al menos un token alfabetico significativo (>= 2 letras);
        de lo contrario se considera semanticamente vacia (caso TC-03 de Fase 1)
    """

    MAX_LENGTH = 256
    MIN_TOKEN_LENGTH = 2
    # Una corrida de >=2 letras (unicode); excluye digitos, simbolos y guion bajo.
    _MEANINGFUL_TOKEN = re.compile(r"[^\W\d_]{%d,}" % MIN_TOKEN_LENGTH, re.UNICODE)

    def __init__(self, raw):
        normalized = " ".join((raw or "").split())

        if len(normalized) > self.MAX_LENGTH:
            raise ContractValidationError(
                f"La consulta excede el maximo de {self.MAX_LENGTH} caracteres.",
                details=[{"field": "query", "rule": "max_length", "limit": self.MAX_LENGTH}],
            )

        if not self._MEANINGFUL_TOKEN.search(normalized):
            raise ContractValidationError(
                "La consulta no contiene terminos con sentido para una busqueda semantica.",
                details=[{"field": "query", "rule": "meaningful_terms"}],
            )

        self.value = normalized

    def __str__(self):
        return self.value
