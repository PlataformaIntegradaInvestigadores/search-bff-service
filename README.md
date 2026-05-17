# centinela-backend-search-ms

Microservicio de búsqueda (v2) para Centinela. Implementa un bridge hacia la API v1 y expone un contrato estable para el frontend.

## Requisitos

- Python 3.10+ (recomendado 3.11)
- Entorno virtual (venv) recomendado

## Configuración

Variables en `.env` (opcional, con defaults):

```
V1_SEARCH_URL=http://localhost:8001/api-se/v1/llm-search/semantic-search/
BASE_URL=http://localhost:8001
DATASET_VERSION=2026-04-us8
```

## Instalación

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecución

```
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Base URL local: `http://localhost:8002`

## Contrato (API v2)

Prefijo: `/api-se/v2`

### POST /search

Búsqueda semántica. Retorna resultados con metadatos y filtros de años.

**Request**

```
{
	"query": "string",
	"page": 1,
	"page_size": 10,
	"filters": {
		"years": [2024, 2023],
		"type": "article"
	}
}
```

**Response 200**

```
{
	"data": [
		{
			"title": "string",
			"abstract": "string",
			"scopus_id": "string",
			"publication_date": "YYYY-MM-DD",
			"relevance": 0.0
		}
	],
	"years": ["2024", "2023"],
	"total": 1,
	"query_time_ms": 12.34,
	"total_results": 120,
	"search_type": "semantic"
}
```

**Errores**

- 400 `INVALID_INPUT` cuando `query` es vacío.
- 503 `DEPENDENCY_UNAVAILABLE` si el bridge Django no responde.
- 500 `INTERNAL_ERROR` para errores no controlados.

```
{
	"error": {
		"code": "INVALID_INPUT",
		"message": "string",
		"details": []
	},
	"trace_id": "uuid"
}
```

### GET /search/filters

Retorna filtros estáticos para la UI.

**Response 200**

```
{
	"years": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
	"types": ["article", "review"]
}
```

### GET /health

Verifica conectividad con el bridge Django (v1).

**Response 200**

```
{
	"status": "healthy",
	"version": "2.0.0"
}
```

**Response 503**

```
{
	"error": {
		"code": "DEPENDENCY_UNAVAILABLE",
		"message": "string",
		"details": []
	},
	"trace_id": "uuid"
}
```