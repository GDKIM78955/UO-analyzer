import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime, timedelta, timezone
import calendar

# SSL 보안 경고 무시 (일부 도매 사이트 크롤링 오류 방지)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="스마트스토어 위탁판매 & 장부 매니저", layout="wide")

# 한국 시간(KST) 기준 오늘 날짜 계산
KST = timezone(timedelta(hours=9))
today = datetime.now(KST).date()

st.title("🛒 스마트스토어 위탁판매 & 수익장부·인포그래픽 통합 매니저")
st.write(
    f"📅 **오늘 날짜: {today.strftime('%Y년 %m월 %d일')}** | "
    "시즌 소싱 캘린더, 도매처 품절 스캔, **수익·지출 장부 관리**, **5종 블로그 인포그래픽 제작(복사 & PNG 저장)**을 한곳에서 관리합니다."
)

# ==========================================
# 1. 대한민국 이커머스 핵심 기념일 & 시즌 소싱 데이터베이스
# ==========================================
SEASONAL_EVENTS = [
    {"month": 1, "day": 1, "name": "신정 / 새해 다짐 시즌", "items": "다이어리, 플래너, 홈트레이닝 용품, 독서대, 영양제 케이스", "keywords": "새해선물, 갓생템, 다이어리꾸미기, 홈트기구"},
    {"month": 1, "day": 25, "name": "설날 명절 선물 대목", "items": "건강기능식품, 과일/한우 선물세트 포장재, 용돈봉투, 효도 안마기, 차량용 거치대", "keywords": "설날선물세트, 부모님명절선물, 센스있는용돈봉투"},
    {"month": 2, "day": 14, "name": "발렌타인데이 / 졸업·입학식", "items": "초콜릿 DIY 키트, 남성 지갑/벨트, 꽃다발 비누꽃, 입학 백팩, 학용품 세트", "keywords": "발렌타인데이선물, 남자친구선물, 졸업식꽃다발, 신학기책가방"},
    {"month": 3, "day": 2, "name": "신학기 개학 / 봄맞이 대청소", "items": "어린이 네임스티커, 수저통, 자취방 수납함, 침구 정리함, 먼지떨이/청소용품", "keywords": "어린이집준비물, 자취방수납, 봄맞이인테리어"},
    {"month": 3, "day": 14, "name": "화이트데이", "items": "사탕/디저트 선물상자, 쥬얼리 보관함, 여성 파우치, 무드등, 향수 공병", "keywords": "화이트데이선물, 여자친구선물추천, 감성무드등"},
    {"month": 4, "day": 5, "name": "본격 봄 캠핑 & 나들이·피크닉 오픈", "items": "피크닉 매트, 감성 우드 롤테이블, 캠핑 의자, 보냉백, 차량용 피크닉 용품", "keywords": "감성캠핑용품, 한강피크닉세트, 방수피크닉매트"},
    {"month": 5, "day": 5, "name": "어린이날 (가정의 달 빅시즌)", "items": "완구/장난감, 보드게임, 어린이 킥보드, 역할놀이 세트, 아동용 카메라", "keywords": "어린이날선물추천, 조카선물, 유아장난감"},
    {"month": 5, "day": 8, "name": "어버이날 / 스승의날 (가정의 달 최고 대목)", "items": "카네이션 비누꽃/용돈박스, 손목/어깨 마사지기, 건강차 세트, 감사패/토퍼", "keywords": "어버이날용돈박스, 부모님선물추천, 스승의날선물"},
    {"month": 5, "day": 21, "name": "부부의날 / 성년의날", "items": "커플 잠옷, 커플 머그컵, 장미꽃 인테리어 소품, 미니 향수, 와인잔 세트", "keywords": "부부의날선물, 성년의날선물, 커플아이템"},
    {"month": 6, "day": 15, "name": "초여름 & 장마철 사전 대비", "items": "초경량 양산/우산, 제습제, 레인부츠, 신발 건조기, 손선풍기, 쿨매트", "keywords": "장마철필수템, 자외선차단양산, 휴대용선풍기, 냉감패드"},
    {"month": 7, "day": 20, "name": "여름 휴가철 / 물놀이·바캉스 피크", "items": "방수팩, 구명조끼, 대형 튜브, 아쿠아슈즈, 비치타월, 캐리어 파우치, 모기퇴치기", "keywords": "물놀이용품, 해외여행준비물, 캐리어정리파우치"},
    {"month": 9, "day": 15, "name": "가을 캠핑 오픈 & 추석 명절 대목", "items": "명절 선물세트, 용돈박스, 한복 소품, 캠핑 화로대, 캠핑 랜턴, 침낭", "keywords": "추석선물추천, 가을캠핑용품, 감성랜턴, 불멍화로대"},
    {"month": 10, "day": 31, "name": "할로윈 데이 & 가을 단풍 나들이", "items": "어린이 코스튬 의상, 파티 풍선/가랜드, 호박 바구니, 등산 스틱, 보온병", "keywords": "할로윈코스튬, 어린이집할로윈, 홈파티용품, 등산용품"},
    {"month": 11, "day": 11, "name": "빼빼로데이 / 수능 응원 선물", "items": "빼빼로 포장 키트, 합격 엿/초콜릿 상자, 수험생 방석, 보온 도시락, 무릎담요", "keywords": "빼빼로데이포장, 수능응원선물, 수험생필수템"},
    {"month": 11, "day": 25, "name": "첫눈 & 겨울 한파 월동준비 시작", "items": "충전식 손난로, 발난로, 온수매트, 방풍 비닐, 가습기, 차량용 성에제거기", "keywords": "겨울필수템, 사무실발난로, 휴대용손난로, 대용량가습기"},
    {"month": 12, "day": 25, "name": "크리스마스 & 연말 홈파티 대목", "items": "크리스마스 미니 트리, LED 전구, 오너먼트, 산타 양말, 와인 오프너, 파티 테이블보", "keywords": "크리스마스트리세트, 연말홈파티소품, 크리스마스선물"},
]


def get_upcoming_events(ref_date):
    upcoming = []
    for ev in SEASONAL_EVENTS:
        try_date = datetime(ref_date.year, ev["month"], ev["day"]).date()
        if try_date < ref_date:
            try_date = datetime(ref_date.year + 1, ev["month"], ev["day"]).date()

        d_day = (try_date - ref_date).days
        prep_start = try_date - timedelta(days=28)
        prep_end = try_date - timedelta(days=21)

        if d_day <= 7:
            action_status = "🔥 [막바지 당일발송 피크] 지금 즉시 재고/품절 집중 관리!"
            urgency = "high"
        elif 14 <= d_day <= 35:
            action_status = "🚨 [황금 소싱 타이밍! (3~4주 전)] 지금 바로 상품 등록 & 블로그 포스팅하세요!"
            urgency = "golden"
        elif 7 < d_day < 14:
            action_status = "⚡ [집중 홍보 주간 (1~2주 전)] 블로그/카페 인포그래픽 홍보글을 집중 업로드하세요!"
            urgency = "medium"
        else:
            action_status = f"⏳ 사전 준비 대기 (권장 소싱 시작일: {prep_start.strftime('%m월 %d일')}부터)"
            urgency = "normal"

        upcoming.append({
            "event_date": try_date,
            "d_day": d_day,
            "name": ev["name"],
            "items": ev["items"],
            "keywords": ev["keywords"],
            "prep_window": f"{prep_start.strftime('%m/%d')} ~ {prep_end.strftime('%m/%d')}",
            "action_status": action_status,
            "urgency": urgency,
            "month": ev["month"],
            "day": ev["day"],
        })

    return sorted(upcoming, key=lambda x: x["d_day"])


