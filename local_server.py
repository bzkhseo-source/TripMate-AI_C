"""
TripMate AI - 로컬 테스트 서버

목적:
- Vercel에 배포하기 전, 로컬 PC에서 프론트엔드와 Python API 로직을
  빠르게 연동 테스트하기 위한 Flask 서버.
- 실제 배포용 Serverless Function 형식은 STEP 16에서 별도로 정리한다.
- 동일 조건 재검색 시 api/cache.py를 통해 24시간 캐시를 활용,
  외부 API(Gemini/Places/TourAPI/Ticketmaster/YouTube) 호출을 절약한다.

실행 방법:
  python local_server.py
  -> http://127.0.0.1:5000 에서 정적 파일 + API가 함께 서빙됨
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경변수 로드

from api.recommend import get_ai_recommendations, RecommendationError
from api.places import search_stays, search_foods, PlacesError
from api.events import get_events, EventsError
from api.youtube import search_top_videos, YoutubeError
from api.cache import get_cached, set_cache

app = Flask(__name__, static_folder=".", static_url_path="")


@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(silent=True) or {}

    start_date = data.get("startDate")
    end_date = data.get("endDate")
    country = data.get("country")
    city = data.get("city")
    trip_style = data.get("tripStyle")

    if not start_date or not end_date or not city:
        return jsonify({"error": "여행 날짜와 여행 지역을 입력해주세요."}), 400

    cache_params = {
        "startDate": start_date, "endDate": end_date,
        "country": country, "city": city, "tripStyle": trip_style,
    }
    cached = get_cached("recommend", cache_params)
    if cached is not None:
        return jsonify(cached), 200

    try:
        result = get_ai_recommendations(
            start_date=start_date,
            end_date=end_date,
            country=country,
            city=city,
            trip_style=trip_style,
        )
        set_cache("recommend", cache_params, result)
        return jsonify(result), 200
    except RecommendationError as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "여행 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}), 500


@app.route("/api/stays", methods=["POST"])
def api_stays():
    data = request.get_json(silent=True) or {}
    country = data.get("country")
    city = data.get("city")

    if not city:
        return jsonify({"error": "여행 날짜와 여행 지역을 입력해주세요."}), 400

    cache_params = {"country": country, "city": city}
    cached = get_cached("stays", cache_params)
    if cached is not None:
        return jsonify({"stays": cached}), 200

    try:
        results = search_stays(country=country, city=city)
        set_cache("stays", cache_params, results)
        return jsonify({"stays": results}), 200
    except PlacesError as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "숙박 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}), 500


@app.route("/api/foods", methods=["POST"])
def api_foods():
    data = request.get_json(silent=True) or {}
    country = data.get("country")
    city = data.get("city")

    if not city:
        return jsonify({"error": "여행 날짜와 여행 지역을 입력해주세요."}), 400

    cache_params = {"country": country, "city": city}
    cached = get_cached("foods", cache_params)
    if cached is not None:
        return jsonify({"foods": cached}), 200

    try:
        results = search_foods(country=country, city=city)
        set_cache("foods", cache_params, results)
        return jsonify({"foods": results}), 200
    except PlacesError as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "맛집 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}), 500


@app.route("/api/events", methods=["POST"])
def api_events():
    data = request.get_json(silent=True) or {}
    domestic_or_overseas = data.get("domesticOrOverseas", "domestic")
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    country = data.get("country")
    city = data.get("city")

    if not start_date or not end_date or not city:
        return jsonify({"error": "여행 날짜와 여행 지역을 입력해주세요."}), 400

    cache_params = {
        "domesticOrOverseas": domestic_or_overseas, "startDate": start_date,
        "endDate": end_date, "country": country, "city": city,
    }
    cached = get_cached("events", cache_params)
    if cached is not None:
        return jsonify({"events": cached}), 200

    try:
        results = get_events(
            domestic_or_overseas=domestic_or_overseas,
            start_date=start_date,
            end_date=end_date,
            country=country,
            city=city,
        )
        set_cache("events", cache_params, results)
        return jsonify({"events": results}), 200
    except EventsError as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "행사 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}), 500


@app.route("/api/videos", methods=["POST"])
def api_videos():
    data = request.get_json(silent=True) or {}
    country = data.get("country")
    city = data.get("city")
    food_names = data.get("foodNames")

    if not city:
        return jsonify({"error": "여행 날짜와 여행 지역을 입력해주세요."}), 400

    cache_params = {"country": country, "city": city, "foodNames": food_names}
    cached = get_cached("videos", cache_params)
    if cached is not None:
        return jsonify({"videos": cached}), 200

    try:
        results = search_top_videos(country=country, city=city, food_names=food_names)
        set_cache("videos", cache_params, results)
        return jsonify({"videos": results}), 200
    except YoutubeError as e:
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "영상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)