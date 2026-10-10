import hashlib
import json


def hash_request_body(body: dict) -> str:
    """
    Return a stable SHA-256 hex digest of a request body.

    The body is canonicalised (sorted keys, no extra whitespace) so the
    same logical request always hashes to the same digest.
    """
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