upcoming_list = get_upcoming_events(today)

# 상단 고정: 3~4주 전 소싱 골든타임 자동 알림 배너
golden_events = [e for e in upcoming_list if e["d_day"] <= 42]
if golden_events:
    with st.container(border=True):
        st.markdown("### 🔔 [자동 소싱 레이더] 지금 즉시 판매 준비해야 할 시즌/기념일 알림")
        st.caption("스마트스토어 상위노출과 블로그 검색 반영에는 약 3~4주가 걸립니다. 아래 일정을 보고 미리 상품을 등록하세요!")
        for ge in golden_events[:3]:
            if ge["urgency"] == "golden":
                st.error(
                    f"**🎯 D-{ge['d_day']} | {ge['name']} ({ge['event_date'].strftime('%m월 %d일')}) — 지금이 3~4주 전 황금 소싱 타이밍입니다!**\n\n"
                    f"- **📦 추천 소싱 상품군:** {ge['items']}\n"
                    f"- **🔑 블로그/스토어 핵심 키워드:** `{ge['keywords']}`"
                )
            elif ge["urgency"] in ("medium", "high"):
                st.warning(
                    f"**⚡ D-{ge['d_day']} | {ge['name']} ({ge['event_date'].strftime('%m월 %d일')}) — {ge['action_status']}**\n\n"
                    f"- **📦 주력 판매 상품군:** {ge['items']} | **🔑 추천 키워드:** `{ge['keywords']}`"
                )
            else:
                st.info(
                    f"**📅 D-{ge['d_day']} | {ge['name']} ({ge['event_date'].strftime('%m월 %d일')})** — 권장 소싱 시작일: `{ge['prep_window']}`\n\n"
                    f"- **📦 미리 봐둘 상품군:** {ge['items']}"
                )

# ==========================================
# 2. 구글 시트 자동 연동 설정
# ==========================================
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/12g0e-ER14x2cyx2ipEAluZjHU5FAxUNpKIrg6sP1jiI"
gid = "0"
csv_url = f"{DEFAULT_SHEET_URL}/export?format=csv&gid={gid}"


@st.cache_data(ttl=60, show_spinner=False)
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df


