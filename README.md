# TripMate AI

AI가 여행 날짜와 지역만으로 여행지·행사·숙박·맛집·인기 영상까지 한 번에 정리해주는 여행 추천 웹 서비스입니다.

**배포 URL**: https://tripmate-ai-five.vercel.app

경남 코디세이(Gyeongnam Codyssey) 2026 미션 프로젝트로 제작되었습니다.

---

## 주요 기능

- **AI 여행지 추천**: 여행 날짜·지역·스타일을 입력하면 Gemini AI가 실제 존재하는 여행지 10곳 이상을 이유·체류시간·일정 적합성과 함께 추천
- **행사/축제 정보**: 국내는 한국관광공사 TourAPI, 해외는 Ticketmaster Discovery API로 여행 기간 내 행사 조회
- **숙박·맛집 추천**: Google Places API(New) 기반 평점·리뷰수 포함 숙박시설·맛집 각 10곳 이상 제공
- **인기 여행 영상**: 추천 맛집 이름 기반으로 YouTube에서 관련 리뷰/브이로그 영상 상위 3개 검색 (검색어 다중 시도로 결과 다양화)
- **여행 계획 저장 (보너스)**: 조회한 여행 계획을 브라우저에 저장하고, MY TRIP에서 목록 확인·방문상태(방문예정/방문완료) 관리·상세보기(재조회 없이 즉시 확인)·삭제 가능
- **캐싱**: 동일 조건 재검색 시 24시간 캐시를 사용해 외부 API 호출 절약
- **예외 처리**: 빈 입력, 0건 결과, 인증 실패, 쿼터 초과 등 모든 오류 상황을 사용자 친화적 메시지로 안전하게 처리

## 기술 스택

**Frontend**
- HTML / CSS / Vanilla JavaScript (SPA 구조, `tripState` 객체 기반 화면 전환)
- 반응형 디자인 (데스크톱·모바일 대응)

**Backend**
- Python (Flask — 로컬 개발용 `local_server.py`)
- Vercel Serverless Function (`api/index.py` — 배포용, 동일 Flask 앱을 서버리스로 실행)

**외부 API**
| API | 용도 |
|---|---|
| Google Gemini API (`gemini-3.5-flash`) | AI 여행지 추천 |
| Google Places API (New) | 숙박시설/맛집 검색 |
| 한국관광공사 TourAPI (KorService2) | 국내 행사/축제 정보 |
| Ticketmaster Discovery API | 해외 행사/이벤트 정보 |
| YouTube Data API v3 | 인기 여행 영상 검색 |

**배포**
- Vercel (Serverless Functions)
- GitHub (버전 관리)

## 프로젝트 구조
TripMate-AI/
    ├── api/
    │ └── index.py # Vercel 서버리스 함수 진입점 (Flask 앱)
    ├── server/ # API 로직 모듈
    │ ├── recommend.py # Gemini AI 여행지 추천
    │ ├── places.py # Google Places (숙박/맛집)
    │ ├── events.py # TourAPI / Ticketmaster (행사)
    │ ├── youtube.py # YouTube Data API (영상)
    │ └── cache.py # 24시간 파일 캐시
    ├── css/
    │ └── style.css
    ├── js/
    │ └── app.js # 화면 전환, API 호출, 저장 기능
    ├── images/
    ├── index.html
    ├── local_server.py # 로컬 개발용 Flask 서버
    ├── requirements.txt
    ├── vercel.json
    ├── .env.example
    └── .gitignore
## 로컬 실행 방법

### 1. 환경 준비
```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

### 2. API 키 설정
GEMINI_API_KEY=여기에_Places용_새_키_붙여넣기
GOOGLE_PLACES_API_KEY=여기에_Places용_새_키_붙여넣기
TOUR_API_KEY=여기에_발급받은_실제_키_붙여넣기
TICKETMASTER_API_KEY=여기에_발급받은_실제_키_붙여넣기
YOUTUBE_API_KEY=여기에_발급받은_실제_키_붙여넣기

### 3. 로컬 서버 실행
```bash
python local_server.py
```
브라우저에서 http://127.0.0.1:5000 접속

## 배포 방법 (Vercel)

```bash
vercel login
vercel          # 최초 배포 (Preview)
vercel --prod   # 프로덕션 배포
```

Vercel 대시보드 → Settings → Environment Variables에 위 5개 API 키를 등록해야 정상 동작합니다.

## 보안 안내

- API 키는 `.env` 파일로만 관리하며 `.gitignore`에 의해 Git에 포함되지 않습니다.
- `.env.example`은 값 없이 형식만 제공하여 다른 개발자가 필요한 키를 파악할 수 있도록 했습니다.
- 캐시 파일(`cache/`)도 Git에서 제외됩니다.

## 라이선스

경남 코디세이 미션 프로젝트 학습 목적으로 제작되었습니다.