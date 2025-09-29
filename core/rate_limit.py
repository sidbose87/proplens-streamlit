import time
import urllib.parse
import requests
from typing import Optional, Tuple
from robotexclusionrulesparser import RobotExclusionRulesParser

# Simple per-host backoff and robots cache
_last_call: dict[str, float] = {}
_robots_cache: dict[str, RobotExclusionRulesParser] = {}
_content_cache: dict[str, tuple[float, requests.Response]] = {}

UA = {"User-Agent": "PropLens/0.1 (+https://example.com)"}

MIN_DELAY_SEC = 2.0
CACHE_TTL_SEC = 600.0


def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc


def robots_allowed(url: str, ua: str = UA["User-Agent"]) -> bool:
    host = _host(url)
    base = f"https://{host}/robots.txt"
    rules = _robots_cache.get(host)
    if not rules:
        try:
            resp = requests.get(base, headers=UA, timeout=10)
            if resp.status_code >= 400:
                # If robots not present, default to allow
                return True
            rules = RobotExclusionRulesParser()
            rules.parse(resp.text)
            _robots_cache[host] = rules
        except Exception:
            return True
    try:
        return rules.is_allowed(ua, url)
    except Exception:
        return True


def polite_get(url: str, timeout: float = 20.0) -> Tuple[Optional[requests.Response], bool]:
    """Returns (response, allowed). If not allowed, response is None.
    Caches content for CACHE_TTL_SEC and enforces MIN_DELAY_SEC per host.
    """
    allowed = robots_allowed(url)
    if not allowed:
        return None, False

    # cache
    now = time.time()
    cached = _content_cache.get(url)
    if cached and now - cached[0] < CACHE_TTL_SEC:
        return cached[1], True

    # backoff per host
    host = _host(url)
    last = _last_call.get(host, 0.0)
    elapsed = now - last
    if elapsed < MIN_DELAY_SEC:
        time.sleep(MIN_DELAY_SEC - elapsed)

    resp = requests.get(url, headers=UA, timeout=timeout)
    _last_call[host] = time.time()
    if resp.ok:
        _content_cache[url] = (time.time(), resp)
    return resp, True