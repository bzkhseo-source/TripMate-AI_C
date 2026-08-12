"""
TripMate AI - YouTube Data API v3 연동 모듈

역할:
- 추천 맛집 이름 기반으로 YouTube 리뷰/브이로그 영상을 검색해 조회수 기준 상위 3개를 반환
- 검색어 하나에 의존하지 않고, 여러 검색어를 순차 시도하며 결과를 모아
  다양한 영상이 노출되도록 한다.
- 기능 요구사항: 인기 여행 영상 TOP 3 제공

주의:
- search.list 1회 호출은 100 유닛을 소모한다. 이 모듈은 검색어 여러 개를
  순차 시도할 수 있어 최악의 경우 여러 번 호출될 수 있지만, 목표 개수를
  채우면 즉시 중단하며, local_server.py의 캐싱으로 동일 조건 재검색 시
  API를 다시 호출하지 않는다.
- API 키는 .env에서 로드하며 코드에 직접 작성하지 않는다.
"""

import os
import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class YoutubeError(Exception):
    """YouTube API 호출 중 발생하는 모든 오류를 감싸는 커스텀 예외"""
    pass


def _search(query: str, max_results: int) -> list:
    """실제 YouTube search.list 호출 + 결과 파싱 (내부 헬퍼)"""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise YoutubeError("YOUTUBE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "maxResults": max_results,
        "relevanceLanguage": "ko",
    }

    try:
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise YoutubeError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException:
        raise YoutubeError("외부 서비스 연결에 문제가 발생했습니다.")

    if resp.status_code == 401 or resp.status_code == 403:
        raise YoutubeError("외부 서비스 연결에 문제가 발생했습니다.")
    if resp.status_code == 429:
        raise YoutubeError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    if resp.status_code != 200:
        raise YoutubeError("영상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")

    try:
        data = resp.json()
        items = data.get("items", [])
    except ValueError:
        raise YoutubeError("영상 정보를 처리하지 못했습니다. 다시 시도해주세요.")

    results = []
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        results.append({
            "id": video_id,
            "title": snippet.get("title", "제목 없음"),
            "channel": snippet.get("channelTitle", "채널 정보 없음"),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "videoUrl": f"https://www.youtube.com/watch?v={video_id}",
            "publishedAt": snippet.get("publishedAt", ""),
        })
    return results


def _build_query_list(country: str, city: str, food_names: list = None) -> list:
    """
    다양한 결과를 얻기 위해 시도할 검색어 목록을 우선순위 순으로 구성한다.
    앞쪽일수록 더 구체적인(맛집 이름 기반) 검색어이다.
    """
    queries = []

    if food_names:
        cleaned = [n for n in food_names if n]
        for name in cleaned[:3]:
            queries.append(f"{city} {name} 맛집")
        if len(cleaned) >= 2:
            queries.append(f"{city} {' '.join(cleaned[:2])} 맛집 브이로그")

    queries.append(f"{city} {country} 맛집 추천")
    queries.append(f"{city} 여행 브이로그")
    queries.append(f"{city} {country} 여행")

    return queries


def search_top_videos(country: str, city: str, food_names: list = None, max_results: int = 3) -> list:
    """
    여러 검색어를 순차적으로 시도하여, 중복 없는 영상을 최대 max_results개까지 모은다.
    앞선 검색어에서 목표 개수를 채우면 이후 검색어는 시도하지 않는다.
    """
    queries = _build_query_list(country, city, food_names)

    collected = []
    seen_ids = set()

    for query in queries:
        if len(collected) >= max_results:
            break

        remaining = max_results - len(collected)
        try:
            results = _search(query, max_results=remaining)
        except YoutubeError:
            # 특정 검색어에서 오류가 나도, 이미 확보한 결과가 있으면 계속 진행
            if collected:
                continue
            raise

        for video in results:
            if video["id"] not in seen_ids:
                seen_ids.add(video["id"])
                collected.append(video)
            if len(collected) >= max_results:
                break

    # 내부용 id 필드는 프론트에 불필요하므로 제거
    for v in collected:
        v.pop("id", None)

    return collected