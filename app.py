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
# 1. 핵심 데이터베이스 (시즌 기념일 / 지재권 금지어 / KC인증 / 도서산간 키워드)
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

LEGAL_RISK_DICT = {
    "다이소": ("상표권 침해 위험", "다용도 / 가성비 생활용품"),
    "벨크로": ("상표권 등록어 (Velcro)", "찍찍이 / 접착식 테이프"),
    "뽁뽁이": ("상표권 분쟁 주의", "에어캡 / 단열시트"),
    "스팸": ("상표권 침해 위험", "통조림 햄"),
    "포스트잇": ("3M 상표권 등록어", "점착 메모지"),
    "지퍼백": ("상표권 주의", "지퍼형 비닐팩 / 밀폐백"),
    "마약": ("식약처/청소년유해 금지어", "꿀잠 / 극세사 / 푹신한"),
    "치료": ("의료기기법 위반 (공산품 사용금지)", "케어 / 도움 / 완화 보조"),
    "완치": ("의료법/허위과대광고 위반", "집중 관리 / 컨디션 케어"),
    "교정": ("의료기기 오인 주의", "바른 자세 유도 / 서포트"),
    "혈액순환": ("의료기기법 위반 주의", "온열 마사지 / 피로 케어"),
    "아토피": ("의약품 오인 위반", "민감성 피부 / 저자극 보습"),
    "통증완화": ("의료기기법 위반 주의", "시원한 안마감 / 릴렉싱"),
    "거북목": ("의료적 질환명 사용 주의", "목 받침 / 바른 자세 스트레칭"),
    "최고": ("표시광고법 절대적 표현 주의", "프리미엄 / 베스트"),
    "최초": ("표시광고법 입증 필요 단어", "신개념 / 업그레이드형"),
}

KC_CERT_RULES = [
    {
        "category": "⚡ 전기·전자·배터리·무선 제품 (손난로, 청소기, 가습기, 랜턴, 충전기 등)",
        "keywords": ["충전", "배터리", "무선", "블루투스", "전구", "led", "가습기", "손난로", "청소기", "마사지기", "히터", "선풍기", "케이블"],
        "cert_name": "KC 전기용품 안전인증/안전확인 + 방송통신기자재(전파인증)",
        "check_point": "1) 내장 배터리(리튬이온)가 있으면 'KC 안전확인 번호' 필수!\n2) USB/블루투스/모터가 들어가면 '국립전파연구원 적합등록(R-R-...)' 번호 필수!\n3) 제품안전정보센터(safetykorea.kr)에서 도매처 인증번호가 폐기되지 않았는지 조회 필수.",
        "risk_level": "🔴 최고 위험 (미인증 판매 시 형사고발 및 스토어 즉시 정지)",
    },
    {
        "category": "👶 유아·어린이·완구·학용품 (13세 이하 사용 가능 제품)",
        "keywords": ["어린이", "유아", "아기", "키즈", "장난감", "완구", "인형", "학용품", "크레파스", "킥보드", "보행기", "네임스티커"],
        "cert_name": "KC 어린이제품 특별법 안전인증 / 안전확인 / 공급자적합성확인",
        "check_point": "1) '14세 이상 사용 가능'이라고 대충 적어놓고 어린이용 키워드를 쓰면 적발됩니다!\n2) 반드시 어린이제품 KC인증 번호와 사용연령 표기를 상세페이지에 기입하세요.",
        "risk_level": "🔴 최고 위험 (구매대행/위탁 모두 단속 1순위)",
    },
    {
        "category": "🍽️ 주방·식기·텀블러·조리도구 (입이나 음식에 닿는 모든 용품)",
        "keywords": ["텀블러", "식기", "도시락", "수저", "도마", "냄비", "프라이팬", "머그컵", "보온병", "와인잔", "실리콘조리", "거름망"],
        "cert_name": "식약처 식품용 기구 및 용기·포장 수입신고필증 (한글표시사항)",
        "check_point": "1) 해외직구/중국산 도매 상품을 식약처 정밀검역(식품용 기구 표시) 없이 팔면 식품위생법 위반입니다!\n2) 도매처에 '식약처 정식 수입신고 완료 제품'인지 꼭 확인하세요.",
        "risk_level": "🔴 최고 위험 (식약처 사이버조사단 상시 모니터링 대상)",
    },
    {
        "category": "🧪 방향제·탈취제·세정제·초·습기제거제 (생활화학제품)",
        "keywords": ["방향제", "디퓨저", "캔들", "탈취제", "세정제", "제습제", "물티슈", "모기퇴치", "기피제", "얼룩제거", "코팅제"],
        "cert_name": "환경부 안전확인대상생활화학제품 신고번호 (초록누리 조회)",
        "check_point": "1) 환경부 '초록누리(ecolife.me.go.kr)'에서 신고번호(예: 제HB21-...)를 반드시 스마트스토어 속성창에 입력해야 등록됩니다.",
        "risk_level": "🟠 주의 위험 (신고번호 누락 시 AI 모니터링 자동 판매중지)",
    },
    {
        "category": "⛺ 일반 캠핑가구·수납함·인테리어 소품·성인 잡화",
        "keywords": ["테이블", "의자", "파우치", "수납함", "가방", "지갑", "방석", "매트", "정리함", "우산", "양산"],
        "cert_name": "별도 KC 안전인증 비대상 (단, 품질경영촉진법상 한글표시사항 준수)",
        "check_point": "1) 전기/배터리가 없고 성인용인 일반 가구·잡화는 비교적 안전하게 소싱 가능합니다.\n2) 단, '피부 접촉 섬유류(잠옷, 양말, 담요)'는 가정용 섬유제품 KC(공급자적합성) 표기 여부를 확인하세요.",
        "risk_level": "🟢 안전 소싱군 (초보 위탁판매자 강력 추천 카테고리)",
    },
]

