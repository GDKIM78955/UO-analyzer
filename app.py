import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import calendar

# SSL 보안 경고 무시 (일부 도매 사이트 크롤링 오류 방지)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="스마트스토어 위탁판매 올인원 ERP", layout="wide", initial_sidebar_state="expanded")

# 한국 시간(KST) 기준 오늘 날짜 계산
KST = timezone(timedelta(hours=9))
today = datetime.now(KST).date()

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

# ==========================================
# 2. 구글 시트 연동 설정
# ==========================================
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/12g0e-ER14x2cyx2ipEAluZjHU5FAxUNpKIrg6sP1jiI"
csv_url = f"{SHEET_BASE_URL}/export?format=csv&gid=0"
monthly_sheet_name = quote("월별_수익지출_요약")
monthly_csv_url = f"{SHEET_BASE_URL}/gviz/tq?tqx=out:csv&sheet={monthly_sheet_name}"


@st.cache_data(ttl=60, show_spinner=False)
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df


# ==========================================
# 3. 도매처 & 경쟁사 크롤링/감지 함수
# ==========================================
def check_wholesale_status(url, recorded_wholesale_price=0, selling_price=0, fee_rate=5.6):
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
        "품절", "일시품절", "판매종료", "판매중지", "재고없음",
        "구매불가", "단종", "삭제된 상품", "존재하지 않는 상품",
        "현재 판매중인 상품이 아닙니다", "판매가 종료", "sold out", "out of stock",
    ]

    try:
        resp = requests.get(str(url), headers=headers, timeout=8, verify=False)
        if resp.status_code == 404:
            return "🔴 링크 삭제 (404)", "페이지가 사라졌습니다. 즉시 스토어 품절 처리 & 블로그 링크 교체 필요!"
        elif resp.status_code != 200:
            return f"🟡 접속 확인 필요 ({resp.status_code})", "사이트 보안 또는 일시적 오류 (직접 클릭해 확인 권장)"

        soup = BeautifulSoup(resp.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text(separator=" ").lower()

        detected = [kw for kw in sold_out_keywords if kw in page_text]
        if detected:
            return "🔴 품절/종료 의심", f"감지된 단어: {', '.join(detected[:3])}"

        if selling_price > 0 and recorded_wholesale_price > 0:
            est_fee = int(round(selling_price * (fee_rate / 100)))
            est_margin = selling_price - recorded_wholesale_price - est_fee
            margin_pct = (est_margin / selling_price) * 100
            if margin_pct < 10.0:
                return "🟠 역마진/저마진 주의", f"현재 마진율 {margin_pct:.1f}% (순수익 {est_margin:,}원) - 판매가 인상 권장!"

        if recorded_wholesale_price > 1000:
            price_matches = re.findall(r"([1-9][0-9]{0,2}(?:,[0-9]{3})+)\s*원", page_text)
            extracted_prices = [int(p.replace(",", "")) for p in price_matches]
            higher_candidates = [
                p for p in extracted_prices
                if int(recorded_wholesale_price * 1.05) <= p <= int(recorded_wholesale_price * 1.6)
            ]
            if higher_candidates and recorded_wholesale_price not in extracted_prices:
                suspect_price = min(higher_candidates, key=lambda x: abs(x - recorded_wholesale_price))
                diff = suspect_price - recorded_wholesale_price
                return "🟠 도매가 인상 의심", f"시트원가({recorded_wholesale_price:,}원) 대비 페이지 내 {suspect_price:,}원(+{diff:,}원) 감지됨"

        return "🟢 정상 판매중", "특이사항 없음 (정상 발주 가능)"

    except Exception as e:
        return "🟡 연결 지연/오류", f"수동 확인 필요 ({type(e).__name__})"


def scan_competitor_page(url, my_price):
    if not url or not str(url).startswith("http"):
        return "⚪ URL 미입력", 0, "경쟁사 URL을 입력하세요."
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(str(url), headers=headers, timeout=8, verify=False)
        if resp.status_code != 200:
            return f"🟡 수동 확인 ({resp.status_code})", 0, "보안 정책으로 직접 클릭해 가격을 비교하세요."
        soup = BeautifulSoup(resp.text, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        txt = soup.get_text(separator=" ")
        prices = [int(p.replace(",", "")) for p in re.findall(r"([1-9][0-9]{0,2}(?:,[0-9]{3})+)\s*원", txt)]
        valid_prices = [p for p in prices if int(my_price * 0.4) <= p <= int(my_price * 2.0)]
        if valid_prices:
            comp_p = min(valid_prices, key=lambda x: abs(x - my_price))
            diff = my_price - comp_p
            if diff > 0:
                return "🔴 경쟁사 더 저렴!", comp_p, f"경쟁사가 내 스토어보다 {diff:,}원 더 싸게 판매 중!"
            elif diff < 0:
                return "🟢 내 스토어 최저가 우위", comp_p, f"내가 경쟁사보다 {abs(diff):,}원 더 저렴합니다!"
            else:
                return "🟡 가격 동일", comp_p, "경쟁사와 판매가가 동일합니다."
        return "🟡 가격 자동추출 불가", 0, "동적 로딩 페이지입니다. 링크를 열어 확인하세요."
    except Exception as e:
        return "🟡 접속 지연", 0, f"직접 확인 필요 ({type(e).__name__})"


# ==========================================
# 4. 원클릭 클립보드 복사 박스 헬퍼 함수
# ==========================================
def render_copy_box(title_label, content_text, box_id, btn_color="#03c75a", height=220, display_text=None):
    escaped_text = (
        content_text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
    )
    shown_raw = display_text if display_text is not None else content_text
    html_display = shown_raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    comp_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{ margin: 0; padding: 0; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; background: transparent; }}
        .box-wrap {{
            background-color: #ffffff;
            border: 2px solid {btn_color};
            border-radius: 10px;
            padding: 14px;
            box-sizing: border-box;
        }}
        .top-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px;
        }}
        .box-title {{ font-size: 14.5px; font-weight: 900; color: #111827; }}
        .copy-btn {{
            background-color: {btn_color}; color: #ffffff; border: none;
            padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 800;
            cursor: pointer; white-space: nowrap;
        }}
        .copy-btn:hover {{ opacity: 0.9; }}
        .content-area {{
            background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
            padding: 12px; font-size: 13.5px; color: #1e293b; line-height: 1.65;
            max-height: {height - 85}px; overflow-y: auto;
        }}
        .msg-toast {{ display: none; font-size: 12.5px; font-weight: 800; color: #16a34a; margin-left: 8px; }}
    </style>
    </head>
    <body>
        <div class="box-wrap">
            <div class="top-row">
                <div>
                    <span class="box-title">{title_label}</span>
                    <span id="msg_{box_id}" class="msg-toast">✅ 복사 완료! (Ctrl+V)</span>
                </div>
                <button class="copy-btn" onclick="copyText_{box_id}()">📋 원클릭 복사하기</button>
            </div>
            <div class="content-area">{html_display}</div>
        </div>
        <script>
        function copyText_{box_id}() {{
            const rawText = `{escaped_text}`;
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(rawText).then(() => showToast_{box_id}()).catch(() => fallbackCopy_{box_id}(rawText));
            }} else {{
                fallbackCopy_{box_id}(rawText);
            }}
        }}
        function fallbackCopy_{box_id}(text) {{
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showToast_{box_id}();
        }}
        function showToast_{box_id}() {{
            const el = document.getElementById('msg_{box_id}');
            el.style.display = 'inline';
            setTimeout(() => {{ el.style.display = 'none'; }}, 3500);
        }}
        </script>
    </body>
    </html>
    """
    components.html(comp_code, height=height, scrolling=False)


# ==========================================
# 5. 데이터 로드 및 사이드바 5대 워크스페이스 구성
# ==========================================
try:
    with st.spinner("구글 시트 데이터를 불러오는 중입니다..."):
        try:
            df = load_data(csv_url)
        except Exception:
            df = pd.DataFrame()

        try:
            df_monthly_raw = load_data(monthly_csv_url)
        except Exception:
            df_monthly_raw = pd.DataFrame()

    required_cols = ["상품명", "도매처링크", "도매원가", "판매가"]
    if df.empty or not all(col in df.columns for col in required_cols):
        df = pd.DataFrame([
            {
                "상품명": "캠핑용 초경량 감성 우드 롤테이블",
                "도매처명": "도매꾹",
                "도매처링크": "https://domeggook.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 16500,
                "판매가": 28900,
                "배송비": 3000,
                "블로그홍보링크": "https://blog.naver.com/myblog/1001",
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
                "블로그홍보링크": "https://cafe.naver.com/mycafe/2002",
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
                "블로그홍보링크": "https://blog.naver.com/myblog/1003",
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
                "블로그홍보링크": "https://blog.naver.com/myblog/1004",
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
                "블로그홍보링크": "https://cafe.naver.com/mycafe/2005",
                "누적판매수량": 15,
                "광고및기타지출": 10000,
            },
        ])

    if df_monthly_raw.empty or "기준월" not in df_monthly_raw.columns:
        df_monthly_raw = pd.DataFrame([
            {"기준월": "2026-09", "총매출액": 1850000, "도매원가합계": 1020000, "네이버수수료합계": 103600, "광고및기타지출": 80000, "최종순수익": 646400, "수익률": "34.9%"},
            {"기준월": "2026-10", "총매출액": 2420000, "도매원가합계": 1310000, "네이버수수료합계": 135520, "광고및기타지출": 95000, "최종순수익": 879480, "수익률": "36.3%"},
            {"기준월": "2026-11", "총매출액": 3082000, "도매원가합계": 1618300, "네이버수수료합계": 172592, "광고및기타지출": 100000, "최종순수익": 1191108, "수익률": "38.6%"},
        ])

    def clean_num(series, default=0):
        if series is None:
            return pd.Series([default] * len(df))
        return pd.to_numeric(series.astype(str).str.replace(r"[^0-9.-]", "", regex=True), errors="coerce").fillna(default)

    df["도매원가_num"] = clean_num(df.get("도매원가"), 0)
    df["판매가_num"] = clean_num(df.get("판매가"), 0)
    df["누적판매수량_num"] = clean_num(df.get("누적판매수량"), 0)
    df["광고및기타지출_num"] = clean_num(df.get("광고및기타지출"), 0)

    df["상품선택"] = (
        df.index.astype(str)
        + " | ["
        + df.get("도매처명", pd.Series(["기본"] * len(df))).astype(str)
        + "] "
        + df["상품명"].astype(str)
    )
    product_list = ["➕ [직접 수동 입력 / 신규 상품 작성]"] + df["상품선택"].tolist()

    # ==========================================
    # 좌측 사이드바 네비게이션 (복잡한 탭을 5대 핵심 메뉴로 깔끔하게 분리)
    # ==========================================
    with st.sidebar:
        st.markdown("## 🛒 위탁판매 컨트롤 타워")
        st.caption(f"📅 오늘: {today.strftime('%Y-%m-%d')}")
        st.markdown("---")

        main_menu = st.radio(
            "📂 작업할 메뉴를 선택하세요",
            [
                "📅 1. 소싱 & 시즌 캘린더",
                "🚨 2. 품절·경쟁사·블로그 감시",
                "📦 3. 발주서 변환 & CS 관리",
                "🎨 4. 마케팅·썸네일 스튜디오",
                "💰 5. 수익장부 & 세금 계산기",
            ],
        )

        st.markdown("---")
        next_ev = upcoming_list[0]
        st.info(
            f"🔔 **가장 가까운 시즌 대목**\n\n"
            f"**D-{next_ev['d_day']} | {next_ev['name']}**\n"
            f"({next_ev['event_date'].strftime('%m월 %d일')})"
        )
        st.markdown(f"👉 **[구글 시트 장부 바로 열기]({SHEET_BASE_URL}/edit)**")
        if st.button("🔄 구글 시트 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 상단 공통 타이틀 & 다가오는 3~4주 전 시즌 알림 요약
    st.title("🛒 스마트스토어 위탁판매 & 블로그 올인원 ERP")
    golden_events = [e for e in upcoming_list if e["d_day"] <= 38]
    if golden_events:
        ge = golden_events[0]
        st.warning(
            f"🔔 **[자동 소싱 레이더] D-{ge['d_day']} {ge['name']} ({ge['event_date'].strftime('%m월 %d일')})** — "
            f"{ge['action_status']} | **추천 품목:** {ge['items']}"
        )

    # ==================================================================================
    # MENU 1: 📅 소싱 & 시즌 캘린더
    # ==================================================================================
    if main_menu == "📅 1. 소싱 & 시즌 캘린더":
        st.subheader("📅 연간 기념일 소싱 로드맵 & 월별 달력 (3~4주 전 사전 준비 알림)")
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
            st.dataframe(pd.DataFrame(schedule_rows), use_container_width=True, hide_index=True, height=560)

    # ==================================================================================
    # MENU 2: 🚨 품절·경쟁사·블로그 감시 (품절스캔 + 블로그 죽은링크 역추적 + 경쟁사 가격감시)
    # ==================================================================================
    elif main_menu == "🚨 2. 품절·경쟁사·블로그 감시":
        sub_m1, sub_m2, sub_m3 = st.tabs([
            "🔍 1. 도매처 품절·단종·가격인상 스캔",
            "📝 2. 블로그·카페 죽은 홍보링크 역추적",
            "⚔️ 3. 경쟁사 스토어 최저가 비교·감시",
        ])

        with sub_m1:
            st.subheader("🔍 등록 상품 도매처 품절·단종 & 기습 가격 인상 일괄 스캔")
            st.write("도매처 링크 삭제(404), 품절 키워드, 도매원가 기습 인상 및 저마진(10% 미만) 위험을 한 번에 스캔합니다.")

            if st.button("🚀 전체 상품 도매처 품절 & 가격 변동 실시간 스캔 실행", type="primary", use_container_width=True):
                results = []
                dead_blog_Posts = []
                progress_bar = st.progress(0, text="도매처 링크 및 가격 상태를 점검하고 있습니다...")
                total_items = len(df)

                for idx, row in df.iterrows():
                    p_name = str(row.get("상품명", f"상품 {idx+1}"))
                    w_name = str(row.get("도매처명", "-"))
                    w_url = str(row.get("도매처링크", ""))
                    s_url = str(row.get("스마트스토어링크", ""))
                    b_url = str(row.get("블로그홍보링크", ""))
                    w_price = int(row.get("도매원가_num", 0))
                    s_price = int(row.get("판매가_num", 0))

                    est_fee = int(round(s_price * 0.056))
                    unit_net = s_price - w_price - est_fee
                    unit_margin_pct = (unit_net / s_price * 100) if s_price > 0 else 0.0

                    status_badge, detail_msg = check_wholesale_status(w_url, w_price, s_price, 5.6)

                    results.append({
                        "No": idx + 1,
                        "상태": status_badge,
                        "상품명": p_name,
                        "도매처": w_name,
                        "시트도매원가": f"{w_price:,}원",
                        "스토어판매가": f"{s_price:,}원",
                        "개당순마진": f"{unit_net:,}원 ({unit_margin_pct:.1f}%)",
                        "점검 결과 상세": detail_msg,
                        "도매처 링크": w_url,
                        "내 스토어": s_url,
                        "블로그/카페": b_url,
                    })

                    if "🔴" in status_badge or "🟠" in status_badge:
                        dead_blog_Posts.append({
                            "위험 상태": status_badge,
                            "문제가 발생한 상품명": p_name,
                            "점검 내용": detail_msg,
                            "수정해야 할 블로그/카페 게시글": b_url,
                            "내 스마트스토어 링크": s_url,
                        })

                    progress_bar.progress((idx + 1) / total_items, text=f"[{idx+1}/{total_items}] {p_name} 점검 완료")

                st.session_state["last_scan_results"] = results
                st.session_state["dead_blog_posts"] = dead_blog_Posts

            if "last_scan_results" in st.session_state:
                results = st.session_state["last_scan_results"]
                ok_cnt = sum(1 for r in results if "🟢" in r["상태"])
                danger_cnt = sum(1 for r in results if "🔴" in r["상태"])
                price_warn_cnt = sum(1 for r in results if "🟠" in r["상태"])
                warn_cnt = sum(1 for r in results if "🟡" in r["상태"])

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🟢 정상 판매 가능", f"{ok_cnt}건")
                m2.metric("🔴 품절/단종 위험 (즉시 품절처리)", f"{danger_cnt}건")
                m3.metric("🟠 가격인상/역마진 주의", f"{price_warn_cnt}건")
                m4.metric("🟡 수동 확인 필요", f"{warn_cnt}건")

                st.dataframe(
                    pd.DataFrame(results),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "도매처 링크": st.column_config.LinkColumn("도매처", display_text="🔗 도매처 열기"),
                        "내 스토어": st.column_config.LinkColumn("스마트스토어", display_text="🏪 스토어 열기"),
                        "블로그/카페": st.column_config.LinkColumn("홍보글", display_text="📝 홍보글 열기"),
                    },
                )

        with sub_m2:
            st.subheader("📝 블로그·카페 홍보글 '죽은 링크 / 품절 상품' 역추적기")
            st.write(
                "도매처 상품이 품절·단종되었는데 블로그나 카페 홍보글에 옛날 링크가 그대로 남아있으면 방문자가 이탈합니다. "
                "수정이 시급한 블로그·카페 게시글 목록을 자동으로 추려줍니다."
            )

            blog_audit_rows = []
            for idx, row in df.iterrows():
                p_name = str(row.get("상품명", f"상품 {idx+1}"))
                b_url = str(row.get("블로그홍보링크", "")).strip()
                s_url = str(row.get("스마트스토어링크", "")).strip()
                w_url = str(row.get("도매처링크", "")).strip()

                if not b_url or b_url in ("nan", "None", "https://blog.naver.com/", "https://cafe.naver.com/"):
                    post_status = "⚪ 홍보글 미등록 (포스팅 필요!)"
                    action_guide = "아직 블로그/카페 상세 홍보글 주소가 없습니다. 홍보글을 작성해 유입을 늘리세요!"
                else:
                    post_status = "🟢 홍보링크 연결됨"
                    action_guide = "도매처 품절 발생 시 이 게시글의 스토어 링크를 대체 상품으로 교체하세요."

                blog_audit_rows.append({
                    "No": idx + 1,
                    "상품명": p_name,
                    "홍보글 상태": post_status,
                    "블로그/카페 게시글 바로가기": b_url if b_url.startswith("http") else "",
                    "연결된 스마트스토어": s_url if s_url.startswith("http") else "",
                    "원본 도매처": w_url if w_url.startswith("http") else "",
                    "권장 액션 가이드": action_guide,
                })

            if "dead_blog_posts" in st.session_state and st.session_state["dead_blog_posts"]:
                st.error("🚨 **방금 품절/가격인상 스캔에서 감지된 '즉시 링크 교체 필요' 블로그·카페 게시글 목록입니다!**")
                st.dataframe(pd.DataFrame(st.session_state["dead_blog_posts"]), use_container_width=True, hide_index=True)

            st.markdown("#### 📋 전체 상품별 블로그·카페 홍보글 매핑 현황")
            st.dataframe(
                pd.DataFrame(blog_audit_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "블로그/카페 게시글 바로가기": st.column_config.LinkColumn("블로그/카페 글", display_text="📝 게시글 열기"),
                    "연결된 스마트스토어": st.column_config.LinkColumn("내 스토어", display_text="🏪 스토어 열기"),
                    "원본 도매처": st.column_config.LinkColumn("도매처", display_text="🔗 도매처 열기"),
                },
            )

        with sub_m3:
            st.subheader("⚔️ 경쟁사(타 판매자) 최저가 비교 & 마진 방어 시뮬레이터")
            st.write("나와 똑같은 위탁 상품을 파는 경쟁사의 가격을 비교하고, 내가 가격을 내렸을 때 남는 순수익을 즉시 시뮬레이션합니다.")

            comp_sel = st.selectbox("비교할 내 스토어 상품 선택", product_list, key="comp_prod_sel")
            if comp_sel != "➕ [직접 수동 입력 / 신규 상품 작성]":
                c_idx = int(comp_sel.split(" | ")[0])
                c_row = df.iloc[c_idx]
                my_w_p = int(c_row.get("도매원가_num", 15000))
                my_s_p = int(c_row.get("판매가_num", 25000))
            else:
                my_w_p = 15000
                my_s_p = 25000

            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                my_curr_price = st.number_input("내 스토어 현재 판매가 (원)", value=my_s_p, step=500)
                my_curr_w = st.number_input("내 도매 공급원가 (원)", value=my_w_p, step=500)
            with cc2:
                comp_manual_price = st.number_input("경쟁사 현재 판매가 입력 (원)", value=my_s_p - 1000, step=500)
                comp_url_input = st.text_input("경쟁사 상품 URL (선택 - 스캔 테스트용)", placeholder="https://...")
            with cc3:
                match_price = comp_manual_price - 100
                fee_at_match = int(round(match_price * 0.056))
                profit_at_match = match_price - my_curr_w - fee_at_match
                margin_at_match = (profit_at_match / match_price * 100) if match_price > 0 else 0.0

                if profit_at_match > 2000:
                    st.success(
                        f"💡 **최저가 방어 가능! ({match_price:,}원 세팅 시)**\n\n"
                        f"- 경쟁사보다 100원 더 싸게 팔아도 개당 **{profit_at_match:,}원 (마진 {margin_at_match:.1f}%)**이 남습니다!"
                    )
                else:
                    st.error(
                        f"🚨 **출혈 경쟁 금지! ({match_price:,}원 세팅 시)**\n\n"
                        f"- 개당 순수익이 **{profit_at_match:,}원 ({margin_at_match:.1f}%)**으로 떨어집니다. 가격 대신 사은품/상세페이지(인포그래픽)로 승부하세요!"
                    )

            if comp_url_input and st.button("🔍 경쟁사 URL 가격 자동 추출 시도", use_container_width=True):
                c_badge, c_ext_p, c_msg = scan_competitor_page(comp_url_input, my_curr_price)
                st.info(f"**{c_badge}** | 추출 가격: {c_ext_p:,}원 | {c_msg}")

    # ==================================================================================
    # MENU 3: 📦 발주서 변환 & CS 관리 (스마트스토어 주문 엑셀 -> 도매처 발주서 자동 변환 + CS 복사함)
    # ==================================================================================
    elif main_menu == "📦 3. 발주서 변환 & CS 관리":
        sub_o1, sub_o2 = st.tabs([
            "📦 1. 스마트스토어 주문서 ➡️ 도매처 발주 엑셀 자동 변환기",
            "💬 2. 위탁판매 상황별 고객 CS 1초 복사함",
        ])

        with sub_o1:
            st.subheader("📦 스마트스토어 신규 주문서 ➡️ 도매처(도매꾹·오너클랜) 일괄 발주 양식 변환기")
            st.write(
                "스마트스토어에서 다운로드한 **신규 주문 엑셀/CSV 파일**을 올리거나 아래 표에서 직접 확인하면, "
                "**도매꾹(도매매) 및 오너클랜 대량 발주 업로드용 CSV 파일**로 1초 만에 변환해 줍니다."
            )

            uploaded_order_file = st.file_uploader(
                "📂 스마트스토어 주문내역 파일 업로드 (.csv 또는 .xlsx 지원 - 파일이 없어도 아래 샘플로 즉시 테스트 가능)",
                type=["csv", "xlsx"],
            )

            if uploaded_order_file is not None:
                try:
                    if uploaded_order_file.name.endswith(".csv"):
                        try:
                            raw_orders = pd.read_csv(uploaded_order_file, encoding="utf-8")
                        except UnicodeDecodeError:
                            uploaded_order_file.seek(0)
                            raw_orders = pd.read_csv(uploaded_order_file, encoding="cp949")
                    else:
                        raw_orders = pd.read_excel(uploaded_order_file)
                    st.success(f"✅ 총 {len(raw_orders)}건의 스마트스토어 주문 데이터를 불러왔습니다!")
                except Exception as ex:
                    st.error(f"파일 읽기 오류: {ex}")
                    raw_orders = pd.DataFrame()
            else:
                st.caption("💡 현재 파일이 업로드되지 않아 **테스트용 스마트스토어 신규 주문 3건**으로 미리보기를 표시합니다.")
                raw_orders = pd.DataFrame([
                    {
                        "상품주문번호": "202611120001",
                        "상품명": "캠핑용 초경량 감성 우드 롤테이블",
                        "옵션정보": "컬러: 내추럴우드",
                        "수량": 1,
                        "수취인명": "김민수",
                        "수취인연락처1": "010-1234-5678",
                        "우편번호": "13529",
                        "배송지": "경기도 성남시 분당구 판교역로 166 101동 202호",
                        "배송메세지": "문 앞에 놓아주세요.",
                    },
                    {
                        "상품주문번호": "202611120002",
                        "상품명": "충전식 손난로 보조배터리 10000mAh",
                        "옵션정보": "컬러: 크림화이트",
                        "수량": 2,
                        "수취인명": "이서연",
                        "수취인연락처1": "010-9876-5432",
                        "우편번호": "06236",
                        "배송지": "서울특별시 강남구 테헤란로 152 3층",
                        "배송메세지": "경비실에 맡겨주세요.",
                    },
                ])

            if not raw_orders.empty:
                def pick_col(df_in, candidates, default_val=""):
                    for c in candidates:
                        if c in df_in.columns:
                            return df_in[c].fillna(default_val).astype(str)
                    return pd.Series([default_val] * len(df_in))

                # 내 구글 시트의 상품명과 매칭하여 도매처 링크/원가 자동 조인
                sheet_map = {}
                for _, s_r in df.iterrows():
                    sheet_map[str(s_r.get("상품명", "")).strip()] = (
                        str(s_r.get("도매처명", "-")),
                        str(s_r.get("도매처링크", "")),
                        int(s_r.get("도매원가_num", 0)),
                    )

                p_names = pick_col(raw_orders, ["상품명", "주문상품명", "품목명"])
                opts = pick_col(raw_orders, ["옵션정보", "옵션", "선택사항"], "단품")
                qtys = pick_col(raw_orders, ["수량", "주문수량", "구매수량"], "1")
                recs = pick_col(raw_orders, ["수취인명", "받는분", "수령인"])
                phones = pick_col(raw_orders, ["수취인연락처1", "수취인연락처", "전화번호", "핸드폰"])
                zips = pick_col(raw_orders, ["우편번호", "우편번호(5자리)"], "00000")
                addrs = pick_col(raw_orders, ["배송지", "통합배송지", "주소", "수취인주소"])
                memos = pick_col(raw_orders, ["배송메세지", "배송메모", "요청사항"], "안전배송 부탁드립니다.")

                converted_rows = []
                for i in range(len(raw_orders)):
                    pn = p_names.iloc[i].strip()
                    w_vendor, w_link, w_cost = sheet_map.get(pn, ("직접확인", "", 0))
                    converted_rows.append({
                        "순번": i + 1,
                        "매칭도매처": w_vendor,
                        "도매처상품링크": w_link,
                        "도매예상발주액": int(pd.to_numeric(qtys.iloc[i], errors="coerce") or 1) * w_cost,
                        "받는사람(수취인)": recs.iloc[i],
                        "휴대폰번호": phones.iloc[i],
                        "우편번호": zips.iloc[i],
                        "배송지주소": addrs.iloc[i],
                        "주문상품명": pn,
                        "옵션명": opts.iloc[i],
                        "발주수량": qtys.iloc[i],
                        "배송메모": memos.iloc[i],
                    })

                df_conv = pd.DataFrame(converted_rows)
                st.markdown("#### 📋 변환 완료된 도매처 통합 발주 리스트 (수취인·도매처 자동 매칭)")
                st.dataframe(df_conv, use_container_width=True, hide_index=True)

                dl_c1, dl_c2 = st.columns(2)
                with dl_c1:
                    dome_csv = df_conv[[
                        "받는사람(수취인)", "휴대폰번호", "우편번호", "배송지주소", "주문상품명", "옵션명", "발주수량", "배송메모"
                    ]].to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "📥 [도매꾹/도매매 규격] 대량 발주서 CSV 다운로드",
                        data=dome_csv,
                        file_name=f"도매매_발주서_{today.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                    )
                with dl_c2:
                    owner_csv = df_conv[[
                        "주문상품명", "옵션명", "발주수량", "받는사람(수취인)", "휴대폰번호", "우편번호", "배송지주소", "배송메모", "도매처상품링크"
                    ]].to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        "📥 [오너클랜/일반도매 규격] 발주서 CSV 다운로드",
                        data=owner_csv,
                        file_name=f"오너클랜_발주서_{today.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

        with sub_o2:
            st.subheader("💬 위탁판매 상황별 고객 CS(톡톡/문자) 답변 1초 복사함")
            cs_col1, cs_col2, cs_col3, cs_col4 = st.columns(4)
            with cs_col1:
                cs_cust_name = st.text_input("👤 고객명", value="홍길동")
            with cs_col2:
                cs_prod_name = st.text_input("📦 주문 상품명", value="캠핑용 감성 우드 롤테이블")
            with cs_col3:
                cs_delay_date = st.text_input("🚚 예상 출고일 / 지연 안내일", value="내일(금요일)")
            with cs_col4:
                cs_return_fee = st.text_input("💵 왕복 반품 배송비", value="6,000원")

            cs_grid1, cs_grid2 = st.columns(2, gap="large")

            msg_soldout = (
                f"안녕하세요, {cs_cust_name} 고객님! 저희 스토어를 찾아주셔서 진심으로 감사드립니다.\n\n"
                f"주문해주신 [{cs_prod_name}] 상품의 출고를 위해 검수하던 중, 공급처의 갑작스러운 재고 소진 및 마지막 잔여 수량 불량이 확인되어 부득이하게 정상 상품 발송이 어려운 상황입니다.\n\n"
                f"기대하고 주문해 주셨을 텐데 불편을 드려 정말 죄송합니다. 고객님의 소중한 결제 금액이 묶이지 않도록 우선 취소 처리를 도와드리고자 하며, 재입고 시 우선 안내해 드리겠습니다.\n"
                f"다시 한번 너그러운 양해를 부탁드립니다. 감사합니다."
            )
            msg_delay = (
                f"안녕하세요, {cs_cust_name} 고객님! 주문해주신 [{cs_prod_name}] 배송 관련 안내드립니다.\n\n"
                f"현재 해당 상품의 주문량 급증으로 인해 공급처 검수 및 패킹 작업이 평소보다 하루 정도 지연되고 있습니다.\n"
                f"고객님의 상품은 [{cs_delay_date}] 최우선으로 꼼꼼히 검수하여 출고될 예정이며, 송장 번호가 나오는 대로 즉시 입력해 드리겠습니다.\n\n"
                f"조금만 기다려주시면 안전하고 깨끗한 상품으로 보답하겠습니다. 감사합니다!"
            )
            msg_return = (
                f"안녕하세요, {cs_cust_name} 고객님! 문의하신 [{cs_prod_name}] 반품 절차 안내드립니다.\n\n"
                f"단순 변심 및 사이즈/옵션 착오로 인한 반품의 경우, 수령 후 7일 이내 미개봉·미사용 상태에 한해 가능하며 초기 발송비를 포함한 왕복 택배비 [{cs_return_fee}]이 발생합니다.\n\n"
                f"스마트스토어 [주문내역 -> 반품요청]을 접수해 주시면 지정 택배사 기사님이 1~2일 내 방문 수거하며, 상품 입고 및 검수 완료 후 반품 배송비를 차감한 금액이 자동 환불됩니다. 감사합니다."
            )
            msg_review = (
                f"안녕하세요, {cs_cust_name} 고객님! 주문하신 [{cs_prod_name}]은 안전하게 잘 받아보셨나요?\n\n"
                f"사용해 보시면서 혹시라도 불편한 점이 있으시면 언제든 톡톡으로 말씀해 주세요! 상품이 마음에 드셨다면 잠깐 시간 내어 [구매확정]과 [포토리뷰]를 남겨주시면 저희 스토어 운영에 정말 큰 힘이 됩니다.\n\n"
                f"항상 행복하시고 오늘도 기분 좋은 하루 보내세요. 감사합니다! 😊"
            )

            with cs_grid1:
                render_copy_box("🚨 1. 도매처 갑작스러운 품절/단종 양해 안내", msg_soldout, "cs1", "#dc2626", 240)
                render_copy_box("📦 3. 단순변심 반품 절차 & 왕복 배송비 안내", msg_return, "cs3", "#475569", 240)
            with cs_grid2:
                render_copy_box("⏳ 2. 도매처 출고/배송 지연 사전 양해 안내", msg_delay, "cs2", "#d97706", 240)
                render_copy_box("⭐ 4. 배송 완료 후 구매확정 & 포토리뷰 유도", msg_review, "cs4", "#03c75a", 240)

    # ==================================================================================
    # MENU 4: 🎨 마케팅·썸네일 스튜디오 (5종 인포그래픽 + 1000x1000 썸네일 배지 합성기 + SEO 원고)
    # ==================================================================================
    elif main_menu == "🎨 4. 마케팅·썸네일 스튜디오":
        sub_mk1, sub_mk2, sub_mk3 = st.tabs([
            "🎨 1. 5종 블로그·카페 인포그래픽 카드 제작",
            "🖼️ 2. 스마트스토어 대표 썸네일(1000x1000) 배지 합성기",
            "🚀 3. SEO 황금 상품명 변환 & 블로그 원고 생성기",
        ])

        with sub_mk1:
            st.subheader("🎨 5종 블로그·카페 인포그래픽 스튜디오 (클립보드 복사 & PNG 사진 저장)")

            top_sel1, top_sel2 = st.columns([1.2, 1.2])
            with top_sel1:
                selected_prod_str = st.selectbox("1️⃣ 시트에 등록된 상품을 불러오거나 직접 작성하세요", product_list, key="info_prod_sel")
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
                    "🖼️ 상품 이미지 URL (선택사항)",
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
                    <div id="capture-wrapper">{infographic_html}</div>
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
                        html2canvas(target, {{ scale: 2, useCORS: true, allowTaint: true, backgroundColor: '#ffffff' }}).then(canvas => {{
                            const link = document.createElement('a');
                            link.download = '{safe_filename}_인포그래픽.png';
                            link.href = canvas.toDataURL('image/png');
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            showMessage('🎉 PNG 이미지 파일이 다운로드되었습니다!', '#dbeafe', '#1e40af');
                        }});
                    }}
                    </script>
                </body>
                </html>
                """
                components.html(component_html, height=880, scrolling=True)

        with sub_mk2:
            st.subheader("🖼️ 스마트스토어 대표 썸네일(1000x1000 정사각형) 프레임·배지 합성 스튜디오")
            st.write(
                "도매처 원본 대표 이미지를 그대로 쓰면 노출 점수가 깎입니다. "
                "**내電腦 사진을 불러와 컬러 테두리와 `[오늘출발]`, `[사은품증정]` 스티커 배지를 얹어 1000x1000px 정사각형 PNG**로 즉시 저장하세요!"
            )

            th_c1, th_c2 = st.columns([1.0, 1.3], gap="large")
            with th_c1:
                th_top_left = st.text_input("🏷️ 좌측 상단 스티커 배지", value="🚀 오늘출발")
                th_top_right = st.text_input("🔥 우측 상단 원형 강조 배지", value="특가\n할인")
                th_bottom_bar = st.text_input("📢 하단 와이드 배너 문구", value="전용 파우치 무료 증정 + 무료배송")
                th_color = st.selectbox("🎨 프레임 & 배지 컬러", ["#03c75a", "#e11d48", "#1e3a8a", "#111827", "#d97706"])
                th_border_px = st.slider("🔲 정사각형 외곽 테두리 두께 (px)", min_value=0, max_value=40, value=18)

            with th_c2:
                thumb_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="utf-8">
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .ctrl-box {{
                        background:#1e293b; color:#fff; padding:14px; border-radius:10px; margin-bottom:12px;
                        display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;
                    }}
                    .dl-btn {{
                        background:{th_color}; color:#fff; border:none; padding:12px 20px; border-radius:8px;
                        font-size:15px; font-weight:900; cursor:pointer;
                    }}
                    canvas {{
                        width: 440px; height: 440px; border-radius: 10px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2); background: #ffffff;
                        display: block; margin: 0 auto;
                    }}
                </style>
                </head>
                <body>
                    <div class="ctrl-box">
                        <div>
                            <div style="font-size:13px; font-weight:bold; margin-bottom:4px;">📂 1. 내 컴퓨터에서 도매처 원본 상품 사진 선택</div>
                            <input type="file" id="imgInput" accept="image/*" style="font-size:13px;" />
                        </div>
                        <button class="dl-btn" onclick="downloadThumb()">📸 1000x1000 정사각형 PNG 저장</button>
                    </div>
                    <canvas id="thumbCanvas" width="1000" height="1000"></canvas>

                    <script>
                    const canvas = document.getElementById('thumbCanvas');
                    const ctx = canvas.getContext('2d');
                    let loadedImg = null;

                    function drawCanvas() {{
                        ctx.fillStyle = '#f8fafc';
                        ctx.fillRect(0, 0, 1000, 1000);

                        if (loadedImg) {{
                            const scale = Math.max(1000 / loadedImg.width, 1000 / loadedImg.height);
                            const nw = loadedImg.width * scale;
                            const nh = loadedImg.height * scale;
                            ctx.drawImage(loadedImg, (1000 - nw) / 2, (1000 - nh) / 2, nw, nh);
                        }} else {{
                            ctx.fillStyle = '#94a3b8';
                            ctx.font = 'bold 34px Malgun Gothic';
                            ctx.textAlign = 'center';
                            ctx.fillText('위 [파일 선택]을 눌러 상품 사진을 올려주세요', 500, 460);
                            ctx.font = '26px Malgun Gothic';
                            ctx.fillText('(1000 x 1000 스마트스토어 대표 썸네일 규격)', 500, 515);
                        }}

                        // 하단 배너 바
                        const btmText = `{th_bottom_bar}`;
                        if (btmText.trim() !== '') {{
                            ctx.fillStyle = 'rgba(17, 24, 39, 0.88)';
                            ctx.fillRect(0, 870, 1000, 130);
                            ctx.fillStyle = '#facc15';
                            ctx.font = '900 44px Malgun Gothic';
                            ctx.textAlign = 'center';
                            ctx.fillText(btmText, 500, 950);
                        }}

                        // 외곽 테두리
                        const bPx = {th_border_px};
                        if (bPx > 0) {{
                            ctx.strokeStyle = '{th_color}';
                            ctx.lineWidth = bPx * 2;
                            ctx.strokeRect(0, 0, 1000, 1000);
                        }}

                        // 좌측 상단 배지
                        const tlText = `{th_top_left}`;
                        if (tlText.trim() !== '') {{
                            ctx.fillStyle = '{th_color}';
                            ctx.beginPath();
                            ctx.roundRect(45, 45, 340, 95, 18);
                            ctx.fill();
                            ctx.fillStyle = '#ffffff';
                            ctx.font = '900 42px Malgun Gothic';
                            ctx.textAlign = 'center';
                            ctx.fillText(tlText, 215, 108);
                        }}

                        // 우측 상단 원형 배지
                        const trText = `{th_top_right.replace(chr(10), "\\n")}`;
                        if (trText.trim() !== '') {{
                            ctx.fillStyle = '#e11d48';
                            ctx.beginPath();
                            ctx.arc(870, 130, 90, 0, Math.PI * 2);
                            ctx.fill();
                            ctx.lineWidth = 6;
                            ctx.strokeStyle = '#ffffff';
                            ctx.stroke();

                            ctx.fillStyle = '#ffffff';
                            ctx.font = '900 38px Malgun Gothic';
                            ctx.textAlign = 'center';
                            const lines = trText.split('\\n');
                            if (lines.length > 1) {{
                                ctx.fillText(lines[0], 870, 118);
                                ctx.fillText(lines[1], 870, 165);
                            }} else {{
                                ctx.fillText(lines[0], 870, 142);
                            }}
                        }}
                    }}

                    document.getElementById('imgInput').addEventListener('change', function(e) {{
                        const file = e.target.files[0];
                        if (!file) return;
                        const reader = new FileReader();
                        reader.onload = function(ev) {{
                            const img = new Image();
                            img.onload = function() {{
                                loadedImg = img;
                                drawCanvas();
                            }};
                            img.src = ev.target.result;
                        }};
                        reader.readAsDataURL(file);
                    }});

                    function downloadThumb() {{
                        const link = document.createElement('a');
                        link.download = '스마트스토어_대표썸네일_1000x1000.png';
                        link.href = canvas.toDataURL('image/png');
                        link.click();
                    }}

                    drawCanvas();
                    </script>
                </body>
                </html>
                """
                components.html(thumb_html, height=560, scrolling=False)

        with sub_mk3:
            st.subheader("🚀 스마트스토어 SEO 황금 상품명 변환기 & 블로그·카페 홍보 원고 생성기")
            seo_sel = st.selectbox("시트 상품 불러오기 (또는 직접 입력)", product_list, key="seo_prod_sel")
            if seo_sel != "➕ [직접 수동 입력 / 신규 상품 작성]":
                s_idx = int(seo_sel.split(" | ")[0])
                s_row = df.iloc[s_idx]
                raw_default_name = str(s_row.get("상품명", ""))
                raw_default_price = int(s_row.get("판매가_num", 28900))
                raw_default_url = str(s_row.get("스마트스토어링크", "https://smartstore.naver.com/"))
            else:
                raw_default_name = "[당일발송/특가] ★캠핑용★ 초경량 감성 우드 롤테이블 / 접이식 캠핑테이블"
                raw_default_price = 28900
                raw_default_url = "https://smartstore.naver.com/"

            sc1, sc2 = st.columns([1.05, 1.35], gap="large")
            with sc1:
                raw_wholesale_title = st.text_input("도매처 원본 상품명", value=raw_default_name)
                target_main_kw = st.text_input("핵심 타겟 키워드 (쉼표 구분)", value="감성캠핑용품, 접이식우드테이블, 피크닉테이블")
                target_sub_kw = st.text_input("용도 / 타겟층 수식어", value="차박, 캠핑초보, 베란다홈캠핑, 집들이선물")
                spec_kw = st.text_input("핵심 스펙 / 특징 단어", value="초경량, 원목, 파우치증정")
                post_tone = st.radio(
                    "📝 생성할 블로그/카페 홍보 원고 스타일",
                    ["① 블로그 내돈내산·실사용 추천 후기톤", "② 블로그 정보성 꼼꼼 비교·분석톤", "③ 네이버 카페 회원 전용 공동구매·특가 공지톤"],
                )

            cleaned_base = re.sub(r"\[.*?\]|\(.*?\)|★|☆|♥|♡|/|_|!|\+|~|-", " ", raw_wholesale_title)
            for bw in ["당일발송", "무료배송", "특가", "할인", "세일", "최저가", "인기", "추천", "주문폭주", "정품"]:
                cleaned_base = cleaned_base.replace(bw, " ")

            base_tokens = []
            for tk in cleaned_base.split():
                if tk not in base_tokens and len(tk) >= 1:
                    base_tokens.append(tk)
            clean_core_name = " ".join(base_tokens)

            main_kws = [k.strip() for k in target_main_kw.split(",") if k.strip()]
            sub_kws = [k.strip() for k in target_sub_kw.split(",") if k.strip()]
            spec_kws = [k.strip() for k in spec_kw.split(",") if k.strip()]

            m1_k = main_kws[0] if len(main_kws) > 0 else "인기상품"
            m2_k = main_kws[1] if len(main_kws) > 1 else ""
            s1_k = sub_kws[0] if len(sub_kws) > 0 else "다용도"
            s2_k = sub_kws[1] if len(sub_kws) > 1 else ""
            sp1_k = spec_kws[0] if len(spec_kws) > 0 else "고급형"
            sp2_k = spec_kws[1] if len(spec_kws) > 1 else ""

            seo_candidates = [
                f"{m1_k} {clean_core_name} {s1_k} {sp1_k} {sp2_k}".strip(),
                f"{s1_k} {s2_k} {clean_core_name} {m1_k} {sp1_k}".strip(),
                f"{sp1_k} {clean_core_name} {m1_k} {m2_k} {s1_k}".strip(),
                f"{clean_core_name} {m1_k} {s1_k} {s2_k} {sp1_k}".strip(),
                f"{m1_k} {m2_k} {sp1_k} {clean_core_name} {s1_k}".strip(),
            ]
            final_seo_list = []
            for cand in seo_candidates:
                uniq_words = []
                for w in cand.split():
                    if w not in uniq_words:
                        uniq_words.append(w)
                joined = " ".join(uniq_words)[:48]
                final_seo_list.append(f"{joined} ({len(joined)}자)")

            seo_names_block = "\n".join([f"{i+1}. {name}" for i, name in enumerate(final_seo_list)])

            all_tag_seeds = base_tokens + main_kws + sub_kws + spec_kws + ["스마트스토어추천", "가성비템", "내돈내산추천"]
            hashtags = []
            for tg in all_tag_seeds:
                clean_tg = re.sub(r"\s+", "", tg)
                if clean_tg and f"#{clean_tg}" not in hashtags:
                    hashtags.append(f"#{clean_tg}")
            hashtag_str = " ".join(hashtags[:15])

            if "①" in post_tone:
                blog_draft = (
                    f"[추천 타이틀] {m1_k} 고민 끝! {clean_core_name} 실사용 솔직 정리 ✨\n\n"
                    f"안녕하세요! 요즘 {s1_k} 준비하면서 정말 많은 제품을 비교해 봤는데요.\n"
                    f"그러다 결국 정착하게 된 가성비 끝판왕 '{clean_core_name}'을 소개해 드립니다!\n\n"
                    f"📌 [핵심 장점 3가지]\n"
                    f"1️⃣ {sp1_k} 사양이라 마감 퀄리티가 기대 이상으로 탄탄합니다.\n"
                    f"2️⃣ 초보자도 1분이면 바로 세팅할 수 있을 만큼 간편해요 ({sp2_k}).\n"
                    f"3️⃣ {s1_k}뿐만 아니라 {s2_k} 용도로도 디자인이 정말 깔끔합니다.\n\n"
                    f"👉 공식 스마트스토어({raw_default_price:,}원 특가): {raw_default_url}\n\n"
                    f"{hashtag_str}"
                )
            elif "②" in post_tone:
                blog_draft = (
                    f"[추천 타이틀] {m1_k} 실패 없이 고르는 법! ({clean_core_name} 비교 분석) 📊\n\n"
                    f"🔍 [구매 전 반드시 확인해야 할 3대 기준]\n"
                    f"✔️ 체크 1. 소재와 내구성: '{sp1_k}' 여부를 꼭 확인하세요.\n"
                    f"✔️ 체크 2. 휴대성과 구성품: '{sp2_k}' 등 필수 구성이 포함되어 있는지 따져보세요.\n"
                    f"✔️ 체크 3. 빠른 국내 발송 & AS: 불량 시 즉시 교환되는 곳인지가 핵심입니다.\n\n"
                    f"👉 공식 판매처 상세페이지 바로가기: {raw_default_url}\n\n"
                    f"{hashtag_str}"
                )
            else:
                blog_draft = (
                    f"📢 [카페 회원 전용 특가 공지] {clean_core_name} 한정수량 안내 🔥\n\n"
                    f"• 상품명: {clean_core_name} ({sp1_k} / {sp2_k})\n"
                    f"• 회원 특별가: {raw_default_price:,}원\n"
                    f"• 출고 안내: 평일 오후 2시 이전 주문 시 당일 발송\n\n"
                    f"👉 네이버 스마트스토어 바로가기: {raw_default_url}\n\n"
                    f"{hashtag_str}"
                )

            with sc2:
                render_copy_box("🏷️ SEO 추천 상품명 5가지 (특수문자·중복단어 제거 완료)", seo_names_block, "seo_names", "#1e3a8a", 215)
                render_copy_box("📝 블로그·카페 맞춤형 포스팅 원고 & 해시태그 15개", blog_draft, "blog_draft", "#03c75a", 360)

    # ==================================================================================
    # MENU 5: 💰 수익장부 & 세금 계산기 (장부 + 월별기록 + 마진역산 & 부가세/종소세 계산기 + 시트원본)
    # ==================================================================================
    elif main_menu == "💰 5. 수익장부 & 세금 계산기":
        sub_f1, sub_f2, sub_f3, sub_f4 = st.tabs([
            "💎 1. 실시간 수익장부 & 효자 랭킹",
            "🗓️ 2. 월별 정산 마감 & 누적 성장 그래프",
            "🧾 3. 목표 마진 역산 & 부가세·소득세 계산기",
            "📊 4. 구글 시트 원본 데이터 보기",
        ])

        col_ym, col_fee_opt, col_extra_exp = st.columns(3)
        with col_ym:
            settlement_ym = st.text_input("🗓️ 정산 기준 연월 (예: 2026-11)", value=today.strftime("%Y-%m"))
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
                "판매수량": f"{qty:,}개",
                "총매출액 (수익)": f"{item_rev:,}원",
                "도매원가 합계": f"{item_w_cost:,}원",
                "수수료 합계": f"{item_fee_cost:,}원",
                "광고/기타지출": f"{ad_c:,}원",
                "최종 순수익": item_net_profit,
                "순수익(표시)": f"{item_net_profit:,}원",
                "실마진율": f"{item_roi:.1f}%",
            })

        total_ad_and_extra = total_ad_cost + extra_fixed_cost
        total_expense = total_wholesale_cost + total_naver_fee + total_ad_and_extra
        final_net_profit = total_rev - total_expense
        overall_margin_rate = (final_net_profit / total_rev * 100) if total_rev > 0 else 0.0
        df_ledger = pd.DataFrame(ledger_rows)

        with sub_f1:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📈 총 매출액 (Gross 수익)", f"{total_rev:,}원")
            k2.metric("💸 총 지출 합계 (원가+수수료+광고)", f"{total_expense:,}원", f"-도매원가 {total_wholesale_cost:,}원", delta_color="inverse")
            k3.metric("💎 최종 순수익 (Net Profit)", f"{final_net_profit:,}원", f"마진율 {overall_margin_rate:.1f}%")
            k4.metric("📢 마케팅·기타 총지출", f"{total_ad_and_extra:,}원", f"네이버수수료 {total_naver_fee:,}원 별도", delta_color="off")

            st.markdown("---")
            col_l_table, col_l_chart = st.columns([1.35, 1.15], gap="large")
            with col_l_table:
                st.markdown(f"#### 📋 [{settlement_ym}] 상품별 수익·지출 상세 명세서")
                display_cols = [
                    "상품명", "도매처", "판매수량", "총매출액 (수익)",
                    "도매원가 합계", "수수료 합계", "광고/기타지출", "순수익(표시)", "실마진율"
                ]
                st.dataframe(df_ledger[display_cols], use_container_width=True, hide_index=True)

                csv_backup_bytes = df_ledger[display_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label=f"💾 [{settlement_ym}] 상품별 정산 상세내역 CSV 다운로드",
                    data=csv_backup_bytes,
                    file_name=f"스마트스토어_정산장부_{settlement_ym}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col_l_chart:
                st.markdown("#### 🏆 효자 상품 순수익 랭킹 (가로형 한눈에 보기)")
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
                <html><head><meta charset="utf-8">
                <style>
                    body {{ margin: 0; padding: 0; font-family: 'Malgun Gothic', sans-serif; background-color: transparent; }}
                    .rank-container {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; color: #f8fafc; }}
                    .rank-card {{ margin-bottom: 14px; }}
                    .rank-card:last-child {{ margin-bottom: 0; }}
                    .rank-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 8px; flex-wrap: wrap; }}
                    .rank-title {{ display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 800; color: #ffffff; }}
                    .rank-badge {{ font-size: 11.5px; padding: 2px 8px; border-radius: 6px; color: #ffffff; font-weight: 900; white-space: nowrap; }}
                    .prod-name {{ word-break: keep-all; }}
                    .rank-profit {{ font-size: 14.5px; font-weight: 900; white-space: nowrap; }}
                    .sub-info {{ font-size: 11.5px; color: #94a3b8; font-weight: normal; }}
                    .progress-bg {{ width: 100%; height: 12px; background-color: #0f172a; border-radius: 999px; overflow: hidden; }}
                    .progress-fill {{ height: 100%; border-radius: 999px; }}
                </style></head>
                <body><div class="rank-container">{rank_bars_html}</div></body></html>
                """
                components.html(ranking_component_html, height=max(240, len(df_ranked) * 64 + 35), scrolling=True)

        with sub_f2:
            st.subheader("🗓️ 월별 정산 기록 마감 & 누적 수익 추이 (`월별_수익지출_요약` 탭 연동)")
            tsv_monthly_row = f"{settlement_ym}\t{total_rev}\t{total_wholesale_cost}\t{total_naver_fee}\t{total_ad_and_extra}\t{final_net_profit}\t{overall_margin_rate:.1f}%"
            pretty_monthly_preview = (
                f"📌 [복사될 데이터 미리보기 — 구글 시트 '월별_수익지출_요약' 탭 A열 클릭 후 Ctrl+V 하면 7칸에 자동 입력됩니다]\n"
                f"• 기준월: {settlement_ym}  |  • 총매출액: {total_rev:,}원  |  • 도매원가합계: {total_wholesale_cost:,}원  |  "
                f"• 네이버수수료: {total_naver_fee:,}원  |  • 광고및기타지출: {total_ad_and_extra:,}원  |  "
                f"• 최종순수익: {final_net_profit:,}원 ({overall_margin_rate:.1f}%)"
            )
            render_copy_box(
                f"📥 [{settlement_ym}] 월간 정산 마감 데이터 한 줄 복사",
                tsv_monthly_row,
                "monthly_tsv",
                "#2563eb",
                145,
                display_text=pretty_monthly_preview,
            )

            df_m_valid = df_monthly_raw[df_monthly_raw["기준월"].astype(str).str.match(r"^20\d{2}-\d{2}")].copy()
            if not df_m_valid.empty:
                for m_col in ["총매출액", "도매원가합계", "네이버수수료합계", "광고및기타지출", "최종순수익"]:
                    if m_col in df_m_valid.columns:
                        df_m_valid[f"{m_col}_num"] = pd.to_numeric(
                            df_m_valid[m_col].astype(str).str.replace(r"[^0-9.-]", "", regex=True), errors="coerce"
                        ).fillna(0)
                    else:
                        df_m_valid[f"{m_col}_num"] = 0

                m_hist_left, m_hist_right = st.columns([1.3, 1.2], gap="large")
                with m_hist_left:
                    st.markdown("#### 📜 구글 시트에 저장된 월별 수익·지출 누적 장부")
                    m_show_rows = []
                    for _, m_r in df_m_valid.iterrows():
                        m_rev = int(m_r["총매출액_num"])
                        m_net = int(m_r["최종순수익_num"])
                        m_rate = (m_net / m_rev * 100) if m_rev > 0 else 0.0
                        m_show_rows.append({
                            "기준월": str(m_r["기준월"]),
                            "총매출액": f"{m_rev:,}원",
                            "도매원가합계": f"{int(m_r['도매원가합계_num']):,}원",
                            "수수료합계": f"{int(m_r['네이버수수료합계_num']):,}원",
                            "광고/기타지출": f"{int(m_r['광고및기타지출_num']):,}원",
                            "최종순수익": f"{m_net:,}원",
                            "수익률": f"{m_rate:.1f}%",
                        })
                    st.dataframe(pd.DataFrame(m_show_rows), use_container_width=True, hide_index=True)

                with m_hist_right:
                    st.markdown("#### 📈 월별 매출 & 최종 순수익 성장 추이")
                    max_m_rev = max(df_m_valid["총매출액_num"].max(), 1)
                    m_bars_html = ""
                    for _, m_r in df_m_valid.iterrows():
                        ym_str = str(m_r["기준월"])
                        rev_v = int(m_r["총매출액_num"])
                        net_v = int(m_r["최종순수익_num"])
                        rev_w = max(2, min(100, int((rev_v / max_m_rev) * 100)))
                        net_w = max(2, min(100, int((net_v / max_m_rev) * 100))) if net_v > 0 else 0
                        m_bars_html += f"""
                        <div style="margin-bottom: 12px;">
                            <div style="display:flex; justify-content:space-between; font-size:13.5px; font-weight:800; color:#ffffff; margin-bottom:4px;">
                                <span>🗓️ {ym_str}</span>
                                <span>매출 {rev_v:,}원 / <span style="color:#34d399;">순수익 {net_v:,}원</span></span>
                            </div>
                            <div style="width:100%; height:10px; background:#0f172a; border-radius:999px; overflow:hidden; margin-bottom:3px;">
                                <div style="width:{rev_w}%; height:100%; background:#3b82f6; border-radius:999px;"></div>
                            </div>
                            <div style="width:100%; height:10px; background:#0f172a; border-radius:999px; overflow:hidden;">
                                <div style="width:{net_w}%; height:100%; background:#10b981; border-radius:999px;"></div>
                            </div>
                        </div>
                        """
                    m_chart_html = f"""
                    <!DOCTYPE html><html><head><meta charset="utf-8"></head>
                    <body style="margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent;">
                        <div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:16px;">
                            <div style="font-size:12px; color:#94a3b8; margin-bottom:10px;">🟦 파란 바: 월 총매출액 | 🟩 초록 바: 월 최종 순수익</div>
                            {m_bars_html}
                        </div>
                    </body></html>
                    """
                    components.html(m_chart_html, height=max(180, len(df_m_valid) * 62 + 50), scrolling=True)

        with sub_f3:
            st.markdown("#### 🧮 1. 목표 마진 & 스토어 쿠폰 할인가 역산 시뮬레이터")
            sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)
            with sim_c1:
                sim_w_cost = st.number_input("1️⃣ 도매 공급원가 (원)", value=14000, step=500)
            with sim_c2:
                sim_ship_subsidy = st.number_input("2️⃣ 내가 부담할 배송비 보조금", value=0, step=500)
            with sim_c3:
                sim_coupon = st.number_input("3️⃣ 스토어 할인 쿠폰 설정액 (원)", value=1000, step=500)
            with sim_c4:
                sim_target_profit = st.number_input("4️⃣ 개당 목표 순수익 (원)", value=6000, step=500)

            fee_ratio = ledger_fee_rate / 100.0
            required_actual_pay = int(round((sim_w_cost + sim_ship_subsidy + sim_target_profit) / (1.0 - fee_ratio), -2))
            recommended_list_price = required_actual_pay + sim_coupon
            bep_price = int(round((sim_w_cost + sim_ship_subsidy) / (1.0 - fee_ratio), -1))
            expected_margin_pct = (sim_target_profit / required_actual_pay * 100) if required_actual_pay > 0 else 0.0

            res_c1, res_c2, res_c3 = st.columns(3)
            res_c1.success(f"🏷️ **권장 등록 판매가: {recommended_list_price:,}원** (쿠폰 적용 실결제가: {required_actual_pay:,}원)")
            res_c2.info(f"💎 **개당 확정 순수익: {sim_target_profit:,}원** (순마진율: {expected_margin_pct:.1f}%)")
            res_c3.warning(f"⚠️ **손익분기점(BEP): {bep_price:,}원** (이 금액 미만 판매 시 적자)")

            st.markdown("---")
            st.markdown("#### 🏦 2. 간이과세자 / 일반과세자 예상 부가세 & 세금 적립금 계산기")
            st.write("위탁판매 매출과 매입(도매원가+수수료+광고비)을 바탕으로 세금 신고를 위해 통장에 미리 빼두어야 할 예상 세액을 계산합니다.")

            tx1, tx2, tx3 = st.columns(3)
            with tx1:
                tax_type = st.radio("사업자 과세 유형 선택", ["간이과세자 (소매업 부가가치율 15% 적용)", "일반과세자 (매출세액 10% - 매입세액 10%)"])
            with tx2:
                tax_rev = st.number_input("정산 기간 총 매출액 (원, VAT포함)", value=int(total_rev), step=100000)
            with tx3:
                tax_purchase = st.number_input("정산 기간 세금계산서 매입 합계 (도매원가+수수료+광고비)", value=int(total_expense), step=100000)

            if "간이" in tax_type:
                # 소매업 간이과세 부가세 약식 계산 (공급대가 * 15% * 10% - 매입세액공제 0.5%)
                est_vat = max(0, int(round(tax_rev * 0.015 - (tax_purchase / 1.1) * 0.005)))
                vat_note = "연 매출 1억 400만 원 미만 간이과세자 기준 (연 4,800만 원 미만 시 부가세 납부 면제)"
            else:
                # 일반과세자 부가세: (매출 - 매입) / 11
                est_vat = max(0, int(round((tax_rev - tax_purchase) / 11.0)))
                vat_note = "일반과세자 기준 (도매처 및 네이버 수수료 세금계산서 100% 수취 가정)"

            est_income_tax_reserve = max(0, int(round((tax_rev - tax_purchase - est_vat) * 0.066)))
            total_tax_reserve = est_vat + est_income_tax_reserve

            tk1, tk2, tk3 = st.columns(3)
            tk1.metric("🧾 예상 부가가치세 (VAT)", f"{est_vat:,}원")
            tk2.metric("🏦 종합소득세 대비 권장 적립액 (순이익의 6.6%)", f"{est_income_tax_reserve:,}원")
            tk3.metric("💰 세금 통장에 미리 빼둘 총액", f"{total_tax_reserve:,}원")
            st.caption(f"💡 안내: {vat_note}")

        with sub_f4:
            st.subheader("📊 구글 시트 원본 데이터 & 바로가기")
            st.markdown(f"👉 **[여기를 클릭해 내 구글 시트(상품관리 및 월별 수익장부) 바로 열기]({SHEET_BASE_URL}/edit)**")
            display_raw = [c for c in df.columns if not c.endswith("_num") and c != "상품선택"]
            st.dataframe(df[display_raw], use_container_width=True)
            st.dataframe(df_monthly_raw, use_container_width=True)

except Exception as e:
    st.error(f"앱 실행 중 오류가 발생했습니다. 상세 에러: {e}")
