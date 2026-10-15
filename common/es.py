"""Elasticsearch clients. The app uses the rag_app API key; only setup scripts use elastic."""
from elasticsearch import Elasticsearch

from common import config


def app_client() -> Elasticsearch:
    if not config.ES_API_KEY:
        raise SystemExit("ES_API_KEY is empty: run `python -m es.setup_security` first")
    return Elasticsearch(config.ES_URL, api_key=config.ES_API_KEY, request_timeout=60)


def admin_client() -> Elasticsearch:
    """Superuser client. Used only for one-off setup and admin measurements."""
    return Elasticsearch(config.ES_URL, basic_auth=("elastic", config.ELASTIC_PASSWORD), request_timeout=60)