ISLAND_KEYWORDS = ["제주", "서귀포", "울릉", "백령", "연평", "대청", "덕적", "자월", "영흥", "완도", "진도", "신안", "흑산", "비금", "도초", "임자", "자은", "암태", "안좌", "팔금", "추자", "우도", "거문", "욕지", "사량", "조도", "선유", "어청", "위도"]


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
                "누적판매수량": 2,
                "광고및기타지출": 18000,
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
    df["배송비_num"] = clean_num(df.get("배송비"), 3000)
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

    with st.sidebar:
        st.markdown("## 🛒 위탁판매 컨트롤 타워")
        st.caption(f"📅 오늘: {today.strftime('%Y-%m-%d')} (총 27대 기능 탑재)")
        st.markdown("---")

        main_menu = st.radio(
            "📂 작업할 워크스페이스를 선택하세요",
            [
                "📅 1. 소싱 캘린더 & KC인증 판독",
                "🚨 2. 품절·성적표·좀비상품 진단",
                "📦 3. 발주·도서산간·송장·CS·리뷰",
                "🎨 4. 마케팅·Top3기획전·후킹·UTM",
                "💰 5. 수익장부·등급진단·세트·세금",
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

    st.title("🛒 스마트스토어 위탁판매 & 블로그 올인원 ERP (27대 기능 완전체)")
    golden_events = [e for e in upcoming_list if e["d_day"] <= 38]
    if golden_events:
        ge = golden_events[0]
        st.warning(
            f"🔔 **[자동 소싱 레이더] D-{ge['d_day']} {ge['name']} ({ge['event_date'].strftime('%m월 %d일')})** — "
            f"{ge['action_status']} | **추천 품목:** {ge['items']}"
        )

    # ==================================================================================
    # MENU 1: 📅 소싱 캘린더 & KC인증 판독
    # ==================================================================================
    if main_menu == "📅 1. 소싱 캘린더 & KC인증 판독":
        sub_s1, sub_s2 = st.tabs([
            "📅 1. 연간 기념일 소싱 로드맵 & 월별 달력 (3~4주 전 알림)",
            "🛡️ 2. KC인증·전파인증·식약처 필수 대상 품목 판독기",
        ])

        with sub_s1:
            st.subheader("📅 연간 기념일 소싱 로드맵 & 월별 달력")
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
                <!DOCTYPE html><html><head><meta charset="utf-8">
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
                </style></head>
                <body>
                    <table class="cal-table">
                        <thead><tr><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th style="color:#93c5fd;">토</th><th style="color:#fca5a5;">일</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </body></html>
                """
                components.html(calendar_component_html, height=65 + (len(cal_matrix) * 64), scrolling=False)
                st.caption("🟥 빨간칸: 해당 월 기념일 당일 | 🟨 노란칸: 다음 대목 3~4주 전 소싱 시작일 | 🟩 초록칸: 오늘")

                if prep_alerts_in_month:
                    st.markdown(f"##### 🚨 {sel_month}월에 미리 소싱 시작해야 할 항목 (3~4주 전 알림)")
                    for p_day, p_name, p_date_str, p_items in prep_alerts_in_month:
                        st.warning(f"**{sel_month}월 {p_day}일경 준비 시작** ➡️ **{p_name} ({p_date_str}) 대비**\n\n- **추천 소싱 품목:** {p_items}")

            with col_cal_right:
                st.markdown("#### 📋 다가오는 시즌/기념일 전체 스케줄 (D-Day 순)")
                schedule_rows = [{
                    "D-Day": f"D-{ev['d_day']}",
                    "기념일 날짜": ev["event_date"].strftime("%Y-%m-%d"),
                    "시즌 / 기념일명": ev["name"],
                    "권장 소싱 기간 (3~4주 전)": ev["prep_window"],
                    "현재 액션 상태": ev["action_status"],
                    "추천 소싱 상품군": ev["items"],
                    "블로그 추천 키워드": ev["keywords"],
                } for ev in upcoming_list]
                st.dataframe(pd.DataFrame(schedule_rows), use_container_width=True, hide_index=True, height=560)

        with sub_s2:
            st.subheader("🛡️ 소싱 전 필수! KC인증·전파인증·식약처 대상 품목 자동 판독기")
            kc_input = st.text_input(
                "🔍 소싱하려는 상품명 또는 품목 키워드를 입력하세요",
                value="충전식 손난로 보조배터리 / 어린이 크리스마스 장난감 / 캠핑 우드 테이블",
            )

            matched_rules = []
            for rule in KC_CERT_RULES:
                hit_kws = [kw for kw in rule["keywords"] if kw in kc_input.lower()]
                if hit_kws:
                    matched_rules.append((rule, hit_kws))

            if matched_rules:
                for rule, hits in matched_rules:
                    if "🔴" in rule["risk_level"]:
                        st.error(f"**{rule['risk_level']} | {rule['category']}** (감지 단어: `{', '.join(hits)}`)\n\n- **필수 확인 인증:** `{rule['cert_name']}`\n- **소싱 체크리스트:**\n{rule['check_point']}")
                    elif "🟠" in rule["risk_level"]:
                        st.warning(f"**{rule['risk_level']} | {rule['category']}** (감지 단어: `{', '.join(hits)}`)\n\n- **필수 확인 인증:** `{rule['cert_name']}`\n- **소싱 체크리스트:**\n{rule['check_point']}")
                    else:
                        st.success(f"**{rule['risk_level']} | {rule['category']}** (감지 단어: `{', '.join(hits)}`)\n\n- **인증 안내:** `{rule['cert_name']}`\n- **소싱 체크리스트:**\n{rule['check_point']}")
            else:
                st.info("🟢 특별 위험 키워드가 감지되지 않았습니다. 아래 5대 카테고리별 필수 인증 기준표를 참고해 안전하게 소싱하세요.")

            st.dataframe(
                pd.DataFrame([{
                    "위험도": r["risk_level"], "품목 카테고리": r["category"],
                    "필수 인증 명칭": r["cert_name"], "주요 해당 키워드": ", ".join(r["keywords"][:8]),
                } for r in KC_CERT_RULES]),
                use_container_width=True, hide_index=True
            )

    # ==================================================================================
    # MENU 2: 🚨 품절·성적표·좀비상품 진단 (품절스캔 + 블로그역추적 + 경쟁사비교 + 도매처성적표 + 좀비상품처방전)
    # ==================================================================================
    elif main_menu == "🚨 2. 품절·성적표·좀비상품 진단":
        sub_m1, sub_m2, sub_m3, sub_m4, sub_m5 = st.tabs([
            "🔍 1. 도매처 품절·단종·가격인상 스캔",
            "📝 2. 블로그·카페 죽은 홍보링크 역추적",
            "⚔️ 3. 경쟁사 스토어 최저가 비교·감시",
            "🏆 4. 도매처(공급사)별 수익성·안정성 성적표",
            "🧟 5. 좀비 상품(판매부진·적자) 자동 진단 & 리뉴얼 처방전",
        ])

        with sub_m1:
            st.subheader("🔍 등록 상품 도매처 품절·단종 & 기습 가격 인상 일괄 스캔")
            if st.button("🚀 전체 상품 도매처 품절 & 가격 변동 실시간 스캔 실행", type="primary", use_container_width=True):
                results, dead_blog_posts = [], []
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
                        "No": idx + 1, "상태": status_badge, "상품명": p_name, "도매처": w_name,
                        "시트도매원가": f"{w_price:,}원", "스토어판매가": f"{s_price:,}원",
                        "개당순마진": f"{unit_net:,}원 ({unit_margin_pct:.1f}%)",
                        "점검 결과 상세": detail_msg, "도매처 링크": w_url, "내 스토어": s_url, "블로그/카페": b_url,
                    })
                    if "🔴" in status_badge or "🟠" in status_badge:
                        dead_blog_posts.append({
                            "위험 상태": status_badge, "문제가 발생한 상품명": p_name, "점검 내용": detail_msg,
                            "수정해야 할 블로그/카페 게시글": b_url, "내 스마트스토어 링크": s_url,
                        })
                    progress_bar.progress((idx + 1) / total_items, text=f"[{idx+1}/{total_items}] {p_name} 점검 완료")

                st.session_state["last_scan_results"] = results
                st.session_state["dead_blog_posts"] = dead_blog_posts

            if "last_scan_results" in st.session_state:
                results = st.session_state["last_scan_results"]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🟢 정상 판매 가능", f"{sum(1 for r in results if '🟢' in r['상태'])}건")
                m2.metric("🔴 품절/단종 위험", f"{sum(1 for r in results if '🔴' in r['상태'])}건")
                m3.metric("🟠 가격인상/역마진 주의", f"{sum(1 for r in results if '🟠' in r['상태'])}건")
                m4.metric("🟡 수동 확인 필요", f"{sum(1 for r in results if '🟡' in r['상태'])}건")

                st.dataframe(
                    pd.DataFrame(results), use_container_width=True, hide_index=True,
                    column_config={
                        "도매처 링크": st.column_config.LinkColumn("도매처", display_text="🔗 도매처 열기"),
                        "내 스토어": st.column_config.LinkColumn("스마트스토어", display_text="🏪 스토어 열기"),
                        "블로그/카페": st.column_config.LinkColumn("홍보글", display_text="📝 홍보글 열기"),
                    },
                )

        with sub_m2:
            st.subheader("📝 블로그·카페 홍보글 '죽은 링크 / 품절 상품' 역추적기")
            if "dead_blog_posts" in st.session_state and st.session_state["dead_blog_posts"]:
                st.error("🚨 **방금 품절/가격인상 스캔에서 감지된 '즉시 링크 교체 필요' 블로그·카페 게시글 목록입니다!**")
                st.dataframe(pd.DataFrame(st.session_state["dead_blog_posts"]), use_container_width=True, hide_index=True)

            blog_audit_rows = []
            for idx, row in df.iterrows():
                p_name = str(row.get("상품명", f"상품 {idx+1}"))
                b_url = str(row.get("블로그홍보링크", "")).strip()
                s_url = str(row.get("스마트스토어링크", "")).strip()
                w_url = str(row.get("도매처링크", "")).strip()
                post_status = "⚪ 홍보글 미등록" if not b_url or b_url in ("nan", "None", "https://blog.naver.com/", "https://cafe.naver.com/") else "🟢 홍보링크 연결됨"
                blog_audit_rows.append({
                    "No": idx + 1, "상품명": p_name, "홍보글 상태": post_status,
                    "블로그/카페 게시글 바로가기": b_url if b_url.startswith("http") else "",
                    "연결된 스마트스토어": s_url if s_url.startswith("http") else "",
                    "원본 도매처": w_url if w_url.startswith("http") else "",
                })
            st.dataframe(pd.DataFrame(blog_audit_rows), use_container_width=True, hide_index=True)

        with sub_m3:
            st.subheader("⚔️ 경쟁사(타 판매자) 최저가 비교 & 마진 방어 시뮬레이터")
            comp_sel = st.selectbox("비교할 내 스토어 상품 선택", product_list, key="comp_prod_sel")
            if comp_sel != "➕ [직접 수동 입력 / 신규 상품 작성]":
                c_idx = int(comp_sel.split(" | ")[0])
                c_row = df.iloc[c_idx]
                my_w_p, my_s_p = int(c_row.get("도매원가_num", 15000)), int(c_row.get("판매가_num", 25000))
            else:
                my_w_p, my_s_p = 15000, 25000

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
                    st.success(f"💡 **최저가 방어 가능! ({match_price:,}원 세팅 시)**\n\n개당 **{profit_at_match:,}원 (마진 {margin_at_match:.1f}%)** 남음!")
                else:
                    st.error(f"🚨 **출혈 경쟁 주의! ({match_price:,}원 세팅 시)**\n\n순수익 **{profit_at_match:,}원 ({margin_at_match:.1f}%)**. 가격 대신 인포그래픽/사은품으로 승부하세요!")

            if comp_url_input and st.button("🔍 경쟁사 URL 가격 자동 추출 시도", use_container_width=True):
                c_badge, c_ext_p, c_msg = scan_competitor_page(comp_url_input, my_curr_price)
                st.info(f"**{c_badge}** | 추출 가격: {c_ext_p:,}원 | {c_msg}")

        with sub_m4:
            st.subheader("🏆 도매처(공급사)별 수익 기여도 & 안정성 성적표")
            vendor_stats = {}
            for idx, row in df.iterrows():
                v_name = str(row.get("도매처명", "기타")).strip() or "기타"
                w_p = int(row.get("도매원가_num", 0))
                s_p = int(row.get("판매가_num", 0))
                qty = int(row.get("누적판매수량_num", 0))
                ad_c = int(row.get("광고및기타지출_num", 0))
                fee = int(round(s_p * 0.056))
                net_p = (s_p - w_p - fee) * qty - ad_c
                rev = s_p * qty

                if v_name not in vendor_stats:
                    vendor_stats[v_name] = {"items": 0, "qty": 0, "rev": 0, "profit": 0}
                vendor_stats[v_name]["items"] += 1
                vendor_stats[v_name]["qty"] += qty
                vendor_stats[v_name]["rev"] += rev
                vendor_stats[v_name]["profit"] += net_p

            vendor_rows = []
            for v_name, st_d in vendor_stats.items():
                avg_roi = (st_d["profit"] / st_d["rev"] * 100) if st_d["rev"] > 0 else 0.0
                if avg_roi >= 30 and st_d["profit"] >= 100000:
                    grade = "👑 S등급 (주력 소싱처)"
                elif avg_roi >= 20:
                    grade = "🟢 A등급 (우수 공급처)"
                elif avg_roi >= 10:
                    grade = "🟡 B등급 (마진 개선 필요)"
                else:
                    grade = "🔴 C등급 (교체 검토)"

                vendor_rows.append({
                    "도매처명": v_name, "종합 평가 등급": grade, "등록 상품 수": f"{st_d['items']}종",
                    "총 판매수량": f"{st_d['qty']:,}개", "총 매출액": f"{st_d['rev']:,}원",
                    "누적 순수익 기여": f"{st_d['profit']:,}원", "평균 순마진율": f"{avg_roi:.1f}%",
                })
            st.dataframe(pd.DataFrame(vendor_rows), use_container_width=True, hide_index=True)

        with sub_m5:
            st.subheader("🧟 좀비 상품(판매 부진 · 광고비 적자) 자동 진단 & 리뉴얼 처방전")
            st.write(
                "스마트스토어에 등록된 상품 중 **판매량이 저조하거나 광고비 대비 적자가 나는 좀비 상품**을 방치하면 스토어 전체의 노출 지수가 하락합니다. "
                "상품별 상태에 따른 **맞춤형 회생 처방전**을 확인하세요."
            )

            zombie_rows = []
            for idx, row in df.iterrows():
                p_name = str(row.get("상품명", f"상품 {idx+1}"))
                w_p = int(row.get("도매원가_num", 0))
                s_p = int(row.get("판매가_num", 0))
                qty = int(row.get("누적판매수량_num", 0))
                ad_c = int(row.get("광고및기타지출_num", 0))
                fee = int(round(s_p * 0.056))
                unit_m = s_p - w_p - fee
                net_p = (unit_m * qty) - ad_c

                if net_p < 0:
                    z_status = "🔴 적자 좀비 (즉시 수술 필요)"
                    rx = "1) 유료 검색광고 즉시 중단! 2) 4번 메뉴에서 '세부 키워드'로 상품명 변경 후 블로그 후기 유입으로 전환"
                elif qty <= 5:
                    z_status = "🟠 판매 부진 (노출 리뉴얼 요망)"
                    rx = "1) 기존 상품 삭제 후 '신상품 버프'를 받기 위해 썸네일 배지 합성 + 새 상품명으로 재등록 권장"
                elif unit_m < 3000:
                    z_status = "🟡 박리다매형 (객단가 상승 필요)"
                    rx = "1) 5번 메뉴의 '1+1 세트/무료배송 설계기'를 활용해 2개 묶음 옵션 추가로 객단가 2배 인상 권장"
                else:
                    z_status = "🟢 건강 효자 상품 (유지·확장)"
                    rx = "1) 품절 방어 최우선! 2) 블로그/카페에 '실구매 베스트 리뷰 모음 인포그래픽' 추가 발행으로 1위 굳히기"

                zombie_rows.append({
                    "진단 등급": z_status,
                    "상품명": p_name,
                    "누적 판매량": f"{qty}개",
                    "개당 순마진": f"{unit_m:,}원",
                    "누적 순수익": f"{net_p:,}원",
                    "맞춤 리뉴얼 처방전 (Action Plan)": rx,
                })
            st.dataframe(pd.DataFrame(zombie_rows), use_container_width=True, hide_index=True)

    # ==================================================================================
    # MENU 3: 📦 발주·도서산간·송장·CS·리뷰
    # ==================================================================================
    elif main_menu == "📦 3. 발주·도서산간·송장·CS·리뷰":
        sub_o1, sub_o2, sub_o3, sub_o4, sub_o5 = st.tabs([
            "📦 1. 주문서 ➡️ 도매처 발주 변환 (+도서산간·진상 경보)",
            "🚚 2. 도매처 송장 ➡️ 스토어 일괄 발송 변환",
            "🛡️ 3. 상습 반품·진상 고객 요주의 DB",
            "💬 4. 고객 CS 답변 1초 복사함",
            "⭐ 5. 스마트스토어 리뷰 답글(사장님 댓글) 생성기",
        ])

        if "blacklist_keywords" not in st.session_state:
            st.session_state["blacklist_keywords"] = "010-0000-0000, 상습파손클레임, 허위반품요구"

        with sub_o1:
            st.subheader("📦 스마트스토어 주문서 ➡️ 도매처 발주 엑셀 변환 (+🏝️제주·도서산간 추가운임 & 진상고객 자동 감지)")
            uploaded_order_file = st.file_uploader(
                "📂 스마트스토어 주문내역 파일 업로드 (.csv 또는 .xlsx 지원 - 미업로드 시 제주도 포함 샘플 3건으로 즉시 테스트)",
                type=["csv", "xlsx"], key="ord_up"
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
                except Exception:
                    raw_orders = pd.DataFrame()
            else:
                raw_orders = pd.DataFrame([
                    {
                        "상품주문번호": "202611120001", "상품명": "캠핑용 초경량 감성 우드 롤테이블",
                        "옵션정보": "컬러: 내추럴우드", "수량": 1, "수취인명": "김민수",
                        "수취인연락처1": "010-1234-5678", "우편번호": "13529",
                        "배송지": "경기도 성남시 분당구 판교역로 166 101동 202호", "배송메세지": "문 앞에 놓아주세요.",
                    },
                    {
                        "상품주문번호": "202611120002", "상품명": "충전식 손난로 보조배터리 10000mAh",
                        "옵션정보": "컬러: 크림화이트", "수량": 2, "수취인명": "이서연",
                        "수취인연락처1": "010-9876-5432", "우편번호": "06236",
                        "배송지": "서울특별시 강남구 테헤란로 152 3층", "배송메세지": "경비실에 맡겨주세요.",
                    },
                    {
                        "상품주문번호": "202611120003", "상품명": "크리스마스 미니 트리 LED 풀세트",
                        "옵션정보": "기본형 풀세트", "수량": 1, "수취인명": "박제주",
                        "수취인연락처1": "010-5555-7777", "우편번호": "63000",
                        "배송지": "제주특별자치도 제주시 첨단로 242", "배송메세지": "선물용이니 안전배송 부탁드려요.",
                    },
                ])

            if not raw_orders.empty:
                def pick_col(df_in, candidates, default_val=""):
                    for c in candidates:
                        if c in df_in.columns:
                            return df_in[c].fillna(default_val).astype(str)
                    return pd.Series([default_val] * len(df_in))

                sheet_map = {
                    str(s_r.get("상품명", "")).strip(): (
                        str(s_r.get("도매처명", "-")), str(s_r.get("도매처링크", "")), int(s_r.get("도매원가_num", 0))
                    ) for _, s_r in df.iterrows()
                }
                bl_tokens = [k.strip() for k in st.session_state["blacklist_keywords"].split(",") if k.strip()]

                ord_nos = pick_col(raw_orders, ["상품주문번호", "주문번호"], "0000")
                p_names = pick_col(raw_orders, ["상품명", "주문상품명", "품목명"])
                opts = pick_col(raw_orders, ["옵션정보", "옵션", "선택사항"], "단품")
                qtys = pick_col(raw_orders, ["수량", "주문수량", "구매수량"], "1")
                recs = pick_col(raw_orders, ["수취인명", "받는분", "수령인"])
                phones = pick_col(raw_orders, ["수취인연락처1", "수취인연락처", "전화번호", "핸드폰"])
                zips = pick_col(raw_orders, ["우편번호", "우편번호(5자리)"], "00000")
                addrs = pick_col(raw_orders, ["배송지", "통합배송지", "주소", "수취인주소"])
                memos = pick_col(raw_orders, ["배송메세지", "배송메모", "요청사항"], "안전배송 부탁드립니다.")

                converted_rows = []
                island_alert_cnt = 0
                for i in range(len(raw_orders)):
                    pn = p_names.iloc[i].strip()
                    addr_str = addrs.iloc[i]
                    zip_str = zips.iloc[i].strip()
                    w_vendor, w_link, w_cost = sheet_map.get(pn, ("직접확인", "", 0))
                    row_concat = f"{recs.iloc[i]} {phones.iloc[i]} {addr_str}"

                    risk_flag = "🚨 요주의 고객 확인!" if any(bt in row_concat for bt in bl_tokens) else "🟢 정상"
                    is_island = any(ik in addr_str for ik in ISLAND_KEYWORDS) or zip_str.startswith("63") or zip_str.startswith("402")
                    if is_island:
                        island_alert_cnt += 1
                        ship_zone = "🏝️ 도서산간/제주 (추가운임 3~5천원 확인!)"
                    else:
                        ship_zone = "🚚 일반지역"

                    converted_rows.append({
                        "배송권역(운임경보)": ship_zone,
                        "고객검증": risk_flag, "상품주문번호": ord_nos.iloc[i], "매칭도매처": w_vendor,
                        "받는사람(수취인)": recs.iloc[i], "휴대폰번호": phones.iloc[i], "우편번호": zip_str,
                        "배송지주소": addr_str, "주문상품명": pn, "옵션명": opts.iloc[i],
                        "발주수량": qtys.iloc[i], "배송메모": memos.iloc[i], "도매처상품링크": w_link,
                    })

                if island_alert_cnt > 0:
                    st.warning(
                        f"🏝️ **[제주·도서산간 주문 {island_alert_cnt}건 감지됨!]** "
                        "도매처 발주 시 추가 배송비(3,000~5,000원)가 청구되어 역마진이 날 수 있으니, 고객이 추가배송비를 결제했는지 반드시 확인하세요!"
                    )

                df_conv = pd.DataFrame(converted_rows)
                st.dataframe(df_conv, use_container_width=True, hide_index=True)

                dl_c1, dl_c2 = st.columns(2)
                with dl_c1:
                    dome_csv = df_conv[["받는사람(수취인)", "휴대폰번호", "우편번호", "배송지주소", "주문상품명", "옵션명", "발주수량", "배송메모"]].to_csv(index=False).encode("utf-8-sig")
                    st.download_button("📥 [도매꾹/도매매 규격] 대량 발주서 CSV 다운로드", data=dome_csv, file_name=f"도매매_발주서_{today.strftime('%Y%m%d')}.csv", mime="text/csv", type="primary", use_container_width=True)
                with dl_c2:
                    owner_csv = df_conv[["상품주문번호", "주문상품명", "옵션명", "발주수량", "받는사람(수취인)", "휴대폰번호", "우편번호", "배송지주소", "배송메모"]].to_csv(index=False).encode("utf-8-sig")
                    st.download_button("📥 [오너클랜/일반도매 규격] 발주서 CSV 다운로드", data=owner_csv, file_name=f"오너클랜_발주서_{today.strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

        with sub_o2:
            st.subheader("🚚 도매처 출고 송장번호 ➡️ 스마트스토어 일괄 발송처리 엑셀(CSV) 변환기")
            up_inv = st.file_uploader("📂 도매처 송장 파일 업로드 (.csv / .xlsx - 미업로드 시 샘플 데이터로 즉시 테스트)", type=["csv", "xlsx"], key="inv_up")
            if up_inv is not None:
                try:
                    df_inv_raw = pd.read_csv(up_inv) if up_inv.name.endswith(".csv") else pd.read_excel(up_inv)
                except Exception:
                    df_inv_raw = pd.DataFrame()
            else:
                df_inv_raw = pd.DataFrame([
                    {"상품주문번호": "202611120001", "수취인명": "김민수", "택배사": "CJ대한통운", "운송장번호": "6543-1234-9876"},
                    {"상품주문번호": "202611120002", "수취인명": "이서연", "택배사": "한진택배", "운송장번호": "4123-8765-0012"},
                ])

            if not df_inv_raw.empty:
                naver_dispatch_rows = []
                for idx_i, r_i in df_inv_raw.iterrows():
                    ord_no = str(r_i.get("상품주문번호", r_i.get("주문번호", f"20261112000{idx_i+1}")))
                    courier = str(r_i.get("택배사", r_i.get("배송업체", "CJ대한통운")))
                    track_no = re.sub(r"[^0-9]", "", str(r_i.get("운송장번호", r_i.get("송장번호", ""))))
                    naver_dispatch_rows.append({
                        "상품주문번호": ord_no, "배송방법": "택배,등기,소포", "택배사": courier,
                        "송장번호": track_no, "수취인명(확인용)": str(r_i.get("수취인명", r_i.get("받는사람", "-"))),
                    })
                df_dispatch = pd.DataFrame(naver_dispatch_rows)
                st.dataframe(df_dispatch, use_container_width=True, hide_index=True)

                dispatch_csv = df_dispatch[["상품주문번호", "배송방법", "택배사", "송장번호"]].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "🚀 [네이버 스마트스토어 일괄 발송처리용] 송장 파일 다운로드",
                    data=dispatch_csv, file_name=f"스마트스토어_일괄발송_{today.strftime('%Y%m%d')}.csv",
                    mime="text/csv", type="primary", use_container_width=True
                )

        with sub_o3:
            st.subheader("🛡️ 상습 반품·부당 클레임 요주의 고객(블랙컨슈머) 필터 DB")
            st.session_state["blacklist_keywords"] = st.text_area(
                "요주의 연락처 / 수취인명 / 주소 키워드 목록 (쉼표로 구분하여 입력)",
                value=st.session_state["blacklist_keywords"], height=120
            )
            st.info("💡 여기에 등록된 번호나 단어는 1번 탭에서 주문서를 올릴 때 실시간으로 대조되어 발주 전 사전 확인이 가능합니다.")

        with sub_o4:
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
            msg_soldout = f"안녕하세요, {cs_cust_name} 고객님! 주문해주신 [{cs_prod_name}] 출고 검수 중 공급처의 갑작스러운 재고 소진 및 마지막 잔여 수량 불량이 확인되어 부득이하게 정상 발송이 어려운 상황입니다. 결제 금액이 묶이지 않도록 우선 취소 처리를 도와드리고자 하며, 불편을 드려 진심으로 죄송합니다."
            msg_delay = f"안녕하세요, {cs_cust_name} 고객님! 주문해주신 [{cs_prod_name}] 주문량 급증으로 공급처 검수 작업이 하루 정도 지연되어 [{cs_delay_date}] 최우선 출고될 예정입니다. 송장 번호가 나오는 대로 즉시 입력해 드리겠습니다. 감사합니다!"
            msg_return = f"안녕하세요, {cs_cust_name} 고객님! [{cs_prod_name}] 단순 변심 반품의 경우 수령 후 7일 이내 미개봉 상태에 한해 가능하며 왕복 택배비 [{cs_return_fee}]이 발생합니다. 스마트스토어 반품요청을 접수해 주시면 기사님이 방문 수거합니다."
            msg_review = f"안녕하세요, {cs_cust_name} 고객님! 주문하신 [{cs_prod_name}]은 잘 받아보셨나요? 상품이 마음에 드셨다면 잠깐 시간 내어 [구매확정]과 [포토리뷰]를 남겨주시면 스토어 운영에 큰 힘이 됩니다. 감사합니다! 😊"

            with cs_grid1:
                render_copy_box("🚨 1. 도매처 품절/단종 양해 안내", msg_soldout, "cs1", "#dc2626", 220)
                render_copy_box("📦 3. 단순변심 반품 절차 & 배송비 안내", msg_return, "cs3", "#475569", 220)
            with cs_grid2:
                render_copy_box("⏳ 2. 도매처 출고/배송 지연 양해 안내", msg_delay, "cs2", "#d97706", 220)
                render_copy_box("⭐ 4. 배송 완료 후 구매확정 & 리뷰 유도", msg_review, "cs4", "#03c75a", 220)

        with sub_o5:
            st.subheader("⭐ 스마트스토어 고객 리뷰 1:1 맞춤 답글(사장님 댓글) 생성기")
            rv_c1, rv_c2 = st.columns([1.0, 1.3], gap="large")
            with rv_c1:
                rv_prod = st.text_input("리뷰 달린 상품명", value="캠핑용 초경량 감성 우드 롤테이블")
                rv_point = st.text_input("칭찬/언급된 포인트", value="빠른 배송과 튼튼한 마감")
                rv_benefit = st.text_input("재구매 유도 혜택 안내", value="스토어 찜 & 소식받기 1,000원 할인 쿠폰")

            with rv_c2:
                reply_5star = f"안녕하세요 고객님! 바쁘신 와중에도 정성스러운 별점 5점 리뷰를 남겨주셔서 진심으로 감사드립니다 😊\n구매하신 [{rv_prod}]의 '{rv_point}' 부분에 만족하셨다니 준비한 보람이 느껴져 정말 기쁩니다!\n다음 방문 시 [{rv_benefit}]도 꼭 챙겨서 알뜰하게 이용해 보세요! 늘 행복하세요 💚"
                reply_3star = f"안녕하세요 고객님! 소중한 시간을 내어 솔직한 사용 후기를 남겨주셔서 감사드립니다.\n[{rv_prod}] 사용 중 말씀해주신 소중한 의견은 공급처 및 검수팀과 즉시 공유하여 한층 더 만족스러운 품질로 개선하겠습니다!\n추가로 불편하신 점이 있다면 언제든 네이버 톡톡으로 말씀해 주세요. 감사합니다!"
                reply_1star = f"안녕하세요 고객님, 먼저 기대하고 주문해주신 [{rv_prod}] 상품으로 인해 불편과 실망을 드려 고개 숙여 사과드립니다.\n번거로우시겠지만 네이버 톡톡으로 연락 주시면 판매자 100% 부담으로 **즉시 새 상품 맞교환 또는 전액 환불**을 가장 빠르게 처리해 드리겠습니다. 다시 한번 죄송합니다."
                render_copy_box("😍 1. [별점 5점 극찬 리뷰용] 재구매 & 단골 유도 감사 답글", reply_5star, "rv5", "#03c75a", 190)
                render_copy_box("🙂 2. [별점 3~4점 아쉬움 리뷰용] 피드백 수용 & 신뢰도 상승 답글", reply_3star, "rv3", "#2563eb", 190)
                render_copy_box("🙇‍♂️ 3. [별점 1~2점 불만/불량 리뷰용] 다른 예비 구매자를 안심시키는 사과 답글", reply_1star, "rv1", "#dc2626", 195)
                # ==================================================================================
    # MENU 4: 🎨 마케팅·Top3기획전·후킹·UTM (5종인포 + Top3큐레이션 + 3초후킹브릿지 + 썸네일 + 공지배너 + SEO/지재권 + UTM)
    # ==================================================================================
    elif main_menu == "🎨 4. 마케팅·Top3기획전·후킹·UTM":
        sub_mk1, sub_mk_top3, sub_mk_hook, sub_mk2, sub_mk3, sub_mk4, sub_mk5 = st.tabs([
            "🎨 1. 5종 단품 인포그래픽",
            "🏆 2. Top 3 묶음 기획전 카드",
            "⚡ 3. 상세페이지 3초 후킹 브릿지",
            "🖼️ 4. 썸네일(1000x1000) 합성",
            "📢 5. 상세 상·하단 공지 배너",
            "🚀 6. SEO 상품명·원고·금지어",
            "🔗 7. 블로그·카페 UTM 추적링크",
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

                img_url = st.text_input("🖼️ 상품 이미지 URL (선택사항)", value="", placeholder="https://...")

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

            img_block = f'<tr><td colspan="2" align="center" style="padding:16px 24px 6px 24px;background:#fff;"><img src="{img_url.strip()}" crossorigin="anonymous" style="max-width:100%;max-height:300px;border-radius:10px;border:1px solid #e5e7eb;" /></td></tr>' if img_url.strip() else ""
            discount_badge_html = f'<span style="font-size:26px;font-weight:900;color:#e11d48;margin-right:10px;">{disc_rate}% ↓</span>' if disc_rate > 0 else ""

            price_box_html = f"""
            <tr><td colspan="2" style="padding:14px 24px;background:#ffffff;">
                <table width="100%" style="border-collapse:collapse;background:{sub_bg};border-radius:10px;border:1px solid {main_color}33;" bgcolor="{sub_bg}">
                    <tr>
                        <td style="padding:15px 20px;width:65%;">
                            <div style="font-size:13px;color:#777;text-decoration:line-through;">정상가 {orig_price:,}원</div>
                            <div style="margin-top:4px;">{discount_badge_html}<span style="font-size:26px;font-weight:900;color:#111;">{s_price:,}원</span></div>
                        </td>
                        <td align="right" style="padding:15px 20px;width:35%;">
                            <span style="background:{main_color};color:#fff;padding:8px 14px;border-radius:8px;font-size:14px;font-weight:800;display:inline-block;">🚚 {ship_info}</span>
                        </td>
                    </tr>
                </table>
            </td></tr>
            """

            if "①" in template_type:
                body_section_html = f"""
                {price_box_html}
                <tr><td colspan="2" style="padding:4px 24px 16px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;">
                        <tr bgcolor="#f8fafc"><td style="padding:11px 16px;font-size:14px;font-weight:800;color:#1e293b;border-bottom:1px solid #e5e7eb;">📌 핵심 체크포인트 TOP 3</td></tr>
                        <tr><td style="padding:16px;font-size:14.5px;color:#222;line-height:1.85;background:#fff;">
                            <div>✅ <b>POINT 1.</b> {feat1}</div><div>✅ <b>POINT 2.</b> {feat2}</div><div>✅ <b>POINT 3.</b> {feat3}</div>
                        </td></tr>
                    </table>
                </td></tr>
                <tr><td colspan="2" style="padding:0 24px 18px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;border:1px solid #e5e7eb;font-size:13px;">
                        <tr><td width="28%" bgcolor="#f8fafc" style="padding:10px 12px;font-weight:bold;color:#475569;border-bottom:1px solid #e5e7eb;border-right:1px solid #e5e7eb;">{spec_label1}</td><td width="72%" style="padding:10px 12px;color:#1e293b;border-bottom:1px solid #e5e7eb;">{spec_val1}</td></tr>
                        <tr><td width="28%" bgcolor="#f8fafc" style="padding:10px 12px;font-weight:bold;color:#475569;border-right:1px solid #e5e7eb;">{spec_label2}</td><td width="72%" style="padding:10px 12px;color:#1e293b;">{spec_val2}</td></tr>
                    </table>
                </td></tr>
                """
            elif "②" in template_type:
                body_section_html = f"""
                {price_box_html}
                <tr><td colspan="2" style="padding:4px 24px 20px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;border:2px solid #cbd5e1;font-size:13.5px;text-align:center;">
                        <tr bgcolor="#1e293b" style="color:#fff;font-weight:800;">
                            <td width="24%" style="padding:11px 8px;border:1px solid #334155;">비교 항목</td>
                            <td width="36%" style="padding:11px 8px;border:1px solid #334155;background:#64748b;">😟 타사 일반 저가형</td>
                            <td width="40%" style="padding:11px 8px;border:1px solid #334155;background:{main_color};">🏆 우리 스토어 정품</td>
                        </tr>
                        <tr><td bgcolor="#f8fafc" style="padding:12px 8px;font-weight:bold;border:1px solid #cbd5e1;">{comp_criteria1}</td><td style="padding:12px 10px;color:#64748b;border:1px solid #cbd5e1;">❌ {comp_bad1}</td><td bgcolor="{sub_bg}" style="padding:12px 10px;color:#111;font-weight:800;border:1px solid #cbd5e1;">⭕ {comp_good1}</td></tr>
                        <tr><td bgcolor="#f8fafc" style="padding:12px 8px;font-weight:bold;border:1px solid #cbd5e1;">{comp_criteria2}</td><td style="padding:12px 10px;color:#64748b;border:1px solid #cbd5e1;">❌ {comp_bad2}</td><td bgcolor="{sub_bg}" style="padding:12px 10px;color:#111;font-weight:800;border:1px solid #cbd5e1;">⭕ {comp_good2}</td></tr>
                        <tr><td bgcolor="#f8fafc" style="padding:12px 8px;font-weight:bold;border:1px solid #cbd5e1;">{comp_criteria3}</td><td style="padding:12px 10px;color:#64748b;border:1px solid #cbd5e1;">❌ {comp_bad3}</td><td bgcolor="{sub_bg}" style="padding:12px 10px;color:#111;font-weight:800;border:1px solid #cbd5e1;">⭕ {comp_good3}</td></tr>
                    </table>
                </td></tr>
                """
            elif "③" in template_type:
                body_section_html = f"""
                {price_box_html}
                <tr><td colspan="2" style="padding:4px 24px 18px 24px;background:#fff;">
                    <div style="font-size:14px;font-weight:900;color:{main_color};margin-bottom:10px;">💬 실구매 고객님들의 100% 리얼 극찬 후기</div>
                    <table width="100%" style="border-collapse:collapse;margin-bottom:10px;background:#f8fafc;border-left:4px solid {main_color};"><tr><td style="padding:12px 16px;"><div style="font-size:12px;font-weight:bold;color:#ca8a04;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev1_user}</span></div><div style="font-size:13.5px;color:#1e293b;">"{rev1_text}"</div></td></tr></table>
                    <table width="100%" style="border-collapse:collapse;margin-bottom:10px;background:#f8fafc;border-left:4px solid {main_color};"><tr><td style="padding:12px 16px;"><div style="font-size:12px;font-weight:bold;color:#ca8a04;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev2_user}</span></div><div style="font-size:13.5px;color:#1e293b;">"{rev2_text}"</div></td></tr></table>
                    <table width="100%" style="border-collapse:collapse;background:#f8fafc;border-left:4px solid {main_color};"><tr><td style="padding:12px 16px;"><div style="font-size:12px;font-weight:bold;color:#ca8a04;">⭐⭐⭐⭐⭐ <span style="color:#64748b;">| {rev3_user}</span></div><div style="font-size:13.5px;color:#1e293b;">"{rev3_text}"</div></td></tr></table>
                </td></tr>
                """
            elif "④" in template_type:
                body_section_html = f"""
                {price_box_html}
                <tr><td colspan="2" style="padding:4px 24px 18px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;border:1px solid #e2e8f0;">
                        <tr bgcolor="#f1f5f9"><td style="padding:11px 16px;font-size:14px;font-weight:900;color:#0f172a;border-bottom:1px solid #e2e8f0;">🙋‍♂️ 구매 전 가장 많이 묻는 질문 Q&A</td></tr>
                        <tr><td style="padding:14px 16px;border-bottom:1px solid #f1f5f9;"><div style="font-size:14px;font-weight:800;color:{main_color};">Q1. {q1_text}</div><div style="font-size:13.5px;color:#334155;">👉 <b>A.</b> {a1_text}</div></td></tr>
                        <tr><td style="padding:14px 16px;border-bottom:1px solid #f1f5f9;"><div style="font-size:14px;font-weight:800;color:{main_color};">Q2. {q2_text}</div><div style="font-size:13.5px;color:#334155;">👉 <b>A.</b> {a2_text}</div></td></tr>
                        <tr><td style="padding:14px 16px;"><div style="font-size:14px;font-weight:800;color:{main_color};">Q3. {q3_text}</div><div style="font-size:13.5px;color:#334155;">👉 <b>A.</b> {a3_text}</div></td></tr>
                    </table>
                </td></tr>
                """
            else:
                body_section_html = f"""
                <tr><td colspan="2" style="padding:16px 24px 8px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;background:#111827;color:#fff;border-radius:10px;text-align:center;" bgcolor="#111827">
                        <tr><td style="padding:18px 16px;"><div style="font-size:18px;font-weight:900;color:#facc15;margin-bottom:6px;">{promo_headline}</div><div style="font-size:13.5px;color:#e5e7eb;">🎁 {coupon_text}</div></td></tr>
                    </table>
                </td></tr>
                {price_box_html}
                <tr><td colspan="2" style="padding:0 24px 18px 24px;background:#fff;">
                    <table width="100%" style="border-collapse:collapse;background:#fef2f2;border:1px dashed #ef4444;border-radius:8px;text-align:center;" bgcolor="#fef2f2">
                        <tr><td style="padding:12px;font-size:13.5px;font-weight:800;color:#b91c1c;">⏰ {stock_limit}</td></tr>
                    </table>
                </td></tr>
                """

            infographic_html = f"""
<table width="100%" style="max-width:620px;margin:0 auto;border-collapse:collapse;font-family:'Malgun Gothic',sans-serif;border:3px solid {main_color};background:#ffffff;border-radius:12px;overflow:hidden;">
    <tr bgcolor="{main_color}">
        <td colspan="2" style="padding:15px 22px;color:#ffffff;background:{main_color};">
            <span style="background:#ffffff;color:{main_color};padding:4px 12px;border-radius:20px;font-size:13px;font-weight:800;">{badge_text}</span>
            <span style="float:right;font-size:14px;color:#ffffff;font-weight:bold;">만족도 {rating_stars}</span>
        </td>
    </tr>
    <tr>
        <td colspan="2" style="padding:24px 24px 12px 24px;border-bottom:1px solid #eeeeee;background:#ffffff;">
            <div style="font-size:24px;font-weight:900;color:#111111;line-height:1.35;margin-bottom:8px;">{p_name}</div>
            <div style="font-size:15px;color:#555555;font-weight:600;">{p_sub}</div>
        </td>
    </tr>
    {img_block}
    {body_section_html}
    <tr>
        <td colspan="2" align="center" style="padding:6px 24px 24px 24px;background:#ffffff;">
            <a href="{s_url}" target="_blank" style="background:{main_color};color:#ffffff;padding:15px 36px;text-decoration:none;border-radius:8px;font-weight:900;font-size:16px;display:inline-block;">
                👉 네이버 스마트스토어 공식 판매처 바로가기
            </a>
        </td>
    </tr>
</table>
"""

            with preview_col:
                st.markdown("#### 👀 실시간 프리뷰 & 원클릭 추출 (복사 / PNG 저장)")
                component_html = f"""
                <!DOCTYPE html><html><head><meta charset="utf-8">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .action-bar {{ display:flex; flex-direction:column; gap:10px; margin-bottom:14px; }}
                    .big-btn {{ width:100%; padding:18px 20px; font-size:18px; font-weight:900; border-radius:10px; cursor:pointer; border:none; box-shadow:0 4px 8px rgba(0,0,0,0.12); }}
                    .btn-png {{ background:#111827; color:#ffffff; }}
                    .btn-copy {{ background:{main_color}; color:#ffffff; }}
                    #status-msg {{ text-align:center; font-weight:800; font-size:14.5px; padding:10px; border-radius:8px; margin-bottom:12px; display:none; }}
                    #capture-wrapper {{ background:#ffffff; padding:12px; border-radius:14px; display:inline-block; width:100%; box-sizing:border-box; }}
                </style></head>
                <body>
                    <div class="action-bar">
                        <button class="big-btn btn-png" onclick="downloadPNG()">📸 인포그래픽 고화질 PNG 사진으로 다운로드</button>
                        <button class="big-btn btn-copy" onclick="copyInfographic()">📋 블로그/카페 표 서식 통째로 복사하기 (Ctrl+V)</button>
                    </div>
                    <div id="status-msg"></div>
                    <div id="capture-wrapper">{infographic_html}</div>
                    <script>
                    function showMessage(text, bg, col) {{
                        const m = document.getElementById('status-msg');
                        m.innerText = text; m.style.backgroundColor = bg; m.style.color = col; m.style.display = 'block';
                        setTimeout(() => {{ m.style.display = 'none'; }}, 4500);
                    }}
                    function copyInfographic() {{
                        const area = document.getElementById('capture-wrapper');
                        const range = document.createRange(); range.selectNode(area);
                        const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
                        document.execCommand('copy'); sel.removeAllRanges();
                        showMessage('✅ 복사되었습니다! 블로그/카페 본문에 Ctrl+V 하세요.', '#dcfce7', '#166534');
                    }}
                    function downloadPNG() {{
                        const target = document.getElementById('capture-wrapper');
                        showMessage('⏳ 고화질 PNG 생성 중...', '#fef3c7', '#92400e');
                        html2canvas(target, {{ scale: 2, useCORS: true, allowTaint: true, backgroundColor: '#ffffff' }}).then(canvas => {{
                            const link = document.createElement('a');
                            link.download = '{safe_filename}_인포그래픽.png';
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                            showMessage('🎉 PNG 이미지 저장 완료!', '#dbeafe', '#1e40af');
                        }});
                    }}
                    </script>
                </body></html>
                """
                components.html(component_html, height=880, scrolling=True)

        # ------------------------------------------
        # 신규 기능: 블로그·카페 '연관 상품 Top 3 큐레이션 기획전' 카드 생성기
        # ------------------------------------------
        with sub_mk_top3:
            st.subheader("🏆 블로그·카페 '연관 상품 묶음 홍보(큐레이션 Top 3)' 기획전 카드 생성기")
            st.write("블로그 글 하나에 상품 1개만 올리는 것보다 **시즌 추천템 BEST 3를 한 장의 비교 카드로 묶어 소개**하면 클릭률과 동시 구매율이 2배 이상 높아집니다.")

            t3_edit, t3_prev = st.columns([1.05, 1.25], gap="large")
            with t3_edit:
                curation_title = st.text_input("🎉 기획전 메인 타이틀", value="🔥 올겨울 후회 없는 월동준비 필수템 BEST 3 총정리")
                curation_sub = st.text_input("💬 기획전 서브 설명", value="가성비·실용성·후기 검증 완료! 가장 인기 있는 3종만 모았습니다.")

                n_rows = len(df)
                r0 = df.iloc[0] if n_rows > 0 else {}
                r1 = df.iloc[1] if n_rows > 1 else r0
                r2 = df.iloc[2] if n_rows > 2 else r0

                st.markdown("##### 🥇 BEST 1 상품 설정")
                b1_name = st.text_input("상품 1 이름", value=str(r0.get("상품명", "충전식 손난로 보조배터리")))
                b1_price = st.number_input("상품 1 판매가", value=int(r0.get("판매가_num", 17900)), step=500)
                b1_desc = st.text_input("상품 1 한줄 매력", value="출퇴근길 주머니 속 온기! 보조배터리 겸용 가성비 1위")
                b1_url = st.text_input("상품 1 스토어 링크", value=str(r0.get("스마트스토어링크", "https://smartstore.naver.com/")))

                st.markdown("##### 🥈 BEST 2 상품 설정")
                b2_name = st.text_input("상품 2 이름", value=str(r1.get("상품명", "크리스마스 미니 트리 LED 풀세트")))
                b2_price = st.number_input("상품 2 판매가", value=int(r1.get("판매가_num", 26900)), step=500)
                b2_desc = st.text_input("상품 2 한줄 매력", value="전구+오너먼트 풀구성! 거실 분위기 1분 만에 변신")
                b2_url = st.text_input("상품 2 스토어 링크", value=str(r1.get("스마트스토어링크", "https://smartstore.naver.com/")))

                st.markdown("##### 🥉 BEST 3 상품 설정")
                b3_name = st.text_input("상품 3 이름", value=str(r2.get("상품명", "겨울 방한 가습기 대용량 무드등")))
                b3_price = st.number_input("상품 3 판매가", value=int(r2.get("판매가_num", 22500)), step=500)
                b3_desc = st.text_input("상품 3 한줄 매력", value="건조한 침실 필수템! 은은한 무드등+초음파 풍부한 가습")
                b3_url = st.text_input("상품 3 스토어 링크", value=str(r2.get("스마트스토어링크", "https://smartstore.naver.com/")))

            top3_card_html = f"""
<table width="100%" style="max-width:640px;margin:0 auto;border-collapse:collapse;font-family:'Malgun Gothic',sans-serif;border:3px solid #1e293b;background:#ffffff;border-radius:12px;overflow:hidden;">
    <tr bgcolor="#1e293b">
        <td style="padding:20px 24px;color:#ffffff;text-align:center;">
            <div style="font-size:12px;color:#facc15;font-weight:900;letter-spacing:1px;margin-bottom:4px;">MD CURATION BEST 3 SELECTION</div>
            <div style="font-size:21px;font-weight:900;margin-bottom:6px;">{curation_title}</div>
            <div style="font-size:13.5px;color:#cbd5e1;">{curation_sub}</div>
        </td>
    </tr>
    <tr>
        <td style="padding:18px 22px;border-bottom:1px solid #e2e8f0;background:#f8fafc;">
            <span style="background:#e11d48;color:#fff;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:900;">🥇 BEST 1</span>
            <div style="font-size:18px;font-weight:900;color:#111;margin:8px 0 4px 0;">{b1_name}</div>
            <div style="font-size:13.5px;color:#475569;margin-bottom:10px;">✔️ {b1_desc}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:20px;font-weight:900;color:#e11d48;">특별가 {b1_price:,}원</span>
                <a href="{b1_url}" target="_blank" style="background:#03c75a;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:800;">👉 스토어 보러가기</a>
            </div>
        </td>
    </tr>
    <tr>
        <td style="padding:18px 22px;border-bottom:1px solid #e2e8f0;background:#ffffff;">
            <span style="background:#2563eb;color:#fff;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:900;">🥈 BEST 2</span>
            <div style="font-size:18px;font-weight:900;color:#111;margin:8px 0 4px 0;">{b2_name}</div>
            <div style="font-size:13.5px;color:#475569;margin-bottom:10px;">✔️ {b2_desc}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:20px;font-weight:900;color:#2563eb;">특별가 {b2_price:,}원</span>
                <a href="{b2_url}" target="_blank" style="background:#03c75a;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:800;">👉 스토어 보러가기</a>
            </div>
        </td>
    </tr>
    <tr>
        <td style="padding:18px 22px;background:#f8fafc;">
            <span style="background:#0d9488;color:#fff;padding:3px 10px;border-radius:6px;font-size:12px;font-weight:900;">🥉 BEST 3</span>
            <div style="font-size:18px;font-weight:900;color:#111;margin:8px 0 4px 0;">{b3_name}</div>
            <div style="font-size:13.5px;color:#475569;margin-bottom:10px;">✔️ {b3_desc}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:20px;font-weight:900;color:#0d9488;">특별가 {b3_price:,}원</span>
                <a href="{b3_url}" target="_blank" style="background:#03c75a;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:800;">👉 스토어 보러가기</a>
            </div>
        </td>
    </tr>
</table>
"""
            with t3_prev:
                st.markdown("#### 👀 Top 3 큐레이션 프리뷰 & 추출")
                t3_comp = f"""
                <!DOCTYPE html><html><head><meta charset="utf-8">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .btn {{ width:100%; padding:15px; font-size:16px; font-weight:900; border:none; border-radius:8px; cursor:pointer; margin-bottom:8px; color:#fff; }}
                </style></head>
                <body>
                    <button class="btn" style="background:#111827;" onclick="dlT3()">📸 Top 3 기획전 카드 PNG 사진으로 저장</button>
                    <button class="btn" style="background:#03c75a;" onclick="cpT3()">📋 블로그/카페 표 서식 통째로 복사 (Ctrl+V)</button>
                    <div id="t3Msg" style="display:none;text-align:center;font-weight:bold;color:#16a34a;margin-bottom:8px;">✅ 복사 완료! 블로그에 붙여넣으세요!</div>
                    <div id="t3Wrap" style="background:#fff;padding:10px;border-radius:12px;">{top3_card_html}</div>
                    <script>
                    function cpT3() {{
                        const r = document.createRange(); r.selectNode(document.getElementById('t3Wrap'));
                        const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
                        document.execCommand('copy'); s.removeAllRanges();
                        document.getElementById('t3Msg').style.display='block';
                    }}
                    function dlT3() {{
                        html2canvas(document.getElementById('t3Wrap'), {{ scale:2, backgroundColor:'#ffffff' }}).then(c => {{
                            const a = document.createElement('a'); a.download='Top3_큐레이션_기획전.png'; a.href=c.toDataURL('image/png'); a.click();
                        }});
                    }}
                    </script>
                </body></html>
                """
                components.html(t3_comp, height=780, scrolling=True)

        # ------------------------------------------
        # 신규 기능: 도매처 상세페이지 '통이미지' 사이 3초 후킹 설득 문구 삽입기
        # ------------------------------------------
        with sub_mk_hook:
            st.subheader("⚡ 도매처 상세페이지 '통이미지' 3초 후킹 설득 브릿지 생성기")
            st.write(
                "도매처가 주는 똑같은 상세페이지 사진만 올려두면 고객이 스크롤만 내리다 나갑니다. "
                "**상세페이지 맨 위(도입부)와 사진 중간에 이 '설득 브릿지 카드(PNG 또는 표)'를 끼워 넣으면 구매 전환율이 2배 이상 상승**합니다!"
            )

            hk1, hk2 = st.columns([1.0, 1.3], gap="large")
            with hk1:
                hk_problem = st.text_input("😟 고객이 겪던 기존 불편함 (문제 제기)", value="비슷해 보이는 저가형 샀다가 하루 만에 고장 나고 후회하셨나요?")
                hk_solution = st.text_input("💡 우리 상품만의 확실한 해결책", value="저희 스토어는 출고 전 1:1 직접 작동 검수를 거친 정품만 발송합니다!")
                hk_guarantee = st.text_input("🛡️ 고객 안심 보장 약속", value="수령 후 마음에 안 드시거나 초기 불량 시 100% 무료 맞교환 보장")

            hook_html = f"""
            <!DOCTYPE html><html><head><meta charset="utf-8">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
            </head><body style="margin:0;font-family:'Malgun Gothic',sans-serif;">
                <button onclick="dlHook()" style="width:100%;background:#e11d48;color:#fff;border:none;padding:15px;border-radius:8px;font-size:16px;font-weight:900;cursor:pointer;margin-bottom:12px;">
                    📸 상세페이지 삽입용 '3초 후킹 브릿지' PNG 이미지 다운로드
                </button>
                <div id="hookBox" style="background:#111827;color:#ffffff;padding:30px 26px;border-radius:14px;text-align:center;max-width:650px;margin:0 auto;border:4px solid #facc15;">
                    <div style="background:#e11d48;color:#fff;display:inline-block;padding:5px 16px;border-radius:20px;font-size:13px;font-weight:900;margin-bottom:14px;">잠깐! 결제 전 꼭 확인하세요</div>
                    <div style="font-size:21px;font-weight:900;color:#fca5a5;line-height:1.4;margin-bottom:18px;">"{hk_problem}"</div>
                    <div style="background:#1f2937;padding:18px;border-radius:10px;border-left:5px solid #34d399;text-align:left;margin-bottom:14px;">
                        <div style="font-size:13px;color:#34d399;font-weight:800;margin-bottom:4px;">✅ WHY CHOOSE US (차별화 포인트)</div>
                        <div style="font-size:16px;font-weight:900;color:#ffffff;line-height:1.5;">{hk_solution}</div>
                    </div>
                    <div style="font-size:14.5px;font-weight:800;color:#facc15;">🛡️ 약속드립니다: {hk_guarantee}</div>
                </div>
                <script>
                function dlHook() {{
                    html2canvas(document.getElementById('hookBox'), {{ scale:2, backgroundColor:'#111827' }}).then(c => {{
                        const a = document.createElement('a'); a.download='상세페이지_3초후킹브릿지.png'; a.href=c.toDataURL('image/png'); a.click();
                    }});
                }}
                </script>
            </body></html>
            """
            with hk2:
                components.html(hook_html, height=410, scrolling=False)

        with sub_mk2:
            st.subheader("🖼️ 스마트스토어 대표 썸네일(1000x1000 정사각형) 프레임·배지 합성 스튜디오")
            th_c1, th_c2 = st.columns([1.0, 1.3], gap="large")
            with th_c1:
                th_top_left = st.text_input("🏷️ 좌측 상단 스티커 배지", value="🚀 오늘출발")
                th_top_right = st.text_input("🔥 우측 상단 원형 강조 배지", value="특가\n할인")
                th_bottom_bar = st.text_input("📢 하단 와이드 배너 문구", value="전용 파우치 무료 증정 + 무료배송")
                th_color = st.selectbox("🎨 프레임 & 배지 컬러", ["#03c75a", "#e11d48", "#1e3a8a", "#111827", "#d97706"])
                th_border_px = st.slider("🔲 정사각형 외곽 테두리 두께 (px)", min_value=0, max_value=40, value=18)

            with th_c2:
                thumb_html = f"""
                <!DOCTYPE html><html><head><meta charset="utf-8">
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .ctrl-box {{ background:#1e293b; color:#fff; padding:14px; border-radius:10px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; }}
                    .dl-btn {{ background:{th_color}; color:#fff; border:none; padding:12px 20px; border-radius:8px; font-size:15px; font-weight:900; cursor:pointer; }}
                    canvas {{ width:430px; height:430px; border-radius:10px; background:#fff; display:block; margin:0 auto; box-shadow:0 4px 12px rgba(0,0,0,0.2); }}
                </style></head>
                <body>
                    <div class="ctrl-box">
                        <div>
                            <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">📂 1. 도매처 원본 상품 사진 선택</div>
                            <input type="file" id="imgInput" accept="image/*" style="font-size:13px;" />
                        </div>
                        <button class="dl-btn" onclick="downloadThumb()">📸 1000x1000 PNG 저장</button>
                    </div>
                    <canvas id="thumbCanvas" width="1000" height="1000"></canvas>
                    <script>
                    const canvas = document.getElementById('thumbCanvas');
                    const ctx = canvas.getContext('2d');
                    let loadedImg = null;
                    function drawCanvas() {{
                        ctx.fillStyle = '#f8fafc'; ctx.fillRect(0, 0, 1000, 1000);
                        if (loadedImg) {{
                            const s = Math.max(1000 / loadedImg.width, 1000 / loadedImg.height);
                            ctx.drawImage(loadedImg, (1000 - loadedImg.width*s)/2, (1000 - loadedImg.height*s)/2, loadedImg.width*s, loadedImg.height*s);
                        }} else {{
                            ctx.fillStyle = '#94a3b8'; ctx.font = 'bold 34px Malgun Gothic'; ctx.textAlign = 'center';
                            ctx.fillText('위 [파일 선택]을 눌러 상품 사진을 올려주세요', 500, 480);
                        }}
                        const btm = `{th_bottom_bar}`;
                        if (btm.trim() !== '') {{
                            ctx.fillStyle = 'rgba(17,24,39,0.88)'; ctx.fillRect(0, 870, 1000, 130);
                            ctx.fillStyle = '#facc15'; ctx.font = '900 44px Malgun Gothic'; ctx.textAlign = 'center'; ctx.fillText(btm, 500, 950);
                        }}
                        if ({th_border_px} > 0) {{
                            ctx.strokeStyle = '{th_color}'; ctx.lineWidth = {th_border_px} * 2; ctx.strokeRect(0, 0, 1000, 1000);
                        }}
                        const tl = `{th_top_left}`;
                        if (tl.trim() !== '') {{
                            ctx.fillStyle = '{th_color}'; ctx.beginPath(); ctx.roundRect(45, 45, 340, 95, 18); ctx.fill();
                            ctx.fillStyle = '#fff'; ctx.font = '900 42px Malgun Gothic'; ctx.textAlign = 'center'; ctx.fillText(tl, 215, 108);
                        }}
                        const tr = `{th_top_right.replace(chr(10), "\\n")}`;
                        if (tr.trim() !== '') {{
                            ctx.fillStyle = '#e11d48'; ctx.beginPath(); ctx.arc(870, 130, 90, 0, Math.PI*2); ctx.fill();
                            ctx.lineWidth = 6; ctx.strokeStyle = '#fff'; ctx.stroke();
                            ctx.fillStyle = '#fff'; ctx.font = '900 38px Malgun Gothic'; ctx.textAlign = 'center';
                            const lns = tr.split('\\n');
                            if (lns.length > 1) {{ ctx.fillText(lns[0], 870, 118); ctx.fillText(lns[1], 870, 165); }}
                            else {{ ctx.fillText(lns[0], 870, 142); }}
                        }}
                    }}
                    document.getElementById('imgInput').addEventListener('change', function(e) {{
                        const f = e.target.files[0]; if (!f) return;
                        const r = new FileReader();
                        r.onload = function(ev) {{ const img = new Image(); img.onload = function() {{ loadedImg = img; drawCanvas(); }}; img.src = ev.target.result; }};
                        r.readAsDataURL(f);
                    }});
                    function downloadThumb() {{
                        const a = document.createElement('a'); a.download = '스마트스토어_썸네일_1000x1000.png'; a.href = canvas.toDataURL('image/png'); a.click();
                    }}
                    drawCanvas();
                    </script>
                </body></html>
                """
                components.html(thumb_html, height=550, scrolling=False)

        with sub_mk3:
            st.subheader("📢 스마트스토어 상세페이지 상·하단 공통 공지 배너 생성기 (배송/교환/AS 안내 PNG)")
            bn_c1, bn_c2 = st.columns([1.0, 1.3], gap="large")
            with bn_c1:
                bn_store_name = st.text_input("🏪 내 스마트스토어 이름", value="트렌드 픽 공식 스토어")
                bn_cutoff = st.text_input("⏰ 당일출고 마감 시간", value="평일 오후 2시 이전 결제 완료 건 당일 발송")
                bn_courier = st.text_input("🚚 지정 택배사 및 배송기간", value="CJ대한통운 / 한진택배 (출고 후 1~2일 내 수령)")
                bn_return_rule = st.text_input("🔄 교환/반품 핵심 안내", value="수령 후 7일 이내 접수 가능 (초기불량 100% 판매자 부담 / 단순변심 왕복 6,000원)")
                bn_cs_time = st.text_input("☎️ 고객센터 운영 안내", value="네이버 톡톡 문의: 평일 10:00 ~ 17:00 (점심시간 12:00~13:00)")

            with bn_c2:
                notice_banner_html = f"""
                <!DOCTYPE html><html><head><meta charset="utf-8">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .dl-bar {{ width:100%; background:#111827; color:#fff; border:none; padding:15px; border-radius:8px; font-size:16px; font-weight:900; cursor:pointer; margin-bottom:12px; }}
                </style></head>
                <body>
                    <button class="dl-bar" onclick="dlNotice()">📸 상세페이지 공지 배너 PNG 이미지 다운로드</button>
                    <div id="noticeBox" style="background:#ffffff; border:3px solid #1e293b; border-radius:12px; overflow:hidden; max-width:680px; margin:0 auto;">
                        <div style="background:#1e293b; color:#ffffff; padding:18px 24px; text-align:center;">
                            <div style="font-size:13px; color:#38bdf8; font-weight:800; margin-bottom:4px;">OFFICIAL STORE DELIVERY & CS POLICY</div>
                            <div style="font-size:22px; font-weight:900;">[{bn_store_name}] 주문 및 배송·교환 필수 안내</div>
                        </div>
                        <div style="padding:22px 26px; font-size:14.5px; color:#1e293b; line-height:1.9;">
                            <div style="margin-bottom:10px;">🚀 <b>출고 마감 안내:</b> {bn_cutoff}</div>
                            <div style="margin-bottom:10px;">🚚 <b>택배사 및 배송:</b> {bn_courier}</div>
                            <div style="margin-bottom:10px;">🔄 <b>교환 및 반품 기준:</b> {bn_return_rule}</div>
                            <div>💬 <b>고객센터(CS) 안내:</b> {bn_cs_time}</div>
                        </div>
                        <div style="background:#f8fafc; padding:12px 24px; border-top:1px solid #e2e8f0; font-size:12.5px; color:#64748b; text-align:center;">
                            ※ 사전 협의 없이 임의 반품하거나 상품 택(Tag)/포장 훼손 시 교환 및 환불이 제한될 수 있습니다.
                        </div>
                    </div>
                    <script>
                    function dlNotice() {{
                        html2canvas(document.getElementById('noticeBox'), {{ scale: 2, backgroundColor: '#ffffff' }}).then(canvas => {{
                            const a = document.createElement('a');
                            a.download = '스마트스토어_상세페이지_공지배너.png';
                            a.href = canvas.toDataURL('image/png');
                            a.click();
                        }});
                    }}
                    </script>
                </body></html>
                """
                components.html(notice_banner_html, height=420, scrolling=False)

        with sub_mk4:
            st.subheader("🚀 SEO 황금 상품명·원고 생성기 & 상표권/식약처 법적 금지어 실시간 검출기")
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
                raw_wholesale_title = st.text_input("도매처 원본 상품명 (지재권·금지어 자동 스캔 대상)", value=raw_default_name)
                target_main_kw = st.text_input("핵심 타겟 키워드 (쉼표 구분)", value="감성캠핑용품, 접이식우드테이블, 피크닉테이블")
                target_sub_kw = st.text_input("용도 / 타겟층 수식어", value="차박, 캠핑초보, 베란다홈캠핑, 집들이선물")
                spec_kw = st.text_input("핵심 스펙 / 특징 단어", value="초경량, 원목, 파우치증정")
                post_tone = st.radio(
                    "📝 생성할 블로그/카페 홍보 원고 스타일",
                    ["① 블로그 내돈내산·실사용 추천 후기톤", "② 블로그 정보성 꼼꼼 비교·분석톤", "③ 네이버 카페 회원 전용 공동구매·특가 공지톤"],
                )

                combined_check_text = f"{raw_wholesale_title} {target_main_kw} {target_sub_kw} {spec_kw}"
                found_risks = [f"- ❌ **`{bw}`** ({rs}) ➡️ 권장 대체어: **`{alt}`**" for bw, (rs, alt) in LEGAL_RISK_DICT.items() if bw in combined_check_text]
                if found_risks:
                    st.error("🚨 **[지재권·법적 금지어 경보]** 입력한 단어 중 내용증명 또는 스토어 페널티 위험 단어가 감지되었습니다!\n\n" + "\n".join(found_risks))
                else:
                    st.success("🛡️ **[지재권·법적 금지어 통과]** 상표권 침해 및 의료기기법/식약처 위반 금지어가 감지되지 않았습니다.")

            cleaned_base = re.sub(r"\[.*?\]|\(.*?\)|★|☆|♥|♡|/|_|!|\+|~|-", " ", raw_wholesale_title)
            for bw in list(LEGAL_RISK_DICT.keys()) + ["당일발송", "무료배송", "특가", "할인", "세일", "최저가", "인기", "추천", "주문폭주", "정품"]:
                cleaned_base = cleaned_base.replace(bw, " ")

            base_tokens = [tk for i, tk in enumerate(cleaned_base.split()) if tk not in cleaned_base.split()[:i] and len(tk) >= 1]
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
                uniq_w = [w for i, w in enumerate(cand.split()) if w not in cand.split()[:i]]
                joined = " ".join(uniq_w)[:48]
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
                blog_draft = f"[추천 타이틀] {m1_k} 고민 끝! {clean_core_name} 실사용 솔직 정리 ✨\n\n안녕하세요! 요즘 {s1_k} 준비하면서 정착하게 된 가성비 끝판왕 '{clean_core_name}'을 소개해 드립니다!\n\n📌 [핵심 장점 3가지]\n1️⃣ {sp1_k} 사양이라 마감 퀄리티가 탄탄합니다.\n2️⃣ 초보자도 1분이면 바로 세팅할 수 있을 만큼 간편해요 ({sp2_k}).\n3️⃣ {s1_k}뿐만 아니라 {s2_k} 용도로도 디자인이 깔끔합니다.\n\n👉 공식 스마트스토어({raw_default_price:,}원 특가): {raw_default_url}\n\n{hashtag_str}"
            elif "②" in post_tone:
                blog_draft = f"[추천 타이틀] {m1_k} 실패 없이 고르는 법! ({clean_core_name} 비교 분석) 📊\n\n🔍 [구매 전 반드시 확인해야 할 3대 기준]\n✔️ 체크 1. 소재와 내구성: '{sp1_k}' 여부를 꼭 확인하세요.\n✔️ 체크 2. 휴대성과 구성품: '{sp2_k}' 등 필수 구성이 포함되어 있는지 따져보세요.\n✔️ 체크 3. 빠른 국내 발송 & AS: 불량 시 즉시 교환되는 곳인지가 핵심입니다.\n\n👉 공식 판매처 상세페이지 바로가기: {raw_default_url}\n\n{hashtag_str}"
            else:
                blog_draft = f"📢 [카페 회원 전용 특가 공지] {clean_core_name} 한정수량 안내 🔥\n\n• 상품명: {clean_core_name} ({sp1_k} / {sp2_k})\n• 회원 특별가: {raw_default_price:,}원\n• 출고 안내: 평일 오후 2시 이전 주문 시 당일 발송\n\n👉 네이버 스마트스토어 바로가기: {raw_default_url}\n\n{hashtag_str}"

            with sc2:
                render_copy_box("🏷️ SEO 추천 상품명 5가지 (금지어·특수문자·중복단어 제거 완료)", seo_names_block, "seo_names", "#1e3a8a", 215)
                render_copy_box("📝 블로그·카페 맞춤형 포스팅 원고 & 해시태그 15개", blog_draft, "blog_draft", "#03c75a", 360)

        with sub_mk5:
            st.subheader("🔗 블로그·카페 유입 경로 추적 링크(네이버 애널리틱스 `nt_source` 파라미터) 생성기")
            utm_c1, utm_c2 = st.columns([1.0, 1.3], gap="large")
            with utm_c1:
                base_store_link = st.text_input("내 스마트스토어 상품 원본 URL", value="https://smartstore.naver.com/mystore/products/10000001")
                nt_source = st.selectbox("유입 채널 (nt_source)", ["naver_blog (네이버 블로그)", "naver_cafe (네이버 카페)", "instagram (인스타그램)", "youtube (유튜브)"])
                nt_medium = st.selectbox("홍보 방식 (nt_medium)", ["infographic_card (인포그래픽배너)", "review_post (내돈내산후기글)", "group_buy (카페공구공지)", "profile_link (프로필링크)"])
                nt_detail = st.text_input("게시글 구분 별칭 (nt_detail - 영문/숫자 권장)", value=f"post_{today.strftime('%m%d')}")

            src_code = nt_source.split(" ")[0]
            med_code = nt_medium.split(" ")[0]
            sep = "&" if "?" in base_store_link else "?"
            tracked_url = f"{base_store_link.strip()}{sep}nt_source={src_code}&nt_medium={med_code}&nt_detail={nt_detail.strip()}"

            with utm_c2:
                render_copy_box("🎯 생성된 스마트스토어 유입 추적 전용 URL", tracked_url, "utm_box", "#6d28d9", 180)
                st.info("💡 위 추적 URL을 복사해 [인포그래픽 제작] 탭의 구매 링크 칸에 넣으면 어떤 블로그 글에서 결제가 일어났는지 스마트스토어 통계에 기록됩니다!")

    # ==================================================================================
    # MENU 5: 💰 수익장부·등급진단·세트·세금 (장부 + 월별기록 + 등급시뮬레이터 + 1+1세트 + 마진/ROAS/세금 + 시트원본)
    # ==================================================================================
    elif main_menu == "💰 5. 수익장부·등급진단·세트·세금":
        sub_f1, sub_f2, sub_f_tier, sub_f3, sub_f4, sub_f5 = st.tabs([
            "💎 1. 실시간 수익장부 & 랭킹",
            "🗓️ 2. 월별 정산 마감 & 그래프",
            "👑 3. 스마트스토어 등급 상승(파워/빅파워) 진단기",
            "🎁 4. 1+1 세트 & 무료배송 마진 설계",
            "🎯 5. 단품 마진 · ROAS · 세금 계산기",
            "📊 6. 구글 시트 원본 보기",
        ])

        col_ym, col_fee_opt, col_extra_exp = st.columns(3)
        with col_ym:
            settlement_ym = st.text_input("🗓️ 정산 기준 연월 (예: 2026-11)", value=today.strftime("%Y-%m"))
        with col_fee_opt:
            ledger_fee_rate = st.number_input("📉 정산 기준 네이버 수수료율 (%)", value=5.6, step=0.1, key="ledger_fee")
        with col_extra_exp:
            extra_fixed_cost = st.number_input("🧾 이번 달 추가 고정 지출 (택배박스/프로그램비 등, 원)", value=0, step=5000)

        ledger_rows = []
        total_rev, total_wholesale_cost, total_naver_fee, total_ad_cost, total_qty_sold = 0, 0, 0, 0, 0

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
            total_qty_sold += qty

            ledger_rows.append({
                "상품명": p_name, "도매처": w_name, "판매단가": f"{s_p:,}원", "개당순마진": f"{unit_margin:,}원",
                "판매수량": f"{qty:,}개", "총매출액 (수익)": f"{item_rev:,}원", "도매원가 합계": f"{item_w_cost:,}원",
                "수수료 합계": f"{item_fee_cost:,}원", "광고/기타지출": f"{ad_c:,}원",
                "최종 순수익": item_net_profit, "순수익(표시)": f"{item_net_profit:,}원", "실마진율": f"{item_roi:.1f}%",
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
                display_cols = ["상품명", "도매처", "판매수량", "총매출액 (수익)", "도매원가 합계", "수수료 합계", "광고/기타지출", "순수익(표시)", "실마진율"]
                st.dataframe(df_ledger[display_cols], use_container_width=True, hide_index=True)

                csv_backup_bytes = df_ledger[display_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label=f"💾 [{settlement_ym}] 상품별 정산 상세내역 CSV 다운로드",
                    data=csv_backup_bytes, file_name=f"스마트스토어_정산장부_{settlement_ym}.csv",
                    mime="text/csv", use_container_width=True,
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
                            <div class="rank-title"><span class="rank-badge" style="background:{bar_color};">{rank_label}</span><span>{r_row['상품명']}</span></div>
                            <div class="rank-profit" style="color:{val_color};">{p_val:,}원 <span class="sub-info">({r_row['판매수량']} / 마진 {r_row['실마진율']})</span></div>
                        </div>
                        <div class="progress-bg"><div class="progress-fill" style="width:{bar_pct}%; background:{bar_color};"></div></div>
                    </div>
                    """

                ranking_component_html = f"""
                <!DOCTYPE html><html><head><meta charset="utf-8">
                <style>
                    body {{ margin:0; padding:0; font-family:'Malgun Gothic',sans-serif; background:transparent; }}
                    .rank-container {{ background:#1e293b; border:1px solid #334155; border-radius:12px; padding:16px; color:#f8fafc; }}
                    .rank-card {{ margin-bottom:14px; }}
                    .rank-card:last-child {{ margin-bottom:0; }}
                    .rank-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; gap:8px; flex-wrap:wrap; }}
                    .rank-title {{ display:flex; align-items:center; gap:8px; font-size:14px; font-weight:800; color:#fff; }}
                    .rank-badge {{ font-size:11.5px; padding:2px 8px; border-radius:6px; color:#fff; font-weight:900; }}
                    .rank-profit {{ font-size:14.5px; font-weight:900; }}
                    .sub-info {{ font-size:11.5px; color:#94a3b8; font-weight:normal; }}
                    .progress-bg {{ width:100%; height:12px; background:#0f172a; border-radius:999px; overflow:hidden; }}
                    .progress-fill {{ height:100%; border-radius:999px; }}
                </style></head>
                <body><div class="rank-container">{rank_bars_html}</div></body></html>
                """
                components.html(ranking_component_html, height=max(240, len(df_ranked) * 64 + 35), scrolling=True)

        with sub_f2:
            st.subheader("🗓️ 월별 정산 기록 마감 & 누적 수익 추이 (`월별_수익지출_요약` 탭 연동)")
            tsv_monthly_row = f"{settlement_ym}\t{total_rev}\t{total_wholesale_cost}\t{total_naver_fee}\t{total_ad_and_extra}\t{final_net_profit}\t{overall_margin_rate:.1f}%"
            pretty_monthly_preview = (
                f"📌 [구글 시트 '월별_수익지출_요약' 탭 A열 클릭 후 Ctrl+V 하면 7칸에 자동 입력됩니다]\n"
                f"• 기준월: {settlement_ym} | • 총매출액: {total_rev:,}원 | • 도매원가합계: {total_wholesale_cost:,}원 | "
                f"• 네이버수수료: {total_naver_fee:,}원 | • 광고및기타지출: {total_ad_and_extra:,}원 | • 최종순수익: {final_net_profit:,}원 ({overall_margin_rate:.1f}%)"
            )
            render_copy_box(f"📥 [{settlement_ym}] 월간 정산 마감 데이터 한 줄 복사", tsv_monthly_row, "monthly_tsv", "#2563eb", 145, display_text=pretty_monthly_preview)

            df_m_valid = df_monthly_raw[df_monthly_raw["기준월"].astype(str).str.match(r"^20\d{2}-\d{2}")].copy()
            if not df_m_valid.empty:
                for m_col in ["총매출액", "도매원가합계", "네이버수수료합계", "광고및기타지출", "최종순수익"]:
                    df_m_valid[f"{m_col}_num"] = pd.to_numeric(df_m_valid.get(m_col, pd.Series([0]*len(df_m_valid))).astype(str).str.replace(r"[^0-9.-]", "", regex=True), errors="coerce").fillna(0)

                m_hist_left, m_hist_right = st.columns([1.3, 1.2], gap="large")
                with m_hist_left:
                    st.markdown("#### 📜 구글 시트에 저장된 월별 수익·지출 누적 장부")
                    m_show_rows = [{
                        "기준월": str(m_r["기준월"]),
                        "총매출액": f"{int(m_r['총매출액_num']):,}원",
                        "도매원가합계": f"{int(m_r['도매원가합계_num']):,}원",
                        "수수료합계": f"{int(m_r['네이버수수료합계_num']):,}원",
                        "광고/기타지출": f"{int(m_r['광고및기타지출_num']):,}원",
                        "최종순수익": f"{int(m_r['최종순수익_num']):,}원",
                        "수익률": f"{(m_r['최종순수익_num'] / m_r['총매출액_num'] * 100) if m_r['총매출액_num'] > 0 else 0.0:.1f}%",
                    } for _, m_r in df_m_valid.iterrows()]
                    st.dataframe(pd.DataFrame(m_show_rows), use_container_width=True, hide_index=True)

                with m_hist_right:
                    st.markdown("#### 📈 월별 매출 & 최종 순수익 성장 추이")
                    max_m_rev = max(df_m_valid["총매출액_num"].max(), 1)
                    m_bars_html = ""
                    for _, m_r in df_m_valid.iterrows():
                        rev_v, net_v = int(m_r["총매출액_num"]), int(m_r["최종순수익_num"])
                        rev_w = max(2, min(100, int((rev_v / max_m_rev) * 100)))
                        net_w = max(2, min(100, int((net_v / max_m_rev) * 100))) if net_v > 0 else 0
                        m_bars_html += f"""
                        <div style="margin-bottom:12px;">
                            <div style="display:flex;justify-content:space-between;font-size:13.5px;font-weight:800;color:#fff;margin-bottom:4px;">
                                <span>🗓️ {m_r['기준월']}</span><span>매출 {rev_v:,}원 / <span style="color:#34d399;">순수익 {net_v:,}원</span></span>
                            </div>
                            <div style="width:100%;height:10px;background:#0f172a;border-radius:999px;overflow:hidden;margin-bottom:3px;"><div style="width:{rev_w}%;height:100%;background:#3b82f6;"></div></div>
                            <div style="width:100%;height:10px;background:#0f172a;border-radius:999px;overflow:hidden;"><div style="width:{net_w}%;height:100%;background:#10b981;"></div></div>
                        </div>
                        """
                    components.html(f"<!DOCTYPE html><html><body style='margin:0;font-family:Malgun Gothic,sans-serif;'><div style='background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;'><div style='font-size:12px;color:#94a3b8;margin-bottom:10px;'>🟦 파란 바: 월 총매출액 | 🟩 초록 바: 월 최종 순수익</div>{m_bars_html}</div></body></html>", height=max(180, len(df_m_valid) * 62 + 50), scrolling=True)

        # ------------------------------------------
        # 신규 기능: 스마트스토어 등급 상승(씨앗 -> 파워 -> 빅파워) 목표 달성 시뮬레이터
        # ------------------------------------------
        with sub_f_tier:
            st.subheader("👑 스마트스토어 등급 상승 (씨앗 ➡️ 새싹 ➡️ 파워 ➡️ 빅파워) 달성 시뮬레이터")
            st.write(
                "네이버 스마트스토어는 **최근 3개월 누적 판매 건수와 매출액**으로 매월 2일 등급이 산정됩니다. "
                "**'파워' 등급 이상을 달성하면 상품에 파워 배지가 붙어 상위노출과 클릭률이 비약적으로 상승**합니다!"
            )

            tr1, tr2, tr3 = st.columns(3)
            with tr1:
                curr_3m_cnt = st.number_input("최근 3개월 누적 판매 건수 (건)", value=int(total_qty_sold * 2), step=10)
            with tr2:
                curr_3m_rev = st.number_input("최근 3개월 누적 매출액 (원)", value=int(total_rev * 2), step=500000)
            with tr3:
                remain_days = st.slider("이번 달 등급 심사 마감까지 남은 일수 (일)", min_value=1, max_value=90, value=20)

            # 스마트스토어 공식 등급 기준 (최근 3개월 합산)
            tiers = [
                ("🌱 새싹 등급", 100, 2000000),
                ("⚡ 파워 등급 (1차 핵심 목표!)", 300, 8000000),
                ("🔥 빅파워 등급", 1500, 40000000),
                ("💎 프리미엄 등급", 4000, 80000000),
            ]

            for t_name, req_cnt, req_rev in tiers:
                cnt_pct = min(100.0, (curr_3m_cnt / req_cnt) * 100)
                rev_pct = min(100.0, (curr_3m_rev / req_rev) * 100)
                need_cnt = max(0, req_cnt - curr_3m_cnt)
                need_rev = max(0, req_rev - curr_3m_rev)
                daily_need_cnt = (need_cnt / remain_days) if remain_days > 0 else need_cnt
                daily_need_rev = int(need_rev / remain_days) if remain_days > 0 else need_rev

                with st.container(border=True):
                    st.markdown(f"#### {t_name} (기준: 3개월 {req_cnt:,}건 이상 & 매출 {req_rev:,}원 이상)")
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        st.progress(cnt_pct / 100.0, text=f"📦 판매건수 달성률: {cnt_pct:.1f}% ({curr_3m_cnt:,} / {req_cnt:,}건)")
                    with tc2:
                        st.progress(rev_pct / 100.0, text=f"💰 매출액 달성률: {rev_pct:.1f}% ({curr_3m_rev:,} / {req_rev:,}원)")

                    if need_cnt == 0 and need_rev == 0:
                        st.success(f"🎉 축하합니다! 이미 **{t_name}** 달성 조건을 모두 충족하셨습니다!")
                    else:
                        st.info(
                            f"🎯 **남은 목표:** 건수 **{need_cnt:,}건** / 매출 **{need_rev:,}원** 추가 필요 "
                            f"👉 앞으로 {remain_days}일간 **하루 평균 {daily_need_cnt:.1f}건 ({daily_need_rev:,}원/일)** 판매하면 등급이 상승합니다!"
                        )

        with sub_f3:
            st.subheader("🎁 객단가 2배 상승! 1+1(2개 묶음) & 무료배송 전환 마진 비교 설계기")
            bd1, bd2, bd3, bd4 = st.columns(4)
            with bd1:
                b_unit_w = st.number_input("1개당 도매원가 (원)", value=8900, step=500)
            with bd2:
                b_unit_s = st.number_input("1개 단품 판매가 (원)", value=17900, step=500)
            with bd3:
                b_ship_cost = st.number_input("도매처 1회 출고 택배비 (원)", value=3000, step=500)
            with bd4:
                b_bundle_disc = st.number_input("2개 구매 시 고객 추가할인액 (원)", value=2000, step=500)

            fee_r = ledger_fee_rate / 100.0
            single_fee = int(round((b_unit_s + b_ship_cost) * fee_r))
            single_net = (b_unit_s + b_ship_cost) - b_unit_w - b_ship_cost - single_fee

            bundle2_pay = (b_unit_s * 2) - b_bundle_disc
            bundle2_fee = int(round(bundle2_pay * fee_r))
            bundle2_net = bundle2_pay - (b_unit_w * 2) - b_ship_cost - bundle2_fee

            bundle3_pay = (b_unit_s * 3) - (b_bundle_disc * 2)
            bundle3_fee = int(round(bundle3_pay * fee_r))
            bundle3_net = bundle3_pay - (b_unit_w * 3) - b_ship_cost - bundle3_fee

            bc1, bc2, bc3 = st.columns(3)
            bc1.info(f"📦 **단품 1개 판매 시 (유료배송)**\n\n- 고객 결제액: {b_unit_s:,}원 (+배송비 {b_ship_cost:,}원)\n- **내 통장 순수익: {single_net:,}원**")
            bc2.success(f"🔥 **[강력추천] 2개 세트 ({b_bundle_disc:,}원 할인 + 무료배송)**\n\n- 고객 결제액: **{bundle2_pay:,}원 (무료배송!)**\n- **내 통장 순수익: {bundle2_net:,}원** (단품 대비 **+{bundle2_net - single_net:,}원** 이득!)")
            bc3.warning(f"👑 **3개 패밀리 세트 ({b_bundle_disc*2:,}원 할인 + 무료배송)**\n\n- 고객 결제액: **{bundle3_pay:,}원 (무료배송!)**\n- **내 통장 순수익: {bundle3_net:,}원** (단품 대비 **+{bundle3_net - single_net:,}원** 이득!)")

        with sub_f4:
            st.markdown("#### 🧮 1. 목표 마진 & 스토어 쿠폰 할인가 역산 시뮬레이터")
            sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)
            with sim_c1:
                sim_w_cost = st.number_input("1️⃣ 도매 공급원가 (원)", value=14000, step=500)
            with sim_c2:
                sim_ship_subsidy = st.number_input("2️⃣ 배송비 보조금 (원)", value=0, step=500)
            with sim_c3:
                sim_coupon = st.number_input("3️⃣ 스토어 할인 쿠폰액 (원)", value=1000, step=500)
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
            st.markdown("#### 🎯 2. 네이버 쇼핑검색광고 손익분기 ROAS & 최대 클릭당 입찰가(Max CPC) 계산기")
            ro1, ro2, ro3 = st.columns(3)
            with ro1:
                ad_prod_price = st.number_input("광고할 상품 판매가 (원)", value=int(required_actual_pay), step=500)
            with ro2:
                ad_unit_margin = st.number_input("광고비 제외 개당 순마진 (원)", value=int(sim_target_profit), step=500)
            with ro3:
                ad_conv_rate = st.number_input("예상 구매전환율 (%, 보통 2.0 ~ 4.0%)", value=2.5, step=0.5, min_value=0.1)

            bep_roas = (ad_prod_price / ad_unit_margin * 100) if ad_unit_margin > 0 else 9999.0
            max_cpc = int(ad_unit_margin * (ad_conv_rate / 100.0))
            rec_cpc = int(max_cpc * 0.65)

            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("🚨 손익분기 최소 ROAS", f"{bep_roas:.0f}%", "이 ROAS 밑이면 광고할수록 적자!")
            rc2.metric("🛑 손익분기 최대 클릭단가 (Max CPC)", f"{max_cpc:,}원", f"전환율 {ad_conv_rate}% 기준 본전 입찰가")
            rc3.metric("✅ 수익 확보 권장 입찰가", f"{rec_cpc:,}원", "순마진의 35% 이상 보존 입찰가")

            st.markdown("---")
            st.markdown("#### 🏦 3. 간이과세자 / 일반과세자 예상 부가세 & 세금 적립금 계산기")
            tx1, tx2, tx3 = st.columns(3)
            with tx1:
                tax_type = st.radio("사업자 과세 유형 선택", ["간이과세자 (소매업 부가가치율 15% 적용)", "일반과세자 (매출세액 10% - 매입세액 10%)"])
            with tx2:
                tax_rev = st.number_input("정산 기간 총 매출액 (원, VAT포함)", value=int(total_rev), step=100000)
            with tx3:
                tax_purchase = st.number_input("정산 기간 세금계산서 매입 합계 (원가+수수료+광고비)", value=int(total_expense), step=100000)

            if "간이" in tax_type:
                est_vat = max(0, int(round(tax_rev * 0.015 - (tax_purchase / 1.1) * 0.005)))
            else:
                est_vat = max(0, int(round((tax_rev - tax_purchase) / 11.0)))

            est_income_tax_reserve = max(0, int(round((tax_rev - tax_purchase - est_vat) * 0.066)))
            tk1, tk2, tk3 = st.columns(3)
            tk1.metric("🧾 예상 부가가치세 (VAT)", f"{est_vat:,}원")
            tk2.metric("🏦 종합소득세 대비 권장 적립액 (6.6%)", f"{est_income_tax_reserve:,}원")
            tk3.metric("💰 세금 통장에 미리 빼둘 총액", f"{est_vat + est_income_tax_reserve:,}원")

        with sub_f5:
            st.subheader("📊 구글 시트 원본 데이터 & 바로가기")
            st.markdown(f"👉 **[여기를 클릭해 내 구글 시트(상품관리 및 월별 수익장부) 바로 열기]({SHEET_BASE_URL}/edit)**")
            display_raw = [c for c in df.columns if not c.endswith("_num") and c != "상품선택"]
            st.dataframe(df[display_raw], use_container_width=True)
            st.dataframe(df_monthly_raw, use_container_width=True)

except Exception as e:
    st.error(f"앱 실행 중 오류가 발생했습니다. 상세 에러: {e}")
