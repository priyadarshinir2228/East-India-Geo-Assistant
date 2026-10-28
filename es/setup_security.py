"""Task 1.2: create role rag_app and an API key for it. Runs once as the elastic superuser.

The API key is written to .env (ES_API_KEY), never printed to logs or committed.
Run: python -m es.setup_security
"""
import re

from common import config
from common.es import admin_client

ROLE = {
    "cluster": ["monitor"],  # read cluster health only
    "indices": [{
        "names": [config.CHUNKS_INDEX, config.ENTITIES_INDEX, config.RELATIONS_INDEX],
        "privileges": ["read", "write", "view_index_metadata"],
    }],
}


def main():
    es = admin_client()
    es.security.put_role(name="rag_app", **ROLE)
    # Revoke keys from earlier runs, so only the key in .env works
    old = es.security.invalidate_api_key(name="rag_app_key")
    if old["invalidated_api_keys"]:
        print(f"invalidated {len(old['invalidated_api_keys'])} older rag_app key(s)")
    key = es.security.create_api_key(name="rag_app_key", role_descriptors={"rag_app": ROLE})
    env = config.ROOT / ".env"
    text = env.read_text(encoding="utf-8") if env.exists() else ""
    line = f"ES_API_KEY={key['encoded']}"
    text = re.sub(r"^ES_API_KEY=.*$", line, text, flags=re.M) if "ES_API_KEY=" in text else text + "\n" + line + "\n"
    env.write_text(text, encoding="utf-8")
    print(f"role rag_app created; API key id {key['id']} written to .env (value not shown)")


if __name__ == "__main__":
    main()
