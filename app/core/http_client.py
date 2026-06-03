import httpx

# Global HTTP client instance with connection pooling enabled.
# We set limits to allow connection reuse.
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
)
