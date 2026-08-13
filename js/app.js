// ===================================================
// TripMate AI - app.js
// STEP 7~13: 화면 전환 + 입력 폼 + AI 추천 + 행사 + 숙박/맛집 + 영상 + 저장 기능
// ===================================================

// 전체 앱 상태
const tripState = {
  startDate: null,
  endDate: null,
  domesticOrOverseas: "domestic",
  overseasRegion: null,
  country: null,
  city: null,
  tripStyle: null,
  recommendations: null,
  events: null,
  stays: null,
  foods: null,
  videos: null,
  viewOnly: false
};

const SAVED_TRIPS_KEY = "tripmate_saved_trips";

// ---------------------------------------------------
// 1. 화면 전환 함수
// ---------------------------------------------------
function showScreen(screenId) {
  const allScreens = document.querySelectorAll(".screen");
  allScreens.forEach((el) => el.classList.remove("active-screen"));

  const target = document.getElementById(screenId);
  if (target) {
    target.classList.add("active-screen");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else {
    console.error("존재하지 않는 화면 ID:", screenId);
  }
}

// ---------------------------------------------------
// 2. 상단 네비게이션 (MY TRIP / GUIDE)
// ---------------------------------------------------
function setupTopNav() {
  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      showScreen(targetId);
      if (targetId === "mytrip-section") {
        renderMyTripList();
      }
    });
  });

  const logoBtn = document.getElementById("logo-home-btn");
  if (logoBtn) {
    logoBtn.addEventListener("click", () => {
      showScreen("home-section");
    });
  }
}

// ---------------------------------------------------
// 3. HOME -> TRIP INPUT 이동
// ---------------------------------------------------
function setupHomeStartButton() {
  const startBtn = document.getElementById("start-trip-btn");
  startBtn.addEventListener("click", () => {
    showScreen("input-section");
  });
}

// ---------------------------------------------------
// 4. 국내/해외 선택에 따른 입력 필드 동적 표시
// ---------------------------------------------------
function setupRegionToggle() {
  const radios = document.querySelectorAll('input[name="domestic-overseas"]');
  const overseasRegionGroup = document.getElementById("overseas-region-group");
  const countryGroup = document.getElementById("country-group");
  const domesticCityGroup = document.getElementById("domestic-city-group");
  const overseasCityGroup = document.getElementById("overseas-city-group");

  const domesticCityInput = document.getElementById("domestic-city");
  const overseasCityInput = document.getElementById("overseas-city");

  function updateVisibility(selectedValue) {
    if (selectedValue === "overseas") {
      overseasRegionGroup.style.display = "block";
      countryGroup.style.display = "block";
      overseasCityGroup.style.display = "block";
      domesticCityGroup.style.display = "none";

      domesticCityInput.required = false;
      overseasCityInput.required = true;
    } else {
      overseasRegionGroup.style.display = "none";
      countryGroup.style.display = "none";
      overseasCityGroup.style.display = "none";
      domesticCityGroup.style.display = "block";

      domesticCityInput.required = true;
      overseasCityInput.required = false;
    }
  }

  radios.forEach((radio) => {
    radio.addEventListener("change", (e) => {
      updateVisibility(e.target.value);
    });
  });

  updateVisibility("domestic");
}

// ---------------------------------------------------
// 5. 폼 제출 처리 (입력 검증 + 상태 저장)
// ---------------------------------------------------
function showFormError(message) {
  const errorBox = document.getElementById("form-error");
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearFormError() {
  const errorBox = document.getElementById("form-error");
  errorBox.hidden = true;
  errorBox.textContent = "";
}

function setupTripForm() {
  const form = document.getElementById("trip-form");
  form.setAttribute("novalidate", "true");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    clearFormError();

    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    const domesticOrOverseas = document.querySelector(
      'input[name="domestic-overseas"]:checked'
    ).value;
    const overseasRegion = document.getElementById("overseas-region").value;
    const country = document.getElementById("country").value.trim();
    const domesticCity = document.getElementById("domestic-city").value.trim();
    const overseasCity = document.getElementById("overseas-city").value.trim();
    const tripStyle = document.getElementById("trip-style").value.trim();

    if (!startDate || !endDate) {
      showFormError("여행 날짜와 여행 지역을 입력해주세요.");
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      showFormError("여행 종료일은 시작일보다 빠를 수 없습니다.");
      return;
    }

    if (domesticOrOverseas === "domestic" && !domesticCity) {
      showFormError("여행 날짜와 여행 지역을 입력해주세요.");
      return;
    }

    if (domesticOrOverseas === "overseas") {
      if (!overseasRegion || !country || !overseasCity) {
        showFormError("여행 날짜와 여행 지역을 입력해주세요.");
        return;
      }
    }

    tripState.startDate = startDate;
    tripState.endDate = endDate;
    tripState.domesticOrOverseas = domesticOrOverseas;
    tripState.overseasRegion = domesticOrOverseas === "overseas" ? overseasRegion : null;
    tripState.country = domesticOrOverseas === "overseas" ? country : "대한민국";
    tripState.city = domesticOrOverseas === "overseas" ? overseasCity : domesticCity;
    tripState.tripStyle = tripStyle || null;

    tripState.viewOnly = false;

    console.log("여행 정보 저장 완료:", tripState);

    showScreen("recommend-section");
    fetchAiRecommendations();
  });
}

