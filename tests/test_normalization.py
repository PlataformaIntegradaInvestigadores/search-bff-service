"""Suite C — Unitarias del ACL (Slice 3-C: normalizacion scopusId -> scopus_id)."""

from app.data.normalization import normalize_affiliation, normalize_article_author


class TestNormalizeAffiliation:
    def test_camel_a_snake(self):
        r = normalize_affiliation({"scopusId": "113391044", "name": "NUS"})
        assert r == {"scopus_id": "113391044", "name": "NUS"}
        assert "scopusId" not in r

    def test_ya_en_snake(self):
        r = normalize_affiliation({"scopus_id": "1", "name": "X"})
        assert r["scopus_id"] == "1"

    def test_id_ausente_devuelve_cadena_vacia(self):
        # scopus_id es obligatorio (str) en el contrato -> default ""
        assert normalize_affiliation({"name": "X"})["scopus_id"] == ""

    def test_no_dict_se_devuelve_tal_cual(self):
        assert normalize_affiliation("no-es-dict") == "no-es-dict"


class TestNormalizeArticleAuthor:
    def test_camel_a_snake(self):
        r = normalize_article_author({"name": "G. Vasquez", "scopusId": "59231348300"})
        assert r == {"name": "G. Vasquez", "scopus_id": "59231348300"}
        assert "scopusId" not in r

    def test_id_ausente_devuelve_none(self):
        # scopus_id es opcional en el detalle de articulo -> default None
        assert normalize_article_author({"name": "X"})["scopus_id"] is None

    def test_item_no_dict(self):
        r = normalize_article_author("Solo Un Nombre")
        assert r["name"] == "Solo Un Nombre"
        assert r["scopus_id"] is None
