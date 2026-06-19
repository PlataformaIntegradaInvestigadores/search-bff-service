# language: es
# BDD (Gherkin) del microservicio de búsqueda v2 — Centinela (US6 / ADR-06).
# Formaliza los casos de la Suite A (A-01..A-21) como escenarios Given-When-Then.
# Endpoint base: https://centinela.epn.edu.ec/api-se/v2

Característica: Búsqueda de artículos relevantes
  Como usuario del buscador
  Quiero buscar artículos por un tema
  Para encontrar publicaciones relevantes y filtrarlas por año

  Antecedentes:
    Dado que el microservicio v2 está disponible
    Y el endpoint base es "/api-se/v2"

  @slice0 @articles
  Escenario: A-05 Búsqueda válida de artículos relevantes
    Cuando envío POST a "/articles/relevant" con la consulta "machine learning"
    Entonces la respuesta tiene código 200
    Y el cuerpo contiene una lista de artículos

  @slice0 @articles @facetas
  Escenario: A-06 Filtrar artículos relevantes por año
    Cuando envío POST a "/articles/relevant" con la consulta "machine learning" y years [2024]
    Entonces la respuesta tiene código 200
    Y todos los artículos pertenecen al año 2024

  @slice1 @validacion
  Escenario: A-07 Rechazar una consulta sin sentido (defensa de contrato)
    Cuando envío POST a "/articles/relevant" con la consulta "12345"
    Entonces la respuesta tiene código 422
    Y el código de error es "CONTRACT_VALIDATION"
    Y el cuerpo incluye un "trace_id"


Característica: Validación de contrato de la consulta (Slice 1)
  Como dueño del microservicio intermediario
  Quiero validar la consulta antes de llamar al motor v1
  Para devolver errores controlados y no desperdiciar cómputo

  @slice1 @validacion
  Esquema del escenario: Consultas inválidas devuelven el código esperado
    Cuando envío POST a "<endpoint>" con la consulta "<consulta>"
    Entonces la respuesta tiene código <codigo>
    Y el código de error es "<error>"

    Ejemplos:
      | endpoint            | consulta | codigo | error                |
      | /search             |          | 400    | INVALID_INPUT        |
      | /search             | ###      | 422    | CONTRACT_VALIDATION  |
      | /authors/search     | ###      | 422    | CONTRACT_VALIDATION  |
      | /authors/relevant   | a        | 422    | CONTRACT_VALIDATION  |

  @slice1
  Escenario: A-01 Una consulta válida pasa la validación
    Cuando envío POST a "/search" con la consulta "machine learning"
    Entonces la respuesta tiene código 200


Característica: Búsqueda de autores (modos Author y Relevant Authors)

  @slice0 @authors
  Escenario: A-10 Búsqueda de autor por nombre
    Cuando envío POST a "/authors/search" con la consulta "garcia"
    Entonces la respuesta tiene código 200
    Y el cuerpo contiene una lista de autores

  @slice3c @authors @acl
  Escenario: A-13 Autores relevantes con contrato uniforme de identificador
    Cuando envío POST a "/authors/relevant" con la consulta "machine learning"
    Entonces la respuesta tiene código 200
    Y las afiliaciones exponen el campo "scopus_id"
    Y ninguna afiliación expone el campo "scopusId"


Característica: Perfil de autor por composición (Slice 2)
  Como cliente del buscador
  Quiero obtener el perfil completo de un autor en una sola llamada
  Para no orquestar varias peticiones a v1 desde el frontend

  @slice2 @composicion
  Escenario: A-16 Composición de las cinco secciones del perfil
    Dado un autor con scopus_id "57193901649"
    Cuando solicito GET a "/authors/57193901649/profile"
    Entonces la respuesta tiene código 200
    Y el perfil incluye las secciones author, topics, coauthors, years y articles
    Y la lista "degraded" está vacía

  @slice2 @errores
  Escenario: A-17 Autor inexistente devuelve un error controlado
    Cuando solicito GET a "/authors/0000000000/profile"
    Entonces la respuesta tiene código 503
    Y el servicio no se cae (responde un envelope de error)


Característica: Facetas de año dinámicas (Slice 3-A)

  @slice3a @facetas
  Escenario: A-04 El catálogo de filtros ofrece solo años con datos
    Cuando solicito GET a "/search/filters"
    Entonces la respuesta tiene código 200
    Y la lista "years" contiene únicamente años con artículos reales
    Y la lista "years" no incluye 2018 ni 2026


Característica: Resiliencia ante caída de v1 (Slice 3-B)
  Como capa intermediaria
  Quiero reintentar y degradar con elegancia cuando v1 falla
  Para que el frontend nunca reciba una caída abrupta

  @slice3b @resiliencia
  Escenario: A-20 Núcleo sin caché con v1 caído devuelve 503 controlado
    Dado que el motor v1 está caído
    Y la consulta no está en caché
    Cuando envío POST a "/articles/relevant" con la consulta "tema nuevo"
    Entonces la capa de resiliencia reintenta hasta 3 veces con backoff
    Y la respuesta final tiene código 503
    Y el código de error es "DEPENDENCY_UNAVAILABLE"

  @slice3b @resiliencia @degradacion
  Escenario: A-21 Degradación elegante del perfil con secciones cacheadas
    Dado que el perfil de un autor tiene su núcleo (detalle y artículos) en caché
    Y el motor v1 está caído
    Cuando solicito GET al perfil de ese autor
    Entonces la respuesta tiene código 200
    Y se devuelven las secciones disponibles desde caché
    Y la lista "degraded" incluye "topics", "coauthors" y "years"


Característica: Estado del servicio

  @infra
  Escenario: A-18 Health check del microservicio
    Cuando solicito GET a "/health"
    Entonces la respuesta tiene código 200
    Y el cuerpo indica estado "healthy"
