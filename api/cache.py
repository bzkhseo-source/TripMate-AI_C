"""
TripMate AI - 간단 파일 캐시 모듈

목적:
- 동일한 조건(날짜/지역 등)으로 재검색할 경우, 외부 API(Gemini, Places, TourAPI,
  Ticketmaster, YouTube)를 다시 호출하지 않고 하루(24시간) 동안 저장된 결과를
  재사용한다.
- 특히 Gemini API 무료 티어의 분당/일일 요청 제한 영향을 줄이고, 반복 테스트나
  같은 조건 재조회 시 응답 속도도 향상시킨다.

동작 방식:
- 캐시 키는 "네임스페이스 + 요청 파라미터"를 정규화한 문자열의 SHA-256 해시.
- 캐시 파일은 프로젝트 루트의 cache/ 폴더에 JSON으로 저장된다 (Git에는 포함하지 않음).
- 저장된 지 24시간이 지난 캐시는 만료된 것으로 간주하고 무시한다.

주의:
- 로컬 개발/테스트 단계에서만 사용하는 파일 기반 캐시이다. Vercel 등 서버리스
  배포 환경에서는 파일시스템이 요청마다 초기화될 수 있으므로, STEP 16 배포
  단계에서는 별도의 캐시 전략(예: Vercel KV, 짧은 TTL 등)을 검토해야 한다.
"""

import os
import json
import hashlib
import time

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
CACHE_TTL_SECONDS = 24 * 60 * 60  # 1일


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(namespace: str, params: dict) -> str:
    raw = namespace + json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(namespace: str, params: dict):
    """캐시된 결과가 있고 아직 유효(24시간 이내)하면 반환, 없거나 만료되면 None"""
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
    """조회 결과를 캐시 파일로 저장"""
    _ensure_cache_dir()
    key = _cache_key(namespace, params)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    entry = {"timestamp": time.time(), "data": data}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
    except OSError:
        # 캐시 저장 실패는 치명적이지 않으므로 조용히 무시 (기능은 계속 정상 동작)
        pass