"""
TripMate AI - YouTube Data API v3 연동 모듈

역할:
- 추천 맛집 이름 기반으로 YouTube 리뷰 영상을 검색해 조회수 기준 상위 3개를 반환
- 맛집 이름 기반 검색 결과가 0건이면, 지역 맛집 일반 검색으로 자동 재시도(fallback)
- 기능 요구사항: 인기 여행 영상 TOP 3 제공

주의:
- search.list 1회 호출은 100 유닛을 소모한다 (일일 할당량 10,000유닛 기준 약 100회 검색 가능).
  fallback이 발동하면 최대 2회(200유닛) 소모되지만, 캐싱(api/cache.py)으로 동일 조건
  재검색 시에는 API를 다시 호출하지 않는다.
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
            "title": snippet.get("title", "제목 없음"),
            "channel": snippet.get("channelTitle", "채널 정보 없음"),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "videoUrl": f"https://www.youtube.com/watch?v={video_id}",
            "publishedAt": snippet.get("publishedAt", ""),
        })
    return results


def search_top_videos(country: str, city: str, food_names: list = None, max_results: int = 3) -> list:
    """
    지역명(또는 추천 맛집명)으로 검색해 조회수 기준 상위 영상을 반환한다.

    1) food_names가 있으면 맛집 이름 기반으로 먼저 검색
    2) 결과가 0건이면 지역 맛집 일반 검색어로 자동 재시도
    3) food_names가 없으면 처음부터 지역 맛집 일반 검색
    """
    if food_names:
        top_names = [n for n in food_names if n][:2]
        specific_query = f"{city} {' '.join(top_names)} 맛집"
        results = _search(specific_query, max_results)
        if results:
            return results
        # 맛집 이름 기반 검색 결과가 없으면 일반 검색으로 재시도

    fallback_query = f"{city} {country} 맛집 추천"
    return _search(fallback_query, max_results)