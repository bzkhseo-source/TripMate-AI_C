"""
TripMate AI - Vercel 배포용 진입점 (Serverless Function)

역할:
- Vercel은 api/ 폴더의 .py 파일을 서버리스 함수로 인식한다. 이 파일이 유일한
  진입점이며, 여기서 노출하는 Flask 앱(app)이 모든 라우트(/, /api/*)를 처리한다.
- 실제 API 로직은 server/ 패키지의 모듈들이 담당하고, 이 파일은 그것들을
  Flask 라우트로 연결하는 역할만 한다.
- vercel.json의 rewrites 설정에 따라 모든 요청이 이 함수로 전달된다.
"""

import os
import sys

# server 패키지를 import할 수 있도록 프로젝트 루트를 sys.path에 추가
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

from server.recommend import get_ai_recommendations, RecommendationError
from server.places import search_stays, search_foods, PlacesError
from server.events import get_events, EventsError
from server.youtube import search_top_videos, YoutubeError
from server.cache import get_cached, set_cache

app = Flask(__name__, static_folder=ROOT_DIR, static_url_path="")


@app.route("/")
def serve_index():
    return send_from_directory(ROOT_DIR, "index.html")


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