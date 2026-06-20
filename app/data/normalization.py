"""Anti-Corruption Layer (ACL) entre v2 y el legacy v1 (Slice 3-C).

Materializa el patron ACL prescrito en US5 (Tabla 3.5): v2 expone un contrato
ESTABLE y consistente (snake_case 'scopus_id' en todo el dominio) sin filtrar las
inconsistencias del legacy. v1 mezcla camelCase ('scopusId') en los autores de
articulo y en las afiliaciones; aqui se traduce al contrato canonico de v2.
"""


def _scopus_id(raw):
    sid = raw.get("scopusId", raw.get("scopus_id"))
    return str(sid) if sid not in (None, "") else None


def normalize_affiliation(raw):
    """v1: {'scopusId','name'}  ->  v2: {'scopus_id','name'} (scopus_id obligatorio)."""
    if not isinstance(raw, dict):
        return raw
    return {"scopus_id": _scopus_id(raw) or "", "name": raw.get("name", "")}


def normalize_article_author(raw):
    """v1: {'name','scopusId'}  ->  v2: {'name','scopus_id'} (scopus_id opcional)."""
    if not isinstance(raw, dict):
        return {"name": str(raw), "scopus_id": None}
    return {"name": str(raw.get("name", "") or ""), "scopus_id": _scopus_id(raw)}