// ---------------------------------------------------
// 6. 결과 화면 간 다음 버튼 연결
// ---------------------------------------------------
function setupResultNavButtons() {
  const toEventsBtn = document.getElementById("to-events-btn");
  const toStayBtn = document.getElementById("to-stay-btn");
  const toFoodBtn = document.getElementById("to-food-btn");
  const toYoutubeBtn = document.getElementById("to-youtube-btn");
  const saveTripBtn = document.getElementById("save-trip-btn");

  toEventsBtn.addEventListener("click", () => {
    showScreen("events-section");
    if (tripState.viewOnly) {
      renderEvents(tripState.events);
    } else {
      fetchEvents();
    }
  });

  toStayBtn.addEventListener("click", () => {
    showScreen("stay-section");
    if (tripState.viewOnly) {
      renderPlaceList(tripState.stays, "stay-list");
    } else {
      fetchStays();
    }
  });

  toFoodBtn.addEventListener("click", () => {
    showScreen("food-section");
    if (tripState.viewOnly) {
      renderPlaceList(tripState.foods, "food-list");
    } else {
      fetchFoods();
    }
  });

  toYoutubeBtn.addEventListener("click", () => {
    showScreen("youtube-section");
    if (tripState.viewOnly) {
      renderVideos(tripState.videos);
    } else {
      fetchVideos();
    }
  });

  saveTripBtn.addEventListener("click", () => {
    saveCurrentTrip();
  });
}

// ---------------------------------------------------
// 7. AI 여행지 추천 API 호출 (STEP 8)
// ---------------------------------------------------
async function fetchAiRecommendations() {
  const loadingBox = document.getElementById("recommend-loading");
  const errorBox = document.getElementById("recommend-error");
  const listBox = document.getElementById("recommend-list");
  const nextBtn = document.getElementById("to-events-btn");

  errorBox.hidden = true;
  errorBox.textContent = "";
  listBox.innerHTML = "";
  nextBtn.hidden = true;
  loadingBox.hidden = false;

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        startDate: tripState.startDate,
        endDate: tripState.endDate,
        country: tripState.country,
        city: tripState.city,
        tripStyle: tripState.tripStyle,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "여행지 추천을 생성하지 못했습니다. 다시 시도해주세요.");
    }

    tripState.recommendations = data;
    renderRecommendations(data);
    nextBtn.hidden = false;
  } catch (err) {
    console.error("AI 추천 오류:", err);
    errorBox.textContent = err.message || "여행지 추천을 생성하지 못했습니다. 다시 시도해주세요.";
    errorBox.hidden = false;
  } finally {
    loadingBox.hidden = true;
  }
}

function renderRecommendations(data) {
  const listBox = document.getElementById("recommend-list");
  listBox.innerHTML = "";

  if (!data.places || data.places.length === 0) {
    listBox.innerHTML = '<div class="empty-message">해당 조건에 맞는 여행 정보를 찾지 못했습니다.</div>';
    return;
  }

  const summaryEl = document.createElement("p");
  summaryEl.className = "recommend-summary";
  summaryEl.textContent = data.destination_summary || "";
  summaryEl.style.marginBottom = "16px";
  summaryEl.style.color = "var(--color-text-muted)";
  listBox.appendChild(summaryEl);

  data.places.forEach((place) => {
    const card = document.createElement("div");
    card.className = "info-card";
    card.innerHTML = `
      <h3>${escapeHtml(place.name)}</h3>
      <p><strong>추천 이유:</strong> ${escapeHtml(place.reason)}</p>
      <p><strong>예상 체류 시간:</strong> ${escapeHtml(place.expected_duration)}</p>
      <p><strong>일정 적합성:</strong> ${escapeHtml(place.schedule_fit)}</p>
      <div class="card-meta">
        <span>${escapeHtml(place.highlight)}</span>
      </div>
    `;
    listBox.appendChild(card);
  });
}

