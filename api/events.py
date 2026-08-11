"""
TripMate AI - 행사(축제/이벤트) 정보 연동 모듈

역할:
- 국내 여행: 한국관광공사 TourAPI(KorService2 searchFestival2)로 축제/행사 조회
- 해외 여행: Ticketmaster Discovery API로 이벤트 조회
- 기능 요구사항: 여행 기간 내 행사 정보 제공

주의:
- 두 API 모두 결과가 0건일 수 있으며, 이는 오류가 아니라 정상 상황이다.
  (요구사항 17조: "해당 조건에 맞는 행사 없음"으로 안전하게 처리)
- API 키는 .env에서 로드하며 코드에 직접 작성하지 않는다.
"""

import os
import requests

TOUR_API_URL = "http://apis.data.go.kr/B551011/KorService2/searchFestival2"
TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


class EventsError(Exception):
    """행사 정보 조회 중 발생하는 모든 오류를 감싸는 커스텀 예외"""
    pass


def _format_date_for_tourapi(date_str: str) -> str:
    return date_str.replace("-", "")


def search_domestic_events(start_date: str, end_date: str, city: str) -> list:
    """국내 축제/행사 조회 (TourAPI)"""
    api_key = os.environ.get("TOUR_API_KEY")
    if not api_key:
        raise EventsError("TOUR_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    params = {
        "serviceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "TripMateAI",
        "_type": "json",
        "numOfRows": 50,
        "pageNo": 1,
        "eventStartDate": _format_date_for_tourapi(start_date),
        "eventEndDate": _format_date_for_tourapi(end_date),
        "arrange": "A",
    }

    try:
        resp = requests.get(TOUR_API_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise EventsError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException:
        raise EventsError("외부 서비스 연결에 문제가 발생했습니다.")

    if resp.status_code != 200:
        raise EventsError("행사 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")

    try:
        data = resp.json()
        result_code = data.get("response", {}).get("header", {}).get("resultCode")
        if result_code not in ("0000", "00"):
            return []

        body = data.get("response", {}).get("body", {})
        total_count = body.get("totalCount", 0)
        if total_count == 0:
            return []

        items = body.get("items", {})
        item_list = items.get("item", []) if items else []
        if isinstance(item_list, dict):
            item_list = [item_list]

    except (ValueError, KeyError):
        raise EventsError("행사 정보를 처리하지 못했습니다. 다시 시도해주세요.")

    # 전국 결과에서 도시명이 주소 또는 제목에 포함된 항목만 필터링
    filtered = [
        item for item in item_list
        if city and (city in item.get("addr1", "") or city in item.get("title", ""))
    ]

    results = []
    for item in filtered:
        results.append({
            "title": item.get("title", "이름 미상"),
            "place": item.get("eventplace", "장소 정보 없음"),
            "address": item.get("addr1", ""),
            "startDate": item.get("eventstartdate", ""),
            "endDate": item.get("eventenddate", ""),
            "image": item.get("firstimage", None),
            "sourceUrl": None,
        })
    return results


def search_overseas_events(start_date: str, end_date: str, country: str, city: str) -> list:
    """해외 이벤트 조회 (Ticketmaster Discovery API)"""
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        raise EventsError("TICKETMASTER_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    params = {
        "apikey": api_key,
        "city": city,
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "size": 10,
    }

    try:
        resp = requests.get(TICKETMASTER_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise EventsError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException:
        raise EventsError("외부 서비스 연결에 문제가 발생했습니다.")

    if resp.status_code == 401 or resp.status_code == 403:
        raise EventsError("외부 서비스 연결에 문제가 발생했습니다.")
    if resp.status_code == 429:
        raise EventsError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        raise EventsError("행사 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")

    try:
        data = resp.json()
        events = data.get("_embedded", {}).get("events", [])
    except ValueError:
        raise EventsError("행사 정보를 처리하지 못했습니다. 다시 시도해주세요.")

    results = []
    for ev in events:
        venue_name = "장소 정보 없음"
        try:
            venues = ev.get("_embedded", {}).get("venues", [])
            if venues:
                venue_name = venues[0].get("name", "장소 정보 없음")
        except (AttributeError, IndexError):
            pass

        start_info = ev.get("dates", {}).get("start", {})

        results.append({
            "title": ev.get("name", "이름 미상"),
            "place": venue_name,
            "address": "",
            "startDate": start_info.get("localDate", ""),
            "endDate": "",
            "image": ev.get("images", [{}])[0].get("url") if ev.get("images") else None,
            "sourceUrl": ev.get("url"),
        })
    return results


def get_events(domestic_or_overseas: str, start_date: str, end_date: str,
                country: str, city: str) -> list:
    """국내/해외에 따라 적절한 API로 행사 정보를 조회하는 통합 함수"""
    if domestic_or_overseas == "overseas":
        return search_overseas_events(start_date, end_date, country, city)
    else:
        return search_domestic_events(start_date, end_date, city)