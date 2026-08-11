"""
TripMate AI - Google Places API (New) 연동 모듈

역할:
- 숙박시설(호텔), 맛집 정보를 Places API Text Search (New)로 조회 (각 최소 10개)
- 기능 요구사항: 평점/리뷰 기반 관광지·숙박·맛집 정보 제공

주의:
- Google Places API 키는 .env에서 로드하며 코드에 직접 작성하지 않는다.
- 필드마스크(FieldMask)를 최소한으로 지정하여 불필요한 비용 발생을 막는다.
- 비용이 더 비싼 SKU인 리뷰 원문 대신, 평점(rating)과 리뷰수(userRatingCount)만 사용한다.
- 이 모듈 자체는 캐싱하지 않는다. 캐싱은 local_server.py의 라우트 레벨에서
  api/cache.py를 통해 처리한다.
"""

import os
import requests

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.googleMapsUri",
    "places.priceLevel",
])


class PlacesError(Exception):
    """Places API 호출 중 발생하는 모든 오류를 감싸는 커스텀 예외"""
    pass


def _search_text(query: str, max_results: int = 10) -> list:
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise PlacesError("GOOGLE_PLACES_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "languageCode": "ko",
        "maxResultCount": max_results,
    }

    try:
        resp = requests.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body, timeout=10)
    except requests.exceptions.Timeout:
        raise PlacesError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException:
        raise PlacesError("외부 서비스 연결에 문제가 발생했습니다.")

    if resp.status_code == 401 or resp.status_code == 403:
        raise PlacesError("외부 서비스 연결에 문제가 발생했습니다.")
    if resp.status_code == 429:
        raise PlacesError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    if resp.status_code != 200:
        raise PlacesError("정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")

    data = resp.json()
    places = data.get("places", [])

    results = []
    for p in places:
        results.append({
            "name": p.get("displayName", {}).get("text", "이름 미상"),
            "address": p.get("formattedAddress", "주소 정보 없음"),
            "rating": p.get("rating"),
            "userRatingCount": p.get("userRatingCount"),
            "mapUrl": p.get("googleMapsUri"),
            "priceLevel": p.get("priceLevel"),
        })
    return results


def search_stays(country: str, city: str) -> list:
    """숙박시설 검색 (최대 10개, API 관련도순 반환)"""
    query = f"{city} {country} 호텔 숙박시설"
    results = _search_text(query, max_results=10)
    if not results:
        raise PlacesError("해당 조건에 맞는 숙박시설을 찾지 못했습니다.")
    return results


def search_foods(country: str, city: str) -> list:
    """맛집 검색 (최대 10개)"""
    query = f"{city} {country} 맛집 레스토랑"
    results = _search_text(query, max_results=10)
    if not results:
        raise PlacesError("해당 조건에 맞는 맛집을 찾지 못했습니다.")
    return results