function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ---------------------------------------------------
// 8-0. 행사(축제/이벤트) 조회 (STEP 10)
// ---------------------------------------------------
async function fetchEvents() {
  const loadingBox = document.getElementById("events-loading");
  const errorBox = document.getElementById("events-error");
  const listBox = document.getElementById("events-list");

  errorBox.hidden = true;
  errorBox.textContent = "";
  listBox.innerHTML = "";
  loadingBox.hidden = false;

  try {
    const response = await fetch("/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domesticOrOverseas: tripState.domesticOrOverseas,
        startDate: tripState.startDate,
        endDate: tripState.endDate,
        country: tripState.country,
        city: tripState.city,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "행사 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    }

    tripState.events = data.events;
    renderEvents(data.events);
  } catch (err) {
    console.error("행사 정보 오류:", err);
    errorBox.textContent = err.message || "행사 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.";
    errorBox.hidden = false;
  } finally {
    loadingBox.hidden = true;
  }
}

function renderEvents(events) {
  const listBox = document.getElementById("events-list");
  listBox.innerHTML = "";

  if (!events || events.length === 0) {
    listBox.innerHTML = '<div class="empty-message">해당 여행 기간에 예정된 행사 정보를 찾지 못했습니다.</div>';
    return;
  }

  events.forEach((ev) => {
    const dateText = ev.startDate
      ? `${ev.startDate}${ev.endDate ? " ~ " + ev.endDate : ""}`
      : "일정 정보 없음";

    const card = document.createElement("div");
    card.className = "info-card";
    card.innerHTML = `
      <h3>${escapeHtml(ev.title)}</h3>
      <p>${escapeHtml(ev.place)}</p>
      <div class="card-meta">
        <span>${escapeHtml(dateText)}</span>
        ${ev.sourceUrl ? `<a href="${ev.sourceUrl}" target="_blank" rel="noopener">자세히 보기</a>` : ""}
      </div>
    `;
    listBox.appendChild(card);
  });
}

// ---------------------------------------------------
// 8-1. 숙박시설 조회 (STEP 9)
// ---------------------------------------------------
async function fetchStays() {
  const loadingBox = document.getElementById("stay-loading");
  const errorBox = document.getElementById("stay-error");
  const listBox = document.getElementById("stay-list");

  errorBox.hidden = true;
  errorBox.textContent = "";
  listBox.innerHTML = "";
  loadingBox.hidden = false;

  try {
    const response = await fetch("/api/stays", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country: tripState.country,
        city: tripState.city,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "숙박 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    }

    tripState.stays = data.stays;
    renderPlaceList(data.stays, "stay-list");
  } catch (err) {
    console.error("숙박 정보 오류:", err);
    errorBox.textContent = err.message || "숙박 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.";
    errorBox.hidden = false;
  } finally {
    loadingBox.hidden = true;
  }
}

// ---------------------------------------------------
// 8-2. 맛집 조회 (STEP 9)
// ---------------------------------------------------
async function fetchFoods() {
  const loadingBox = document.getElementById("food-loading");
  const errorBox = document.getElementById("food-error");
  const listBox = document.getElementById("food-list");

  errorBox.hidden = true;
  errorBox.textContent = "";
  listBox.innerHTML = "";
  loadingBox.hidden = false;

  try {
    const response = await fetch("/api/foods", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country: tripState.country,
        city: tripState.city,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "맛집 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    }

    tripState.foods = data.foods;
    renderPlaceList(data.foods, "food-list");
  } catch (err) {
    console.error("맛집 정보 오류:", err);
    errorBox.textContent = err.message || "맛집 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.";
    errorBox.hidden = false;
  } finally {
    loadingBox.hidden = true;
  }
}

// 숙박/맛집 공통 카드 렌더링 함수
function renderPlaceList(places, containerId) {
  const listBox = document.getElementById(containerId);
  listBox.innerHTML = "";

  if (!places || places.length === 0) {
    listBox.innerHTML = '<div class="empty-message">해당 조건에 맞는 정보를 찾지 못했습니다.</div>';
    return;
  }

  places.forEach((place) => {
    const ratingText = place.rating
      ? `⭐ ${place.rating} (리뷰 ${place.userRatingCount ?? 0}개)`
      : "평점 정보 없음";

    const card = document.createElement("div");
    card.className = "info-card";
    card.innerHTML = `
      <h3>${escapeHtml(place.name)}</h3>
      <p>${escapeHtml(place.address)}</p>
      <div class="card-meta">
        <span>${escapeHtml(ratingText)}</span>
        ${place.mapUrl ? `<a href="${place.mapUrl}" target="_blank" rel="noopener">지도에서 보기</a>` : ""}
      </div>
    `;
    listBox.appendChild(card);
  });
}

// ---------------------------------------------------
// 8-3. 인기 여행 영상 TOP 3 조회 (STEP 11)
// ---------------------------------------------------
async function fetchVideos() {
  const loadingBox = document.getElementById("youtube-loading");
  const errorBox = document.getElementById("youtube-error");
  const listBox = document.getElementById("youtube-list");

  errorBox.hidden = true;
  errorBox.textContent = "";
  listBox.innerHTML = "";
  loadingBox.hidden = false;

  try {
    const foodNames = (tripState.foods || []).map((f) => f.name).filter(Boolean);

    const response = await fetch("/api/videos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country: tripState.country,
        city: tripState.city,
        foodNames: foodNames,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "영상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    }

    tripState.videos = data.videos;
    renderVideos(data.videos);
  } catch (err) {
    console.error("영상 정보 오류:", err);
    errorBox.textContent = err.message || "영상 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.";
    errorBox.hidden = false;
  } finally {
    loadingBox.hidden = true;
  }
}

function renderVideos(videos) {
  const listBox = document.getElementById("youtube-list");
  listBox.innerHTML = "";

  if (!videos || videos.length === 0) {
    listBox.innerHTML = '<div class="empty-message">관련된 여행 영상을 찾지 못했습니다.</div>';
    return;
  }

  videos.forEach((video) => {
    const card = document.createElement("div");
    card.className = "info-card";
    card.innerHTML = `
      ${video.thumbnail ? `<img class="thumb" src="${video.thumbnail}" alt="${escapeHtml(video.title)}" />` : ""}
      <h3>${escapeHtml(video.title)}</h3>
      <p>${escapeHtml(video.channel)}</p>
      <div class="card-meta">
        <a href="${video.videoUrl}" target="_blank" rel="noopener">YouTube에서 보기</a>
      </div>
    `;
    listBox.appendChild(card);
  });
}

// ---------------------------------------------------
// 8-4. 여행 계획 저장 기능 (STEP 13, 보너스)
// ---------------------------------------------------
function getSavedTrips() {
  try {
    const raw = localStorage.getItem(SAVED_TRIPS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error("저장된 여행 목록을 불러오지 못했습니다:", e);
    return [];
  }
}

function setSavedTrips(trips) {
  try {
    localStorage.setItem(SAVED_TRIPS_KEY, JSON.stringify(trips));
  } catch (e) {
    console.error("여행 계획 저장 실패:", e);
  }
}

function saveCurrentTrip() {
  if (!tripState.city) {
    alert("저장할 여행 정보가 없습니다. 먼저 여행 정보를 입력해주세요.");
    return;
  }

  const trips = getSavedTrips();
  const newTrip = {
    id: `trip_${Date.now()}`,
    savedAt: new Date().toISOString(),
    visited: false,
    startDate: tripState.startDate,
    endDate: tripState.endDate,
    domesticOrOverseas: tripState.domesticOrOverseas,
    country: tripState.country,
    city: tripState.city,
    tripStyle: tripState.tripStyle,
    recommendations: tripState.recommendations,
    events: tripState.events,
    stays: tripState.stays,
    foods: tripState.foods,
    videos: tripState.videos,
  };

  trips.unshift(newTrip);
  setSavedTrips(trips);
  alert("여행 계획이 저장되었습니다. 'MY TRIP'에서 확인하실 수 있습니다.");
}

function toggleTripVisited(tripId) {
  const trips = getSavedTrips();
  const updated = trips.map((t) =>
    t.id === tripId ? { ...t, visited: !t.visited } : t
  );
  setSavedTrips(updated);
  renderMyTripList();
}

function deleteTrip(tripId) {
  const trips = getSavedTrips();
  const updated = trips.filter((t) => t.id !== tripId);
  setSavedTrips(updated);
  renderMyTripList();
}

function renderMyTripList() {
  const listBox = document.getElementById("mytrip-list");
  const emptyBox = document.getElementById("mytrip-empty");
  const trips = getSavedTrips();

  listBox.innerHTML = "";

  if (!trips || trips.length === 0) {
    emptyBox.hidden = false;
    return;
  }
  emptyBox.hidden = true;

  trips.forEach((trip) => {
    const dateText =
      trip.startDate && trip.endDate
        ? `${trip.startDate} ~ ${trip.endDate}`
        : "날짜 정보 없음";
    const placeCount =
      trip.recommendations && trip.recommendations.places
        ? trip.recommendations.places.length
        : 0;

    const card = document.createElement("div");
    card.className = "info-card";
    card.innerHTML = `
      <h3>${escapeHtml(trip.city || "여행지 미상")} (${escapeHtml(trip.country || "")})</h3>
      <p>${escapeHtml(dateText)}</p>
      <p>추천 여행지 ${placeCount}곳 저장됨</p>
      <div class="card-meta">
        <span>${trip.visited ? "✅ 방문 완료" : "🕓 방문 예정"}</span>
      </div>
    `;

    const btnRow = document.createElement("div");
    btnRow.style.marginTop = "12px";
    btnRow.style.display = "flex";
    btnRow.style.gap = "8px";
    btnRow.style.flexWrap = "wrap";

    const viewBtn = document.createElement("button");
    viewBtn.className = "primary-btn";
    viewBtn.style.marginTop = "0";
    viewBtn.style.padding = "10px 16px";
    viewBtn.textContent = "상세보기";
    viewBtn.addEventListener("click", () => loadSavedTrip(trip.id));

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "secondary-btn";
    toggleBtn.style.marginTop = "0";
    toggleBtn.textContent = trip.visited ? "방문 예정으로 변경" : "방문 완료로 표시";
    toggleBtn.addEventListener("click", () => toggleTripVisited(trip.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "secondary-btn";
    deleteBtn.style.marginTop = "0";
    deleteBtn.textContent = "삭제";
    deleteBtn.addEventListener("click", () => {
      if (confirm("이 여행 계획을 삭제하시겠습니까?")) {
        deleteTrip(trip.id);
      }
    });

    btnRow.appendChild(viewBtn);
    btnRow.appendChild(toggleBtn);
    btnRow.appendChild(deleteBtn);
    card.appendChild(btnRow);

    listBox.appendChild(card);
  });
}

// 저장된 여행 계획을 재조회 없이 그대로 불러와서 결과 화면들에 표시
function loadSavedTrip(tripId) {
  const trips = getSavedTrips();
  const trip = trips.find((t) => t.id === tripId);
  if (!trip) {
    alert("저장된 여행 정보를 찾을 수 없습니다.");
    return;
  }

  tripState.startDate = trip.startDate;
  tripState.endDate = trip.endDate;
  tripState.domesticOrOverseas = trip.domesticOrOverseas;
  tripState.country = trip.country;
  tripState.city = trip.city;
  tripState.tripStyle = trip.tripStyle;
  tripState.recommendations = trip.recommendations;
  tripState.events = trip.events;
  tripState.stays = trip.stays;
  tripState.foods = trip.foods;
  tripState.videos = trip.videos;
  tripState.viewOnly = true;

  showScreen("recommend-section");

  const nextBtn = document.getElementById("to-events-btn");
  const errorBox = document.getElementById("recommend-error");
  const loadingBox = document.getElementById("recommend-loading");
  errorBox.hidden = true;
  loadingBox.hidden = true;
  nextBtn.hidden = false;

  renderRecommendations(trip.recommendations || { places: [] });
}

// ---------------------------------------------------
// 9. 초기화
// ---------------------------------------------------
function initApp() {
  setupTopNav();
  setupHomeStartButton();
  setupRegionToggle();
  setupTripForm();
  setupResultNavButtons();
}

document.addEventListener("DOMContentLoaded", initApp);