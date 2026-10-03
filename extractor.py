import json
import os
from urllib.parse import urlparse, parse_qs


def get_headers(headers):
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


def get_query_params(raw_url):
    parsed = urlparse(raw_url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    out = {}
    for k, v in params.items():
        out[k] = v[0] if len(v) == 1 else v
    return out


def build_curl(method, url, headers, body=None):
    parts = [f"curl -X {method} '{url}'"]
    for key, value in headers.items():
        if value is not None and value != "":
            parts.append(f" -H '{key}: {value}'")

    if body is not None:
        if isinstance(body, (dict, list)):
            body_json = json.dumps(body, ensure_ascii=False)
            parts.append(f" --data-raw '{body_json}'")
        else:
            parts.append(f" --data-raw '{str(body)}'")
    return "".join(parts).strip()


def find_tokens(headers, body, query_params):
    found = {}
    token_like = [
        "authorization",
        "token",
        "api-key",
        "x-api-key",
        "apikey",
        "cookie",
        "jwt",
        "secret",
        "sessionid",
    ]

    for key, value in headers.items():
        lower = key.lower()
        if (
            lower in token_like
            or "token" in lower
            or "auth" in lower
            or "key" in lower
            or "cookie" in lower
        ):
            found[key] = value

    if isinstance(body, dict):
        for key, value in body.items():
            lower = key.lower()
            if lower in token_like or "token" in lower or "auth" in lower or "key" in lower:
                found[f"body.{key}"] = value

    for key, value in query_params.items():
        lower = key.lower()
        if lower in token_like or "token" in lower or "auth" in lower or "key" in lower:
            found[f"query.{key}"] = value

    return found


def extract_har(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    output = {
        "source_file": os.path.basename(file_path),
        "total_requests": len(entries),
        "requests": [],
    }

    for index, entry in enumerate(entries, start=1):
        request = entry.get("request", {})
        response = entry.get("response", {})

        url = request.get("url", "")
        method = request.get("method", "GET")
        parsed = urlparse(url)
        query_params = get_query_params(url)
        headers = get_headers(request.get("headers", []))
        body = None

        post_data = request.get("postData")
        if post_data:
            if isinstance(post_data, dict):
                text = post_data.get("text")
                if text:
                    try:
                        body = json.loads(text)
                    except Exception:
                        body = text
            elif isinstance(post_data, str):
                try:
                    body = json.loads(post_data)
                except Exception:
                    body = post_data

        response_headers = get_headers(response.get("headers", []))
        response_content = response.get("content", {})
        response_body = None
        if isinstance(response_content, dict):
            text = response_content.get("text")
            if text:
                try:
                    response_body = json.loads(text)
                except Exception:
                    response_body = text
        elif isinstance(response_content, str):
            response_body = response_content

        token_values = find_tokens(headers, body, query_params)

        req = {
            "index": index,
            "method": method,
            "url": url,
            "endpoint": parsed.path,
            "host": parsed.netloc,
            "scheme": parsed.scheme,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "tokens": token_values,
            "response": {
                "status": response.get("status"),
                "status_text": response.get("statusText"),
                "headers": response_headers,
                "body": response_body,
            },
            "curl": build_curl(method, url, headers, body),
        }

        output["requests"].append(req)

    return output


def extract_api_data(har_data, source_file="file.har"):
    entries = har_data.get("entries", []) if isinstance(har_data, dict) else []
    output = {
        "source_file": source_file,
        "total_requests": len(entries),
        "requests": [],
    }

    for index, entry in enumerate(entries, start=1):
        request = entry.get("request", {})
        response = entry.get("response", {})

        url = request.get("url", "")
        method = request.get("method", "GET")
        parsed = urlparse(url)
        query_params = get_query_params(url)
        headers = get_headers(request.get("headers", []))
        body = None

        post_data = request.get("postData")
        if post_data:
            if isinstance(post_data, dict):
                text = post_data.get("text")
                if text:
                    try:
                        body = json.loads(text)
                    except Exception:
                        body = text
            elif isinstance(post_data, str):
                try:
                    body = json.loads(post_data)
                except Exception:
                    body = post_data

        response_headers = get_headers(response.get("headers", []))
        response_content = response.get("content", {})
        response_body = None
        if isinstance(response_content, dict):
            text = response_content.get("text")
            if text:
                try:
                    response_body = json.loads(text)
                except Exception:
                    response_body = text
        elif isinstance(response_content, str):
            response_body = response_content

        token_values = find_tokens(headers, body, query_params)

        output["requests"].append({
            "index": index,
            "method": method,
            "url": url,
            "endpoint": parsed.path,
            "host": parsed.netloc,
            "scheme": parsed.scheme,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "tokens": token_values,
            "response": {
                "status": response.get("status"),
                "status_text": response.get("statusText"),
                "headers": response_headers,
                "body": response_body,
            },
            "curl": build_curl(method, url, headers, body),
        })

    return output