# ==========================================
# 3. 도매처 링크 생존 & 품절 감지 함수
# ==========================================
def check_wholesale_status(url):
    if not url or pd.isna(url) or not str(url).startswith("http"):
        return "⚪ 링크 미입력", "도매처 URL을 입력해주세요."

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    sold_out_keywords = [
        "품절",
        "일시품절",
        "판매종료",
        "판매중지",
        "재고없음",
        "구매불가",
        "단종",
        "삭제된 상품",
        "존재하지 않는 상품",
        "현재 판매중인 상품이 아닙니다",
        "판매가 종료",
        "sold out",
        "out of stock",
    ]

    try:
        resp = requests.get(str(url), headers=headers, timeout=8, verify=False)
        if resp.status_code == 404:
            return "🔴 링크 삭제 (404)", "페이지가 사라졌습니다. 즉시 스토어 품절 처리 필요!"
        elif resp.status_code != 200:
            return f"🟡 접속 확인 필요 ({resp.status_code})", "사이트 보안 또는 일시적 오류 (직접 클릭해 확인 권장)"

        soup = BeautifulSoup(resp.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text(separator=" ").lower()

        detected = [kw for kw in sold_out_keywords if kw in page_text]
        if detected:
            return "🔴 품절/종료 의심", f"감지된 단어: {', '.join(detected[:3])}"

        return "🟢 정상 판매중", "특이사항 없음 (발주 가능)"

    except Exception as e:
        return "🟡 연결 지연/오류", f"수동 확인 필요 ({type(e).__name__})"


# ==========================================
# 4. 데이터 로드 및 5대 핵심 탭 구성
# ==========================================
try:
    with st.spinner("구글 시트 데이터를 불러오는 중입니다..."):
        try:
            df = load_data(csv_url)
        except Exception:
            df = pd.DataFrame()

    required_cols = ["상품명", "도매처링크", "도매원가", "판매가"]
    if df.empty or not all(col in df.columns for col in required_cols):
        st.info(
            "💡 구글 시트 우측 상단의 **[공유] -> '링크가 있는 모든 사용자(뷰어)'**로 설정하시면 시트 데이터가 실시간 연동됩니다. "
            "(현재는 시트에 세팅된 기본 데이터와 동일한 내장 데이터로 표시 중입니다.)"
        )
        df = pd.DataFrame([
            {
                "상품명": "캠핑용 초경량 감성 우드 롤테이블",
                "도매처명": "도매꾹",
                "도매처링크": "https://domeggook.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 16500,
                "판매가": 28900,
                "배송비": 3000,
                "블로그홍보링크": "https://blog.naver.com/",
                "누적판매수량": 18,
                "광고및기타지출": 15000,
            },
            {
                "상품명": "차량용 무선 초강력 미니 청소기",
                "도매처명": "오너클랜",
                "도매처링크": "https://ownerclan.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 12000,
                "판매가": 21900,
                "배송비": 3000,
                "블로그홍보링크": "https://cafe.naver.com/",
                "누적판매수량": 25,
                "광고및기타지출": 20000,
            },
            {
                "상품명": "충전식 손난로 보조배터리 10000mAh",
                "도매처명": "도매매",
                "도매처링크": "https://domemedb.domeggook.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 8900,
                "판매가": 17900,
                "배송비": 3000,
                "블로그홍보링크": "https://blog.naver.com/",
                "누적판매수량": 42,
                "광고및기타지출": 30000,
            },
            {
                "상품명": "크리스마스 미니 트리 LED 풀세트",
                "도매처명": "도매꾹",
                "도매처링크": "https://domeggook.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 14000,
                "판매가": 26900,
                "배송비": 3000,
                "블로그홍보링크": "https://blog.naver.com/",
                "누적판매수량": 30,
                "광고및기타지출": 25000,
            },
            {
                "상품명": "겨울 방한 가습기 대용량 무드등",
                "도매처명": "오너클랜",
                "도매처링크": "https://ownerclan.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 11500,
                "판매가": 22500,
                "배송비": 3000,
                "블로그홍보링크": "https://cafe.naver.com/",
                "누적판매수량": 15,
                "광고및기타지출": 10000,
            },
        ])

    # 숫자형 컬럼 안전 변환 (통화 기호나 콤마가 있어도 숫자로 자동 인식)
    def clean_num(series, default=0):
        if series is None:
            return pd.Series([default] * len(df))
        return pd.to_numeric(series.astype(str).str.replace(r"[^0-9.-]", "", regex=True), errors="coerce").fillna(default)

    df["도매원가_num"] = clean_num(df.get("도매원가"), 0)
    df["판매가_num"] = clean_num(df.get("판매가"), 0)
    df["누적판매수량_num"] = clean_num(df.get("누적판매수량"), 0)
    df["광고및기타지출_num"] = clean_num(df.get("광고및기타지출"), 0)

    tab_cal, tab_scan, tab_ledger, tab_info, tab_raw = st.tabs([
        "📅 1. 시즌/기념일 소싱 캘린더",
        "🚨 2. 도매처 품절/단종 스캔",
        "💰 3. 수익·지출 장부 대시보드",
        "🎨 4. 5종 인포그래픽 스튜디오 (복사 & PNG)",
        "📊 5. 구글 시트 원본 & 바로가기",
    ])

    # ==========================================
    # TAB 1: 시즌/기념일 소싱 캘린더
    # ==========================================
    with tab_cal:
        st.subheader("📅 연간 기념일 소싱 로드맵 & 월별 달력")
        st.write(
            "위탁판매는 **기념일 3~4주 전에 상품을 소싱해 스토어에 등록하고 블로그/카페에 홍보글을 올려야** "
            "대목 당일에 검색 상위노출로 주문이 터집니다."
        )

        col_cal_left, col_cal_right = st.columns([1.05, 1.35], gap="large")

        with col_cal_left:
            st.markdown("#### 🗓️ 월별 기념일 & 소싱 달력 보기")
            c_yr, c_mo = st.columns(2)
            with c_yr:
                sel_year = st.selectbox("연도 선택", [today.year, today.year + 1], index=0)
            with c_mo:
                sel_month = st.selectbox("월 선택 (달력 확인)", list(range(1, 13)), index=today.month - 1, format_func=lambda x: f"{x}월")

            month_events = {e["day"]: e["name"] for e in SEASONAL_EVENTS if e["month"] == sel_month}

            prep_alerts_in_month = []
            for e in SEASONAL_EVENTS:
                ev_dt = datetime(sel_year, e["month"], e["day"]).date()
                prep_dt = ev_dt - timedelta(days=25)
                if prep_dt.month == sel_month:
                    prep_alerts_in_month.append((prep_dt.day, e["name"], f"{e['month']}/{e['day']}", e["items"]))

            cal_matrix = calendar.monthcalendar(sel_year, sel_month)
            rows_html = ""
            for week in cal_matrix:
                rows_html += "<tr>"
                for idx_day, d in enumerate(week):
                    if d == 0:
                        rows_html += '<td class="empty-cell"></td>'
                    else:
                        is_today = (sel_year == today.year and sel_month == today.month and d == today.day)
                        has_ev = d in month_events
                        has_prep = any(p[0] == d for p in prep_alerts_in_month)

                        bg_class = "cell-today" if is_today else ("cell-event" if has_ev else ("cell-prep" if has_prep else "cell-normal"))
                        day_color = "#2563eb" if idx_day == 5 else ("#dc2626" if idx_day == 6 else "#1e293b")

                        badge_html = ""
                        if is_today:
                            badge_html += '<div class="badge badge-today">오늘</div>'
                        if has_ev:
                            badge_html += '<div class="badge badge-event">🎉기념일</div>'
                        if has_prep:
                            badge_html += '<div class="badge badge-prep">🚨소싱시작</div>'

                        rows_html += f'<td class="{bg_class}"><div class="day-num" style="color:{day_color};">{d}</div>{badge_html}</td>'
                rows_html += "</tr>"

            calendar_component_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Malgun Gothic', sans-serif; background-color: transparent; }}
                .cal-table {{ width: 100%; table-layout: fixed; border-collapse: collapse; background-color: #ffffff; border-radius: 10px; overflow: hidden; border: 2px solid #334155; box-shadow: 0 2px 6px rgba(0,0,0,0.12); }}
                .cal-table th {{ background-color: #1e293b; color: #ffffff; padding: 10px 0; font-size: 13px; font-weight: 800; border: 1px solid #334155; text-align: center; }}
                .cal-table td {{ height: 60px; vertical-align: top; padding: 6px 4px; border: 1px solid #e2e8f0; text-align: center; box-sizing: border-box; }}
                .empty-cell {{ background-color: #f8fafc; }}
                .cell-normal {{ background-color: #ffffff; }}
                .cell-today {{ background-color: #dcfce7; border: 2px solid #16a34a !important; }}
                .cell-event {{ background-color: #fee2e2; }}
                .cell-prep {{ background-color: #fef3c7; }}
                .day-num {{ font-size: 13px; font-weight: 800; margin-bottom: 3px; }}
                .badge {{ font-size: 10px; font-weight: 800; padding: 2px 3px; border-radius: 4px; margin-top: 2px; line-height: 1.2; word-break: keep-all; }}
                .badge-today {{ background-color: #16a34a; color: #ffffff; }}
                .badge-event {{ color: #dc2626; }}
                .badge-prep {{ color: #b45309; }}
            </style>
            </head>
            <body>
                <table class="cal-table">
                    <thead>
                        <tr>
                            <th>월</th><th>화</th><th>수</th><th>목</th><th>금</th>
                            <th style="color:#93c5fd;">토</th><th style="color:#fca5a5;">일</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </body>
            </html>
            """
            cal_height = 65 + (len(cal_matrix) * 64)
            components.html(calendar_component_html, height=cal_height, scrolling=False)
            st.caption("🟥 빨간칸: 해당 월 기념일 당일 | 🟨 노란칸: 다음 대목 3~4주 전 소싱 시작일 | 🟩 초록칸: 오늘")

            if month_events:
                st.markdown(f"##### 🎉 {sel_month}월 당월 기념일")
                for e_day, e_name in month_events.items():
                    st.info(f"**{sel_month}월 {e_day}일:** {e_name}")

            if prep_alerts_in_month:
                st.markdown(f"##### 🚨 {sel_month}월에 미리 소싱 시작해야 할 항목 (3~4주 전 알림)")
                for p_day, p_name, p_date_str, p_items in prep_alerts_in_month:
                    st.warning(
                        f"**{sel_month}월 {p_day}일경 준비 시작** ➡️ **{p_name} ({p_date_str}) 대비**\n\n"
                        f"- **추천 소싱 품목:** {p_items}"
                    )

        with col_cal_right:
            st.markdown("#### 📋 다가오는 시즌/기념일 전체 스케줄 (D-Day 순)")
            schedule_rows = []
            for ev in upcoming_list:
                schedule_rows.append({
                    "D-Day": f"D-{ev['d_day']}",
                    "기념일 날짜": ev["event_date"].strftime("%Y-%m-%d"),
                    "시즌 / 기념일명": ev["name"],
                    "권장 소싱 기간 (3~4주 전)": ev["prep_window"],
                    "현재 액션 상태": ev["action_status"],
                    "추천 소싱 상품군": ev["items"],
                    "블로그 추천 키워드": ev["keywords"],
                })
            df_sched = pd.DataFrame(schedule_rows)
            st.dataframe(df_sched, use_container_width=True, hide_index=True, height=560)

    # ==========================================
    # TAB 2: 도매처 품절/단종 일괄 스캔
    # ==========================================
    with tab_scan:
        st.subheader("🔍 등록 상품 도매처 생존 및 품절 일괄 점검")
        st.write("주문 접수 시 또는 매일 아침 버튼을 눌러 도매처 링크가 살아있는지 한 번에 검사하세요.")

        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            scan_trigger = st.button("🚀 전체 상품 도매처 상태 실시간 스캔 실행", type="primary", use_container_width=True)
        with col_btn2:
            if st.button("🔄 시트 데이터 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        if scan_trigger:
            results = []
            progress_bar = st.progress(0, text="도매처 링크 상태를 점검하고 있습니다...")
            total_items = len(df)

            for idx, row in df.iterrows():
                p_name = str(row.get("상품명", f"상품 {idx+1}"))
                w_name = str(row.get("도매처명", "-"))
                w_url = str(row.get("도매처링크", ""))
                s_url = str(row.get("스마트스토어링크", ""))
                b_url = str(row.get("블로그홍보링크", ""))
                w_price = int(row.get("도매원가_num", 0))
                s_price = int(row.get("판매가_num", 0))

                status_badge, detail_msg = check_wholesale_status(w_url)

                results.append({
                    "No": idx + 1,
                    "상태": status_badge,
                    "상품명": p_name,
                    "도매처": w_name,
                    "도매원가": f"{w_price:,}원",
                    "스토어판매가": f"{s_price:,}원",
                    "점검 결과 상세": detail_msg,
                    "도매처 링크": w_url,
                    "내 스토어": s_url,
                    "블로그/카페": b_url,
                })
                progress_bar.progress((idx + 1) / total_items, text=f"[{idx+1}/{total_items}] {p_name} 점검 완료")

            df_res = pd.DataFrame(results)

            ok_cnt = sum(1 for r in results if "🟢" in r["상태"])
            danger_cnt = sum(1 for r in results if "🔴" in r["상태"])
            warn_cnt = sum(1 for r in results if "🟡" in r["상태"])

            m1, m2, m3 = st.columns(3)
            m1.metric("🟢 정상 판매 가능", f"{ok_cnt}건")
            m2.metric("🔴 품절/단종 위험 (즉시 확인)", f"{danger_cnt}건")
            m3.metric("🟡 수동 확인 필요", f"{warn_cnt}건")

            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "도매처 링크": st.column_config.LinkColumn("도매처", display_text="🔗 도매처 열기"),
                    "내 스토어": st.column_config.LinkColumn("스마트스토어", display_text="🏪 스토어 열기"),
                    "블로그/카페": st.column_config.LinkColumn("홍보글", display_text="📝 홍보글 열기"),
                },
            )

    # ==========================================
    # TAB 3: 수익·지출 장부 대시보드 (가로형 랭킹 바 적용으로 세로 글씨 문제 완벽 해결)
    # ==========================================
    with tab_ledger:
        st.subheader("💰 스마트스토어 수익·지출 통합 장부 대시보드")
        st.write(
            "구글 시트에 입력된 `도매원가`, `판매가`, `누적판매수량`, `광고및기타지출`을 기반으로 "
            "**총매출·총지출·최종 순수익**을 실시간으로 정산합니다."
        )

        col_fee_opt, col_extra_exp = st.columns(2)
        with col_fee_opt:
            ledger_fee_rate = st.number_input("📉 정산 기준 네이버 수수료율 (%)", value=5.6, step=0.1, key="ledger_fee")
        with col_extra_exp:
            extra_fixed_cost = st.number_input("🧾 이번 달 추가 고정 지출 (택배박스/프로그램비 등, 원)", value=0, step=5000)

        ledger_rows = []
        total_rev = 0
        total_wholesale_cost = 0
        total_naver_fee = 0
        total_ad_cost = 0

        for idx, row in df.iterrows():
            p_name = str(row.get("상품명", f"상품 {idx+1}"))
            w_name = str(row.get("도매처명", "-"))
            w_p = int(row.get("도매원가_num", 0))
            s_p = int(row.get("판매가_num", 0))
            qty = int(row.get("누적판매수량_num", 0))
            ad_c = int(row.get("광고및기타지출_num", 0))

            unit_fee = int(round(s_p * (ledger_fee_rate / 100)))
            unit_margin = s_p - w_p - unit_fee

            item_rev = s_p * qty
            item_w_cost = w_p * qty
            item_fee_cost = unit_fee * qty
            item_total_exp = item_w_cost + item_fee_cost + ad_c
            item_net_profit = item_rev - item_total_exp
            item_roi = (item_net_profit / item_rev * 100) if item_rev > 0 else 0.0

            total_rev += item_rev
            total_wholesale_cost += item_w_cost
            total_naver_fee += item_fee_cost
            total_ad_cost += ad_c

            ledger_rows.append({
                "상품명": p_name,
                "도매처": w_name,
                "판매단가": f"{s_p:,}원",
                "개당순마진": f"{unit_margin:,}원",
                "판매수량_num": qty,
                "판매수량": f"{qty:,}개",
                "총매출액 (수익)": f"{item_rev:,}원",
                "도매원가 합계": f"{item_w_cost:,}원",
                "수수료 합계": f"{item_fee_cost:,}원",
                "광고/기타지출": f"{ad_c:,}원",
                "최종 순수익": item_net_profit,
                "순수익(표시)": f"{item_net_profit:,}원",
                "실마진율_num": item_roi,
                "실마진율": f"{item_roi:.1f}%",
            })

        total_expense = total_wholesale_cost + total_naver_fee + total_ad_cost + extra_fixed_cost
        final_net_profit = total_rev - total_expense
        overall_margin_rate = (final_net_profit / total_rev * 100) if total_rev > 0 else 0.0

        # 상단 4대 요약 카드
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📈 총 매출액 (Gross 수익)", f"{total_rev:,}원")
        k2.metric("💸 총 지출 합계 (원가+수수료+광고)", f"{total_expense:,}원", f"-도매원가 {total_wholesale_cost:,}원", delta_color="inverse")
        k3.metric("💎 최종 순수익 (Net Profit)", f"{final_net_profit:,}원", f"마진율 {overall_margin_rate:.1f}%")
        k4.metric("📢 마케팅·기타 총지출", f"{total_ad_cost + extra_fixed_cost:,}원", f"네이버수수료 {total_naver_fee:,}원 별도", delta_color="off")

        st.markdown("---")

        df_ledger = pd.DataFrame(ledger_rows)

        col_l_table, col_l_chart = st.columns([1.35, 1.15], gap="large")
        with col_l_table:
            st.markdown("#### 📋 상품별 수익·지출 상세 명세서")
            display_cols = [
                "상품명", "도매처", "판매수량", "총매출액 (수익)",
                "도매원가 합계", "수수료 합계", "광고/기타지출", "순수익(표시)", "실마진율"
            ]
            st.dataframe(df_ledger[display_cols], use_container_width=True, hide_index=True)

        with col_l_chart:
            st.markdown("#### 🏆 효자 상품 순수익 랭킹 (가로형 한눈에 보기)")

            # 순수익 높은 순으로 정렬하여 가로 막대 카드 형태로 렌더링 (글씨 세로 깨짐 완벽 방지)
            df_ranked = df_ledger.sort_values(by="최종 순수익", ascending=False).reset_index(drop=True)
            max_profit = max(df_ranked["최종 순수익"].max(), 1)

            rank_bars_html = ""
            medals = ["🥇 1위", "🥈 2위", "🥉 3위"]

            for r_idx, r_row in df_ranked.iterrows():
                rank_label = medals[r_idx] if r_idx < 3 else f"🏅 {r_idx + 1}위"
                p_val = int(r_row["최종 순수익"])
                bar_pct = max(0, min(100, int((p_val / max_profit) * 100))) if p_val > 0 else 0
                bar_color = "#10b981" if r_idx == 0 else ("#3b82f6" if r_idx == 1 else ("#6366f1" if r_idx == 2 else "#64748b"))
                val_color = "#34d399" if p_val >= 0 else "#f87171"

                rank_bars_html += f"""
                <div class="rank-card">
                    <div class="rank-header">
                        <div class="rank-title">
                            <span class="rank-badge" style="background-color:{bar_color};">{rank_label}</span>
                            <span class="prod-name">{r_row['상품명']}</span>
                        </div>
                        <div class="rank-profit" style="color:{val_color};">{p_val:,}원 <span class="sub-info">({r_row['판매수량']} / 마진 {r_row['실마진율']})</span></div>
                    </div>
                    <div class="progress-bg">
                        <div class="progress-fill" style="width:{bar_pct}%; background-color:{bar_color};"></div>
                    </div>
                </div>
                """

            ranking_component_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; background-color: transparent; }}
                .rank-container {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 16px;
                    color: #f8fafc;
                }}
                .rank-card {{
                    margin-bottom: 14px;
                }}
                .rank-card:last-child {{
                    margin-bottom: 0;
                }}
                .rank-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 6px;
                    gap: 8px;
                    flex-wrap: wrap;
                }}
                .rank-title {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 14px;
                    font-weight: 800;
                    color: #ffffff;
                }}
                .rank-badge {{
                    font-size: 11.5px;
                    padding: 2px 8px;
                    border-radius: 6px;
                    color: #ffffff;
                    font-weight: 900;
                    white-space: nowrap;
                }}
                .prod-name {{
                    word-break: keep-all;
                }}
                .rank-profit {{
                    font-size: 14.5px;
                    font-weight: 900;
                    white-space: nowrap;
                }}
                .sub-info {{
                    font-size: 11.5px;
                    color: #94a3b8;
                    font-weight: normal;
                }}
                .progress-bg {{
                    width: 100%;
                    height: 12px;
                    background-color: #0f172a;
                    border-radius: 999px;
                    overflow: hidden;
                }}
                .progress-fill {{
                    height: 100%;
                    border-radius: 999px;
                    transition: width 0.4s ease;
                }}
            </style>
            </head>
            <body>
                <div class="rank-container">
                    {rank_bars_html}
                </div>
            </body>
            </html>
            """
            rank_height = max(240, len(df_ranked) * 64 + 35)
            components.html(ranking_component_html, height=rank_height, scrolling=True)

        st.info(
            "💡 **장부 업데이트 방법:** [5. 구글 시트 원본 & 바로가기] 탭에서 시트를 열어 `누적판매수량`이나 `광고및기타지출` 숫자만 고치면 이 장부와 가로 랭킹이 자동으로 계산됩니다!"
        )

    # ==========================================
    # TAB 4: 5종 인포그래픽 카드 제작 스튜디오 (복사 & PNG 다운로드)
    # ==========================================
    with tab_info:
        st.subheader("🎨 5종 블로그·카페 인포그래픽 스튜디오 (클립보드 복사 & PNG 사진 저장)")

        df["상품선택"] = (
            df.index.astype(str)
            + " | ["
            + df.get("도매처명", pd.Series(["기본"] * len(df))).astype(str)
            + "] "
            + df["상품명"].astype(str)
        )
        product_list = ["➕ [직접 수동 입력 / 신규 상품 작성]"] + df["상품선택"].tolist()

        top_sel1, top_sel2 = st.columns([1.2, 1.2])
        with top_sel1:
            selected_prod_str = st.selectbox("1️⃣ 시트에 등록된 상품을 불러오거나 직접 작성하세요", product_list)
        with top_sel2:
            template_type = st.selectbox(
                "2️⃣ 홍보용 인포그래픽 템플릿 스타일 선택 (5종)",
                [
                    "① [기본형] 스탠다드 상품 추천 & 스펙 요약 카드",
                    "② [비교형] 타사 일반 제품 VS 우리 스토어 1:1 팩트 비교표",
                    "③ [후기형] 실구매자 베스트 별점 리뷰 3선 모음 카드",
                    "④ [Q&A형] 구매 전 필수 체크! 자주 묻는 질문 & 해답 카드",
                    "⑤ [특가배너형] 타임특가 & 선착순 한정수량 쿠폰 배너",
                ],
            )

        if selected_prod_str != "➕ [직접 수동 입력 / 신규 상품 작성]":
            sel_idx = int(selected_prod_str.split(" | ")[0])
            row = df.iloc[sel_idx]
        else:
            row = None

        default_p_name = str(row.get("상품명", "캠핑용 초경량 감성 우드 롤테이블")) if row is not None else "캠핑용 초경량 감성 우드 롤테이블"
        default_s_url = str(row.get("스마트스토어링크", "https://smartstore.naver.com/")) if row is not None else "https://smartstore.naver.com/"
        default_s_price = int(row.get("판매가_num", 28900)) if row is not None else 28900

        st.markdown("---")

        edit_col, preview_col = st.columns([1.05, 1.25], gap="large")

        with edit_col:
            st.markdown("#### ✏️ 공통 기본 정보 & 컬러 테마 설정")
            p_name = st.text_input("📦 상품 메인 제목", value=default_p_name)
            p_sub = st.text_input("💬 한 줄 서브 카피", value="설치 1분 완성! 감성과 실용성을 모두 잡은 필수 아이템")

            cp1, cp2, cp3 = st.columns(3)
            with cp1:
                orig_price = st.number_input("정상가 (할인 전)", value=int(default_s_price * 1.35 // 100 * 100), step=1000)
            with cp2:
                s_price = st.number_input("스마트스토어 판매가", value=default_s_price, step=500)
            with cp3:
                ship_info = st.selectbox("🚚 혜택 강조 태그", ["무료배송", "오늘출발", "당일발송", "특가할인", "사은품증정"])

            disc_rate = int((1 - (s_price / orig_price)) * 100) if orig_price > s_price and orig_price > 0 else 0

            cs1, cs2 = st.columns(2)
            with cs1:
                badge_text = st.text_input("🏅 상단 강조 뱃지", value="🔥 스마트스토어 MD 강력추천")
                rating_stars = st.select_slider("⭐ 별점 표시", options=["⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], value="⭐⭐⭐⭐⭐")
            with cs2:
                theme_choice = st.selectbox(
                    "🎨 카드 컬러 테마",
                    ["네이버 그린 (#03c75a)", "다크 네이비 (#1e3a8a)", "코랄 레드 (#e11d48)", "모던 블랙 (#18181b)", "퍼플 라벤더 (#6d28d9)"],
                )
                s_url = st.text_input("🏪 스마트스토어 구매 링크", value=default_s_url)

            img_url = st.text_input(
                "🖼️ 상품 이미지 URL (선택사항 - 넣으면 카드 중앙에 사진 표시)",
                value="",
                placeholder="https://... (비워두면 깔끔한 인포그래픽 전용 표로 생성)",
            )

            st.markdown("#### 📝 선택한 템플릿 전용 상세 문구 편집")

            if "①" in template_type:
                feat1 = st.text_input("✔️ 핵심 포인트 1", value="초경량 프리미엄 소재로 흔들림 없는 튼튼한 내구성")
                feat2 = st.text_input("✔️ 핵심 포인트 2", value="전용 수납 파우치 기본 증정으로 언제 어디서나 간편 휴대")
                feat3 = st.text_input("✔️ 핵심 포인트 3", value="실내 인테리어 및 선물용으로도 손색없는 감성 디자인")
                sp1, sp2 = st.columns(2)
                with sp1:
                    spec_label1 = st.text_input("스펙 항목 1", value="소재 / 규격")
                    spec_val1 = st.text_input("스펙 내용 1", value="프리미엄 친환경 소재 / 표준 사이즈")
                with sp2:
                    spec_label2 = st.text_input("스펙 항목 2", value="발송 / AS 안내")
                    spec_val2 = st.text_input("스펙 내용 2", value="국내 당일발송 / 초기불량 100% 무상교환")

            elif "②" in template_type:
                comp_criteria1 = st.text_input("비교 기준 1", value="핵심 소재 & 내구성")
                comp_bad1 = st.text_input("타사 일반 제품 1", value="저가형 얇은 소재로 쉽게 변형됨")
                comp_good1 = st.text_input("우리 스토어 상품 1", value="고밀도 프리미엄 소재로 반영구적 사용")

                comp_criteria2 = st.text_input("비교 기준 2", value="구성품 & 패키지")
                comp_bad2 = st.text_input("타사 일반 제품 2", value="본품만 단품 발송 (케이스 별도 구매)")
                comp_good2 = st.text_input("우리 스토어 상품 2", value="전용 고급 파우치 + 풀세트 기본 증정")

                comp_criteria3 = st.text_input("비교 기준 3", value="배송 & 사후 관리")
                comp_bad3 = st.text_input("타사 일반 제품 3", value="해외직구 2주 소요 / 교환·환불 어려움")
                comp_good3 = st.text_input("우리 스토어 상품 3", value="국내 검수 후 당일발송 / 100% 책임 AS")

            elif "③" in template_type:
                rev1_user = st.text_input("리뷰어 1 정보", value="네이버페이 실구매자 (kim***님) | 재구매")
                rev1_text = st.text_input("베스트 후기 1", value="비슷한 제품 여러 개 써봤는데 마감 퀄리티가 확실히 다릅니다! 배송도 하루 만에 왔어요.")
                rev2_user = st.text_input("리뷰어 2 정보", value="스마트스토어 한달사용기 (lee***님)")
                rev2_text = st.text_input("베스트 후기 2", value="가성비 최고예요. 지인 선물용으로 샀다가 너무 마음에 들어서 제 것도 하나 더 주문했습니다!")
                rev3_user = st.text_input("리뷰어 3 정보", value="네이버페이 실구매자 (par***님)")
                rev3_text = st.text_input("베스트 후기 3", value="포장도 꼼꼼하고 사진보다 실물이 훨씬 예쁩니다. 고민하시는 분들 무조건 추천해요!")

            elif "④" in template_type:
                q1_text = st.text_input("질문 Q1", value="오늘 주문하면 언제 발송되나요?")
                a1_text = st.text_input("답변 A1", value="평일 오후 2시 이전 주문 건은 당일 출고되어 보통 다음 날 바로 받아보실 수 있습니다.")
                q2_text = st.text_input("질문 Q2", value="초보자도 쉽게 사용할 수 있나요?")
                a2_text = st.text_input("답변 A2", value="네! 별도의 복잡한 조립 없이 개봉 후 1분 만에 누구나 간편하게 사용하실 수 있습니다.")
                q3_text = st.text_input("질문 Q3", value="불량이거나 마음에 안 들면 교환/환불 되나요?")
                a3_text = st.text_input("답변 A3", value="수령 후 7일 이내 단순 변심은 물론, 초기 불량 시 판매자가 배송비를 100% 부담하여 즉시 교환해 드립니다.")

            elif "⑤" in template_type:
                promo_headline = st.text_input("🔥 특가 메인 타이틀", value="⚡ 블로그·카페 이웃 전용 시크릿 타임특가!")
                coupon_text = st.text_input("🎟️ 추가 혜택 문구", value="스토어 알림받기 설정 시 추가 할인 쿠폰 즉시 발급 + 무료배송")
                stock_limit = st.text_input("⏳ 잔여 수량 / 마감 안내", value="준비된 이벤트 수량 50개 소진 시 예고 없이 정상가로 인상됩니다.")

        theme_map = {
            "네이버 그린 (#03c75a)": ("#03c75a", "#e8f8f0"),
            "다크 네이비 (#1e3a8a)": ("#1e3a8a", "#eff6ff"),
            "코랄 레드 (#e11d48)": ("#e11d48", "#fff1f2"),
            "모던 블랙 (#18181b)": ("#18181b", "#f4f4f5"),
            "퍼플 라벤더 (#6d28d9)": ("#6d28d9", "#f5f3ff"),
        }
        main_color, sub_bg = theme_map[theme_choice]
        safe_filename = re.sub(r"[^가-힣a-zA-Z0-9_-]", "_", p_name)[:25] or "smartstore_card"

        img_block = ""
        if img_url.strip():
            img_block = f"""
            <tr>
                <td colspan="2" align="center" style="padding: 16px 24px 6px 24px; background-color: #ffffff;">
                    <img src="{img_url.strip()}" crossorigin="anonymous" style="max-width: 100%; max-height: 300px; height: auto; border-radius: 10px; border: 1px solid #e5e7eb;" alt="상품 이미지" />
                </td>
            </tr>
            """

        discount_badge_html = (
            f'<span style="font-size: 26px; font-weight: 900; color: #e11d48; margin-right: 10px;">{disc_rate}% ↓</span>'
            if disc_rate > 0
            else ""
        )

        price_box_html = f"""
        <tr>
            <td colspan="2" style="padding: 14px 24px; background-color: #ffffff;">
                <table width="100%" style="border-collapse: collapse; background-color: {sub_bg}; border-radius: 10px; border: 1px solid {main_color}33;" bgcolor="{sub_bg}">
                    <tr>
                        <td style="padding: 15px 20px; width: 65%;">
                            <div style="font-size: 13px; color: #777777; text-decoration: line-through;">정상가 {orig_price:,}원</div>
                            <div style="margin-top: 4px;">
                                {discount_badge_html}
                                <span style="font-size: 26px; font-weight: 900; color: #111111;">{s_price:,}원</span>
                            </div>
                        </td>
                        <td align="right" style="padding: 15px 20px; width: 35%;">
                            <span style="background-color: {main_color}; color: #ffffff; padding: 8px 14px; border-radius: 8px; font-size: 14px; font-weight: 800; display: inline-block;">🚚 {ship_info}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

        if "①" in template_type:
            body_section_html = f"""
            {price_box_html}
            <tr>
                <td colspan="2" style="padding: 4px 24px 16px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; border: 1px solid #e5e7eb; border-radius: 8px;">
                        <tr bgcolor="#f8fafc">
                            <td style="padding: 11px 16px; font-size: 14px; font-weight: 800; color: #1e293b; border-bottom: 1px solid #e5e7eb;">
                                📌 핵심 체크포인트 TOP 3
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 16px; font-size: 14.5px; color: #222222; line-height: 1.85; background-color: #ffffff;">
                                <div style="margin-bottom: 4px;">✅ <b>POINT 1.</b> {feat1}</div>
                                <div style="margin-bottom: 4px;">✅ <b>POINT 2.</b> {feat2}</div>
                                <div>✅ <b>POINT 3.</b> {feat3}</div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan="2" style="padding: 0px 24px 18px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; border: 1px solid #e5e7eb; font-size: 13px;">
                        <tr>
                            <td width="28%" bgcolor="#f8fafc" style="padding: 10px 12px; font-weight: bold; color: #475569; border-bottom: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb;">{spec_label1}</td>
                            <td width="72%" style="padding: 10px 12px; color: #1e293b; border-bottom: 1px solid #e5e7eb;">{spec_val1}</td>
                        </tr>
                        <tr>
                            <td width="28%" bgcolor="#f8fafc" style="padding: 10px 12px; font-weight: bold; color: #475569; border-right: 1px solid #e5e7eb;">{spec_label2}</td>
                            <td width="72%" style="padding: 10px 12px; color: #1e293b;">{spec_val2}</td>
                        </tr>
                    </table>
                </td>
            </tr>
            """
        elif "②" in template_type:
            body_section_html = f"""
            {price_box_html}
            <tr>
                <td colspan="2" style="padding: 4px 24px 20px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; border: 2px solid #cbd5e1; font-size: 13.5px; text-align: center;">
                        <tr bgcolor="#1e293b" style="color: #ffffff; font-weight: 800;">
                            <td width="24%" style="padding: 11px 8px; border: 1px solid #334155;">비교 항목</td>
                            <td width="36%" style="padding: 11px 8px; border: 1px solid #334155; background-color: #64748b;">😟 타사 일반 저가형</td>
                            <td width="40%" style="padding: 11px 8px; border: 1px solid #334155; background-color: {main_color};">🏆 우리 스토어 정품</td>
                        </tr>
                        <tr>
                            <td bgcolor="#f8fafc" style="padding: 12px 8px; font-weight: bold; color: #334155; border: 1px solid #cbd5e1;">{comp_criteria1}</td>
                            <td style="padding: 12px 10px; color: #64748b; border: 1px solid #cbd5e1;">❌ {comp_bad1}</td>
                            <td bgcolor="{sub_bg}" style="padding: 12px 10px; color: #111111; font-weight: 800; border: 1px solid #cbd5e1;">⭕ {comp_good1}</td>
                        </tr>
                        <tr>
                            <td bgcolor="#f8fafc" style="padding: 12px 8px; font-weight: bold; color: #334155; border: 1px solid #cbd5e1;">{comp_criteria2}</td>
                            <td style="padding: 12px 10px; color: #64748b; border: 1px solid #cbd5e1;">❌ {comp_bad2}</td>
                            <td bgcolor="{sub_bg}" style="padding: 12px 10px; color: #111111; font-weight: 800; border: 1px solid #cbd5e1;">⭕ {comp_good2}</td>
                        </tr>
                        <tr>
                            <td bgcolor="#f8fafc" style="padding: 12px 8px; font-weight: bold; color: #334155; border: 1px solid #cbd5e1;">{comp_criteria3}</td>
                            <td style="padding: 12px 10px; color: #64748b; border: 1px solid #cbd5e1;">❌ {comp_bad3}</td>
                            <td bgcolor="{sub_bg}" style="padding: 12px 10px; color: #111111; font-weight: 800; border: 1px solid #cbd5e1;">⭕ {comp_good3}</td>
                        </tr>
                    </table>
                </td>
            </tr>
            """
        elif "③" in template_type:
            body_section_html = f"""
            {price_box_html}
            <tr>
                <td colspan="2" style="padding: 4px 24px 18px 24px; background-color: #ffffff;">
                    <div style="font-size: 14px; font-weight: 900; color: {main_color}; margin-bottom: 10px;">💬 실구매 고객님들의 100% 리얼 극찬 후기</div>
                    <table width="100%" style="border-collapse: collapse; margin-bottom: 10px; background-color: #f8fafc; border-left: 4px solid {main_color}; border-radius: 6px;">
                        <tr><td style="padding: 12px 16px;">
                            <div style="font-size: 12px; font-weight: bold; color: #ca8a04; margin-bottom: 4px;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev1_user}</span></div>
                            <div style="font-size: 13.5px; color: #1e293b; line-height: 1.5;">"{rev1_text}"</div>
                        </td></tr>
                    </table>
                    <table width="100%" style="border-collapse: collapse; margin-bottom: 10px; background-color: #f8fafc; border-left: 4px solid {main_color}; border-radius: 6px;">
                        <tr><td style="padding: 12px 16px;">
                            <div style="font-size: 12px; font-weight: bold; color: #ca8a04; margin-bottom: 4px;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev2_user}</span></div>
                            <div style="font-size: 13.5px; color: #1e293b; line-height: 1.5;">"{rev2_text}"</div>
                        </td></tr>
                    </table>
                    <table width="100%" style="border-collapse: collapse; background-color: #f8fafc; border-left: 4px solid {main_color}; border-radius: 6px;">
                        <tr><td style="padding: 12px 16px;">
                            <div style="font-size: 12px; font-weight: bold; color: #ca8a04; margin-bottom: 4px;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev3_user}</span></div>
                            <div style="font-size: 13.5px; color: #1e293b; line-height: 1.5;">"{rev3_text}"</div>
                        </td></tr>
                    </table>
                </td>
            </tr>
            """
        elif "④" in template_type:
            body_section_html = f"""
            {price_box_html}
            <tr>
                <td colspan="2" style="padding: 4px 24px 18px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <tr bgcolor="#f1f5f9">
                            <td style="padding: 11px 16px; font-size: 14px; font-weight: 900; color: #0f172a; border-bottom: 1px solid #e2e8f0;">
                                🙋‍♂️ 구매 전 가장 많이 묻는 질문 Q&A
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #f1f5f9;">
                                <div style="font-size: 14px; font-weight: 800; color: {main_color}; margin-bottom: 4px;">Q1. {q1_text}</div>
                                <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">👉 <b>A.</b> {a1_text}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 14px 16px; border-bottom: 1px solid #f1f5f9;">
                                <div style="font-size: 14px; font-weight: 800; color: {main_color}; margin-bottom: 4px;">Q2. {q2_text}</div>
                                <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">👉 <b>A.</b> {a2_text}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 14px 16px;">
                                <div style="font-size: 14px; font-weight: 800; color: {main_color}; margin-bottom: 4px;">Q3. {q3_text}</div>
                                <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">👉 <b>A.</b> {a3_text}</div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            """
        else:
            body_section_html = f"""
            <tr>
                <td colspan="2" style="padding: 16px 24px 8px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; background-color: #111827; color: #ffffff; border-radius: 10px; text-align: center;" bgcolor="#111827">
                        <tr>
                            <td style="padding: 18px 16px;">
                                <div style="font-size: 18px; font-weight: 900; color: #facc15; margin-bottom: 6px;">{promo_headline}</div>
                                <div style="font-size: 13.5px; color: #e5e7eb;">🎁 {coupon_text}</div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            {price_box_html}
            <tr>
                <td colspan="2" style="padding: 0px 24px 18px 24px; background-color: #ffffff;">
                    <table width="100%" style="border-collapse: collapse; background-color: #fef2f2; border: 1px dashed #ef4444; border-radius: 8px; text-align: center;" bgcolor="#fef2f2">
                        <tr>
                            <td style="padding: 12px; font-size: 13.5px; font-weight: 800; color: #b91c1c;">
                                ⏰ {stock_limit}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            """

        infographic_html = f"""
<table width="100%" style="max-width: 620px; margin: 0 auto; border-collapse: collapse; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; border: 3px solid {main_color}; background-color: #ffffff; border-radius: 12px; overflow: hidden;">
    <tr bgcolor="{main_color}">
        <td colspan="2" style="padding: 15px 22px; color: #ffffff; background-color: {main_color};">
            <span style="background-color: #ffffff; color: {main_color}; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 800;">{badge_text}</span>
            <span style="float: right; font-size: 14px; color: #ffffff; font-weight: bold;">만족도 {rating_stars}</span>
        </td>
    </tr>
    <tr>
        <td colspan="2" style="padding: 24px 24px 12px 24px; border-bottom: 1px solid #eeeeee; background-color: #ffffff;">
            <div style="font-size: 24px; font-weight: 900; color: #111111; line-height: 1.35; margin-bottom: 8px; letter-spacing: -0.5px;">{p_name}</div>
            <div style="font-size: 15px; color: #555555; font-weight: 600;">{p_sub}</div>
        </td>
    </tr>
    {img_block}
    {body_section_html}
    <tr>
        <td colspan="2" align="center" style="padding: 6px 24px 24px 24px; background-color: #ffffff;">
            <a href="{s_url}" target="_blank" style="background-color: {main_color}; color: #ffffff; padding: 15px 36px; text-decoration: none; border-radius: 8px; font-weight: 900; font-size: 16px; display: inline-block;">
                👉 네이버 스마트스토어 공식 판매처 바로가기
            </a>
        </td>
    </tr>
</table>
"""

        with preview_col:
            st.markdown("#### 👀 실시간 프리뷰 & 원클릭 추출 (복사 / PNG 저장)")

            component_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                    body {{ margin: 0; padding: 0; font-family: 'Malgun Gothic', sans-serif; background-color: transparent; }}
                    .action-bar {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }}
                    .big-btn {{
                        width: 100%; padding: 18px 20px; font-size: 18px; font-weight: 900;
                        border-radius: 10px; cursor: pointer; border: none; transition: all 0.15s ease-in-out;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.12); display: flex; align-items: center; justify-content: center; gap: 8px;
                    }}
                    .big-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.18); }}
                    .btn-png {{ background-color: #111827; color: #ffffff; border: 2px solid #111827; }}
                    .btn-copy {{ background-color: {main_color}; color: #ffffff; }}
                    #status-msg {{ text-align: center; font-weight: 800; font-size: 14.5px; padding: 10px; border-radius: 8px; margin-bottom: 12px; display: none; }}
                    #capture-wrapper {{ background-color: #ffffff; padding: 12px; border-radius: 14px; display: inline-block; width: 100%; box-sizing: border-box; }}
                </style>
            </head>
            <body>
                <div class="action-bar">
                    <button class="big-btn btn-png" onclick="downloadPNG()">
                        📸 인포그래픽 고화질 PNG 사진으로 다운로드 (클릭 즉시 저장)
                    </button>
                    <button class="big-btn btn-copy" onclick="copyInfographic()">
                        📋 블로그/카페 표 서식 통째로 복사하기 (클릭 후 본문에 Ctrl+V)
                    </button>
                </div>

                <div id="status-msg"></div>

                <div id="capture-wrapper">
                    {infographic_html}
                </div>

                <script>
                function showMessage(text, bgColor, textColor) {{
                    const msg = document.getElementById('status-msg');
                    msg.innerText = text;
                    msg.style.backgroundColor = bgColor;
                    msg.style.color = textColor;
                    msg.style.display = 'block';
                    setTimeout(() => {{ msg.style.display = 'none'; }}, 4500);
                }}

                function copyInfographic() {{
                    const area = document.getElementById('capture-wrapper');
                    const range = document.createRange();
                    range.selectNode(area);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(range);
                    try {{
                        document.execCommand('copy');
                        showMessage('✅ 클립보드에 복사되었습니다! 네이버 블로그/카페 글쓰기 창에 그대로 Ctrl+V 하세요.', '#dcfce7', '#166534');
                    }} catch (err) {{
                        showMessage('⚠️ 자동 복사에 실패했습니다. 아래 카드를 마우스로 드래그하여 Ctrl+C를 눌러주세요.', '#fee2e2', '#991b1b');
                    }}
                    selection.removeAllRanges();
                }}

                function downloadPNG() {{
                    const target = document.getElementById('capture-wrapper');
                    showMessage('⏳ 고화질 PNG 이미지를 생성 중입니다... 잠시만 기다려주세요.', '#fef3c7', '#92400e');

                    html2canvas(target, {{
                        scale: 2,
                        useCORS: true,
                        allowTaint: true,
                        backgroundColor: '#ffffff'
                    }}).then(canvas => {{
                        const link = document.createElement('a');
                        link.download = '{safe_filename}_인포그래픽.png';
                        link.href = canvas.toDataURL('image/png');
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        showMessage('🎉 PNG 이미지 파일이 다운로드되었습니다! 블로그에 사진처럼 업로드하고 스토어 링크를 걸어주세요.', '#dbeafe', '#1e40af');
                    }}).catch(err => {{
                        console.error(err);
                        showMessage('⚠️ 외부 이미지 보안 정책으로 캡처가 제한되었습니다. 상품 이미지 URL을 비우고 다시 시도해 보세요.', '#fee2e2', '#991b1b');
                    }});
                }}
                </script>
            </body>
            </html>
            """
            components.html(component_html, height=880, scrolling=True)

    # ==========================================
    # TAB 5: 구글 시트 원본 데이터 & 바로가기
    # ==========================================
    with tab_raw:
        st.subheader("📊 구글 시트 원본 데이터 & 시트 열기")
        st.markdown(
            f"👉 **[여기를 클릭해 내 구글 시트(상품관리 및 수익장부) 바로 열기]({DEFAULT_SHEET_URL}/edit)**"
        )
        display_raw = [c for c in df.columns if not c.endswith("_num") and c != "상품선택"]
        st.dataframe(df[display_raw], use_container_width=True)

except Exception as e:
    st.error(f"앱 실행 중 오류가 발생했습니다. 상세 에러: {e}")
