"""
TripMate AI - AI 여행지 추천 모듈

역할:
- 사용자의 여행 날짜/지역 정보를 받아 Gemini API에 전달
- 구조화된 JSON(Pydantic 스키마)으로 추천 여행지 목록(최소 10개)을 받아 반환
- 기능 요구사항 3번(AI 기반 주요 여행지 추천) 구현

주의:
- API 키는 .env에서 로드하며 코드에 직접 작성하지 않는다.
- 오류 발생 시 화면이 깨지지 않도록, 호출부(local_server.py)에서
  이 함수가 발생시키는 예외를 반드시 처리해야 한다.
- 이 모듈 자체는 캐싱하지 않는다. 캐싱은 local_server.py의 라우트 레벨에서
  api/cache.py를 통해 처리한다 (동일 조건 재검색 시 이 함수 자체가 호출되지 않음).
"""

import os
import json
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class RecommendedPlace(BaseModel):
    """추천 여행지 1개에 대한 구조화된 정보"""
    name: str = Field(description="여행지 이름")
    reason: str = Field(description="이 곳을 추천하는 이유")
    expected_duration: str = Field(description="예상 체류 시간 (예: '약 2시간')")
    schedule_fit: str = Field(description="여행 일정상 적합성 설명")
    highlight: str = Field(description="주요 특징 한두 줄 요약")


class RecommendationResult(BaseModel):
    """AI 추천 전체 결과"""
    destination_summary: str = Field(description="이번 여행지에 대한 한 줄 요약")
    places: List[RecommendedPlace] = Field(description="추천 여행지 목록 (최소 10개, 최대 12개)")


class RecommendationError(Exception):
    """추천 생성 중 발생하는 모든 오류를 감싸는 커스텀 예외"""
    pass


def _build_prompt(start_date: str, end_date: str, country: str, city: str,
                   trip_style: Optional[str]) -> str:
    style_line = f"\n여행 스타일/목적: {trip_style}" if trip_style else ""
    return f"""당신은 전문 여행 플래너입니다. 아래 조건에 맞는 주요 여행지를 추천해주세요.

여행 기간: {start_date} ~ {end_date}
여행 국가: {country}
여행 도시: {city}{style_line}

요구사항:
- 실제로 존재하는 장소만 추천할 것 (가상의 장소 금지)
- 여행 기간과 지역 특성을 고려하여 최소 10개, 최대 12개의 주요 여행지를 우선순위 순으로 추천
- 각 장소마다 추천 이유, 예상 체류 시간, 일정상 적합성, 주요 특징을 포함
- 단순 나열이 아니라 여행 동선과 기간을 고려한 추천일 것
- 10개 미만으로는 절대 응답하지 말 것
"""


def get_ai_recommendations(start_date: str, end_date: str, country: str,
                             city: str, trip_style: Optional[str] = None) -> dict:
    """
    Gemini API를 호출하여 AI 여행지 추천 결과를 반환한다.

    Returns:
        dict: RecommendationResult 스키마와 동일한 구조의 딕셔너리

    Raises:
        RecommendationError: API 키 누락, 인증 실패, 응답 파싱 실패 등
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RecommendationError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    if not start_date or not end_date or not city:
        raise RecommendationError("여행 날짜와 여행 지역을 입력해주세요.")

    try:
        client = genai.Client(api_key=api_key)

        prompt = _build_prompt(start_date, end_date, country, city, trip_style)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationResult,
                temperature=0.4,
            ),
        )

        if not response.text:
            raise RecommendationError("여행지 추천을 생성하지 못했습니다. 다시 시도해주세요.")

        result_dict = json.loads(response.text)
        return result_dict

    except json.JSONDecodeError:
        raise RecommendationError("AI 응답을 처리하지 못했습니다. 다시 시도해주세요.")
    except RecommendationError:
        raise
    except Exception as e:
        # 인증 오류, 네트워크 오류, 쿼터 초과 등 모든 예외를 사용자 친화적 메시지로 변환
        error_str = str(e).lower()
        if "api key" in error_str or "unauthorized" in error_str or "permission" in error_str:
            raise RecommendationError("외부 서비스 연결에 문제가 발생했습니다.")
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            raise RecommendationError("응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
        else:
            raise RecommendationError("여행지 추천을 생성하지 못했습니다. 다시 시도해주세요.")