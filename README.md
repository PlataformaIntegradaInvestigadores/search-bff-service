# Centinela — search_microservice_backend

Microservicio FastAPI que actúa como bridge entre el frontend y `search_engine_backend` (API v1, Django/Neo4j/MongoDB), exponiendo un contrato v2 estable, con caché y resiliencia ante caídas del backend de origen.

Parte del org multi-repo `PlataformaIntegradaInvestigadores`. No tiene base de datos propia — todo el estado real vive en `search_engine_backend`, al que llama por HTTP. En producción se accede a través de `api-gateway` (Nginx); en Docker local se expone en el host mediante el puerto 8004.

## Stack

- FastAPI 0.111 + Uvicorn (ASGI)
- Pydantic 2 / pydantic-settings (config por env vars)
- httpx (cliente HTTP hacia `search_engine_backend`)
- cachetools (caché en memoria de resultados)

## Estructura del proyecto

```
app/
  api/v2/            # Endpoints HTTP (search, articles, authors) + validación de input
  application/usecases/  # Casos de uso: orquestan adapters + normalización
  core/              # config, excepciones, cliente HTTP, resiliencia (retries/circuit breaker), caché
  data/adapters/      # Adapters que traducen las respuestas v1 de Django al contrato v2
  data/normalization.py
  domain/            # Entidades, value objects, interfaces de repositorio
  schemas/           # Modelos Pydantic de request/response (v2)
  main.py
tests/               # pytest, un archivo por endpoint/usecase/adapter
```

## Requisitos previos

- Docker y Docker Compose (recomendado), o Python 3.11 si se corre sin Docker.
- Red Docker externa `centinela-net` (compartida con el resto de servicios).

## Levantar en local

### Con Docker (recomendado)
```bash
docker network create centinela-net || true
docker compose up -d --build
```
Queda accesible en `http://localhost:8004`. Dentro de la red Docker se resuelve como `search-microservice-backend:8002`.

Para un entorno prod-like:
```bash
cp .env_produccion.example .env_produccion
docker network create centinela-net || true
docker compose --env-file .env_produccion -f docker-compose_produccion.yaml up -d --build
```
En este modo no se publica puerto al host — el acceso es solo vía Nginx/`api-gateway`.

### Sin Docker (desarrollo)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```
Base URL local: `http://localhost:8002`.

## Variables de entorno

Ver `.env.example` (desarrollo) o `.env_produccion.example` (Docker prod-like). Variables clave:

| Variable | Descripción |
|---|---|
| `BASE_URL` | URL base de `search_engine_backend` (v1) |
| `V1_SEARCH_URL` | Endpoint v1 de búsqueda semántica (`llm-search`) |
| `V1_AUTHORS_URL` / `V1_AUTHORS_FIND_URL` / `V1_AUTHORS_DETAIL_URL` | Endpoints v1 de autores usados por los adapters |
| `V1_ARTICLES_RELEVANT_URL` / `V1_ARTICLES_BY_AUTHOR_URL` / `V1_ARTICLES_DETAIL_URL` | Endpoints v1 de artículos |
| `DATASET_VERSION` | Etiqueta de versión de dataset expuesta en `/health` |

## Tests

```bash
pytest tests/ -v --cov=app --cov-report=term
```

Cobertura mínima exigida en CI: **90%** (`--cov-fail-under=90` en `.github/workflows/ci.yml`). Estado actual: 96%, 122 tests.

## API (v2)

Prefijo: `/api-se/v2`

### POST /search
Búsqueda semántica. Retorna resultados con metadatos y filtros de años.

**Request**
```json
{
  "query": "string",
  "page": 1,
  "page_size": 10,
  "filters": { "years": [2024, 2023], "type": "article" }
}
```

**Response 200**
```json
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
- `400 INVALID_INPUT` — `query` vacío.
- `503 DEPENDENCY_UNAVAILABLE` — el bridge Django no responde.
- `500 INTERNAL_ERROR` — error no controlado.

```json
{
  "error": { "code": "INVALID_INPUT", "message": "string", "details": [] },
  "trace_id": "uuid"
}
```

### GET /search/filters
Filtros estáticos para la UI.
```json
{
  "years": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
  "types": ["article", "review"]
}
```

### GET /health
Verifica conectividad con el bridge Django (v1).

**Response 200**
```json
{ "status": "healthy", "version": "2.0.0" }
```

**Response 503**
```json
{
  "error": { "code": "DEPENDENCY_UNAVAILABLE", "message": "string", "details": [] },
  "trace_id": "uuid"
}
```

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`): tests unitarios → build de imagen Docker → deploy automático a staging (`develop` branch, runner self-hosted `ticcd`) con healthcheck y rollback automático.

## Convenciones

- Branches: `feature/*` → `develop`, `hotfix/*` → `main`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/), inglés, con el *por qué* en el cuerpo.
