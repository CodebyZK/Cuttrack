import json
import os
import time
from http.cookiejar import CookieJar
from urllib import parse, request

BASE_URL = os.environ.get("CUTTRACK_BASE_URL", "http://127.0.0.1:5000")


COOKIE_JAR = CookieJar()
OPENER = request.build_opener(request.HTTPCookieProcessor(COOKIE_JAR))


def http(method, path, data=None, headers=None, is_json=False):
    url = BASE_URL + path
    payload = None
    req_headers = dict(headers or {})
    if data is not None:
        if is_json:
            payload = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        else:
            payload = parse.urlencode(data).encode("utf-8")
    req = request.Request(url, data=payload, method=method, headers=req_headers)
    with OPENER.open(req, timeout=8) as resp:
        return resp.getcode(), resp.read().decode("utf-8", errors="replace"), resp.headers


def wait_for_server(attempts=20, delay=0.5):
    for _ in range(attempts):
        try:
            code, _body, _ = http("GET", "/")
            if code in (200, 302):
                return True
        except Exception:
            time.sleep(delay)
    return False


def main():
    if not wait_for_server():
        raise SystemExit("Server is not reachable at " + BASE_URL)

    code, _body, _ = http("GET", "/")
    print("GET / ->", code)

    register_data = {
        "username": "smoke",
        "password": "smoke-pass-123",
    }
    try:
        reg_code, _reg_body, _ = http("POST", "/register", data=register_data)
        print("POST /register ->", reg_code)
    except Exception as err:
        print("POST /register -> skipped (likely already registered):", err)

    login_code, _login_body, _ = http("POST", "/login", data=register_data)
    print("POST /login ->", login_code)

    if not COOKIE_JAR:
        raise SystemExit("Login did not return a session cookie")

    payloads = [
        ("/api/food", {"name": "smoke meal", "calories": 100, "protein": 20}),
        ("/api/workout", {"exercise": "Pushups", "sets": 3, "reps": 12}),
        ("/api/sleep", {"bedtime": "23:00", "waketime": "07:00"}),
        ("/api/weight", {"value": 165.0}),
    ]

    for path, payload in payloads:
        status, _body, _ = http("POST", path, data=payload, is_json=True)
        print("POST", path, "->", status)

    status, _body, _ = http("GET", "/api/watch/today")
    print("GET /api/watch/today ->", status)

    print("Smoke test complete")


if __name__ == "__main__":
    main()
