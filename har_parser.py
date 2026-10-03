import json
from urllib.parse import urlparse, parse_qs


def parse_har(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "log" in data:
        return data["log"]
    return data


def normalize_headers(headers):
    result = {}
    if not headers:
        return result
    for h in headers:
        if isinstance(h, dict):
            name = h.get("name")
            value = h.get("value")
            if name:
                result[name] = value
    return result


def safe_json_loads(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, str, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def parse_body(entry):
    if not entry:
        return None
    if isinstance(entry, dict):
        return entry
    try:
        return json.loads(entry)
    except Exception:
        return entry


# Fake function left for compatibility
