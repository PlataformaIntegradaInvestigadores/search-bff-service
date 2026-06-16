"""
Centralized in-memory cache instances for the search microservice.

Uses TTLCache from cachetools:
- Entries auto-expire after TTL seconds
- maxsize limits the number of cached entries (LRU eviction)
- Cache resets on process restart (container rebuild)
"""
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class TrackedCache(TTLCache):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hits = 0
        self.misses = 0

    def get(self, key, default=None):
        if key in self:
            self.hits += 1
            return super().get(key, default)
        else:
            self.misses += 1
            return default

# --- Cache Instances ---

# Relevant Articles: query + page + page_size + years
articles_cache = TrackedCache(maxsize=200, ttl=900)  # 15 min

# Authors Search: query + page + page_size
authors_search_cache = TrackedCache(maxsize=200, ttl=900)  # 15 min

# Relevant Authors (graph): query + authors_number + affiliations + mode
authors_relevant_cache = TrackedCache(maxsize=50, ttl=600)  # 10 min

# Article Detail: scopus_id
article_detail_cache = TrackedCache(maxsize=100, ttl=1800)  # 30 min

# Articles by Author: author_id
articles_by_author_cache = TrackedCache(maxsize=100, ttl=1800)  # 30 min

# Author Detail: scopus_id
author_detail_cache = TrackedCache(maxsize=100, ttl=1800)  # 30 min

# Facetas de filtros (anios dinamicos): clave estatica, TTL largo (cambian raramente)
filters_cache = TrackedCache(maxsize=4, ttl=3600)  # 1 hora


def make_key(*args) -> str:
    """Build a deterministic cache key from arguments."""
    return ":".join(str(a) for a in args)
