"""
TripMate AI - 간단 파일 캐시 모듈

목적:
- 동일한 조건(날짜/지역 등)으로 재검색할 경우, 외부 API 호출 없이 하루(24시간) 동안
  저장된 결과를 재사용한다.

주의:
- 시스템 임시 폴더(tempfile.gettempdir())를 사용한다. 로컬 PC에서는 OS의 임시 폴더에,
  Vercel 서버리스 환경에서는 자동으로 /tmp에 저장된다.
- Vercel 서버리스 환경은 함수 인스턴스가 재사용될 때만 캐시가 유지되고, 새 인스턴스가
  뜨면 초기화될 수 있다 (완전한 영속 저장소는 아니며, 동일 세션 내 반복 요청 절약용).
"""

import os
import json
import hashlib
import time
import tempfile

CACHE_DIR = os.path.join(tempfile.gettempdir(), "tripmate_cache")
CACHE_TTL_SECONDS = 24 * 60 * 60  # 1일


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(namespace: str, params: dict) -> str:
    raw = namespace + json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(namespace: str, params: dict):
    _ensure_cache_dir()
    key = _cache_key(namespace, params)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    if time.time() - entry.get("timestamp", 0) > CACHE_TTL_SECONDS:
        return None

    return entry.get("data")


def set_cache(namespace: str, params: dict, data) -> None:
    _ensure_cache_dir()
    key = _cache_key(namespace, params)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    entry = {"timestamp": time.time(), "data": data}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
    except OSError:
        pass