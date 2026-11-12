import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3

# SSL 경고 무시 (일부 도매 사이트 접속 오류 방지)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="스마트스토어 위탁판매 매니저", layout="wide")

st.title("🛒 스마트스토어 위탁판매 & 블로그 마켓 통합 관리")
st.write(
    "구글 시트에 등록된 위탁 상품의 **도매처 품절/단종 여부를 실시간 체크**하고, "
    "**마진 계산 및 블로그/카페 홍보용 HTML 카드**를 자동으로 생성합니다."
)

# ==========================================
# 1. 구글 시트 연동 설정 (본인의 상품 관리 시트 ID와 gid로 변경하세요)
# ==========================================
sheet_id = "1-b-QusmoSnsvMhToNFe1B1IK7dJUKjjANs89y5ZekAQ"  # 새 시트 사용 시 변경
gid = "0"  # 상품 목록이 있는 탭의 gid로 변경
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=60, show_spinner=False)
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df


# ==========================================
# 2. 도매처 링크 생존 & 품절 감지 함수
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

    # 도매 사이트에서 품절/종료 시 자주 뜨는 키워드 목록
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
        "sold out",
        "out of stock",
    ]

    try:
        resp = requests.get(str(url), headers=headers, timeout=8, verify=False)
        if resp.status_code == 404:
            return "🔴 링크 삭제 (404)", "페이지가 사라졌습니다. 즉시 스토어 판매중지 필요!"
        elif resp.status_code != 200:
            return f"🟡 접속 확인 필요 ({resp.status_code})", "사이트 보안 또는 일시적 오류 (수동 확인 권장)"

        soup = BeautifulSoup(resp.text, "html.parser")
        # 스크립트나 스타일 태그 제거 후 실제 화면 텍스트만 추출
        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text(separator=" ").lower()

        detected = [kw for kw in sold_out_keywords if kw in page_text]
        if detected:
            return "🔴 품절/종료 의심", f"감지된 키워드: {', '.join(detected[:3])}"

        return "🟢 정상 판매중", "특이사항 없음 (발주 가능)"

    except Exception as e:
        return "🟡 연결 시간 초과/오류", f"수동 확인 필요 ({type(e).__name__})"


# ==========================================
# 3. 메인 화면 구성
# ==========================================
try:
    with st.spinner("구글 시트에서 상품 데이터를 불러오는 중입니다..."):
        try:
            df = load_data(csv_url)
        except Exception:
            df = pd.DataFrame()

    # 시트에 아직 상품 컬럼이 없을 경우(기존 축구 시트 상태일 경우) 안내 및 샘플 데이터 제공
    required_cols = ["상품명", "도매처링크", "도매원가", "판매가"]
    if df.empty or not all(col in df.columns for col in required_cols):
        st.warning(
            "💡 현재 연결된 구글 시트에 위탁판매용 컬럼(`상품명`, `도매처링크`, `도매원가`, `판매가`)이 없습니다. "
            "아래 샘플 데이터로 화면을 미리 테스트해 보세요!"
        )
        df = pd.DataFrame([
            {
                "상품명": "[샘플] 캠핑용 접이식 우드 롤테이블",
                "도매처명": "도매꾹",
                "도매처링크": "https://domeggook.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 25000,
                "판매가": 38900,
                "배송비": 3000,
                "블로그홍보링크": "https://blog.naver.com/",
            },
            {
                "상품명": "[샘플] 무선 미니 핸디 청소기",
                "도매처명": "오너클랜",
                "도매처링크": "https://ownerclan.com/",
                "스마트스토어링크": "https://smartstore.naver.com/",
                "도매원가": 12000,
                "판매가": 19800,
                "배송비": 3000,
                "블로그홍보링크": "https://cafe.naver.com/",
            },
        ])

    tab1, tab2, tab3 = st.tabs([
        "🚨 도매처 품절/단종 일괄 점검",
        "🧮 개별 상품 마진 & 블로그 홍보 카드",
        "📊 구글 시트 원본 데이터",
    ])

    # ------------------------------------------
    # TAB 1: 도매처 품절/단종 일괄 점검 (주문 들어왔을 때 or 매일 아침 클릭)
    # ------------------------------------------
    with tab1:
        st.subheader("🔍 등록 상품 도매처 생존 및 품절 일괄 스캔")
        st.write("버튼을 누르면 구글 시트에 등록된 모든 도매처 링크에 접속해 페이지 삭제(404)나 품절 문구가 있는지 한 번에 검사합니다.")

        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            scan_trigger = st.button("🚀 전체 상품 도매처 상태 실시간 스캔 실행", type="primary", use_container_width=True)
        with col_btn2:
            if st.button("🔄 구글 시트 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        if scan_trigger:
            results = []
            progress_bar = st.progress(0, text="도매처 링크 상태를 확인하고 있습니다...")
            total_items = len(df)

            for idx, row in df.iterrows():
                p_name = row.get("상품명", f"상품 {idx+1}")
                w_name = row.get("도매처명", "-")
                w_url = row.get("도매처링크", "")
                s_url = row.get("스마트스토어링크", "")
                b_url = row.get("블로그홍보링크", "")
                w_price = float(row.get("도매원가", 0))
                s_price = float(row.get("판매가", 0))

                status_badge, detail_msg = check_wholesale_status(w_url)

                results.append({
                    "No": idx + 1,
                    "상태": status_badge,
                    "상품명": p_name,
                    "도매처": w_name,
                    "도매원가": f"{int(w_price):,}원",
                    "스토어판매가": f"{int(s_price):,}원",
                    "점검 상세": detail_msg,
                    "도매처 바로가기": w_url,
                    "내 스토어 링크": s_url,
                    "블로그/카페 홍보글": b_url,
                })
                progress_bar.progress((idx + 1) / total_items, text=f"[{idx+1}/{total_items}] {p_name} 점검 완료")

            df_res = pd.DataFrame(results)

            # 요약 지표 출력
            danger_cnt = sum(1 for r in results if "🔴" in r["상태"])
            warn_cnt = sum(1 for r in results if "🟡" in r["상태"])
            ok_cnt = sum(1 for r in results if "🟢" in r["상태"])

            m1, m2, m3 = st.columns(3)
            m1.metric("🟢 정상 판매 가능", f"{ok_cnt}건")
            m2.metric("🔴 품절/단종 위험 (즉시 조치)", f"{danger_cnt}건")
            m3.metric("🟡 수동 확인 필요", f"{warn_cnt}건")

            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "도매처 바로가기": st.column_config.LinkColumn("도매처 링크", display_text="🔗 도매처 열기"),
                    "내 스토어 링크": st.column_config.LinkColumn("스마트스토어", display_text="🏪 스토어 열기"),
                    "블로그/카페 홍보글": st.column_config.LinkColumn("홍보 게시글", display_text="📝 게시글 열기"),
                },
            )

    # ------------------------------------------
    # TAB 2: 개별 상품 정밀 체크 (주문 접수 시 확인 & 마진 계산 & 블로그 카드 생성)
    # ------------------------------------------
    with tab2:
        st.subheader("📌 개별 상품 발주 전 점검 & 블로그/카페 홍보 카드 생성")

        df["상품선택"] = df.index.astype(str) + " | [" + df.get("도매처명", pd.Series(["기본"]*len(df))).astype(str) + "] " + df["상품명"].astype(str)
        product_list = ["➕ [직접 수동 입력 / 신규 소싱 테스트]"] + df["상품선택"].tolist()

        selected_prod_str = st.selectbox("관리할 상품을 선택하세요 (선택 시 시트 데이터 자동 연동)", product_list)

        if selected_prod_str != "➕ [직접 수동 입력 / 신규 소싱 테스트]":
            sel_idx = int(selected_prod_str.split(" | ")[0])
            row = df.iloc[sel_idx]
        else:
            row = None

        c1, c2 = st.columns(2)
        with c1:
            p_name = st.text_input("📦 상품명", value=row.get("상품명", "신규 소싱 상품") if row is not None else "캠핑용 감성 랜턴")
            w_url = st.text_input("🔗 도매처 원본 URL", value=row.get("도매처링크", "") if row is not None else "https://domeggook.com/")
            s_url = st.text_input("🏪 내 스마트스토어 상품 URL", value=row.get("스마트스토어링크", "") if row is not None else "https://smartstore.naver.com/")
            p_point = st.text_input("✨ 상품 핵심 소구점 (블로그 카드용)", value="가성비 최고, 당일 발송 가능!")

        with c2:
            w_price = st.number_input("💵 도매 공급가 (원)", value=int(row.get("도매원가", 15000)) if row is not None else 15000, step=500)
            s_price = st.number_input("🏷️ 스마트스토어 판매가 (원)", value=int(row.get("판매가", 24900)) if row is not None else 24900, step=500)
            fee_rate = st.number_input("📉 네이버 수수료율 (%)", value=5.6, step=0.1, help="스마트스토어 기본 결제수수료 + 네이버쇼핑 연동수수료 합산 약 5.5~5.8%")

            # 실시간 마진 계산
            naver_fee = int(s_price * (fee_rate / 100))
            net_profit = s_price - w_price - naver_fee
            margin_rate = (net_profit / s_price * 100) if s_price > 0 else 0.0

            st.info(
                f"💰 **예상 순수익: {net_profit:,}원** (마진율: **{margin_rate:.1f}%**)\n\n"
                f"*(판매가 {s_price:,}원 - 도매원가 {w_price:,}원 - 수수료 약 {naver_fee:,}원)*"
            )

        if st.button("🔍 이 상품 도매처 상태 즉시 확인하기", use_container_width=True):
            status_badge, detail_msg = check_wholesale_status(w_url)
            if "🟢" in status_badge:
                st.success(f"**{status_badge}** : {detail_msg} 👉 지금 도매처에 발주 넣으셔도 됩니다!")
            elif "🔴" in status_badge:
                st.error(f"**{status_badge}** : {detail_msg} 👉 주의! 스마트스토어 품절 처리 및 블로그 링크 수정이 필요합니다.")
            else:
                st.warning(f"**{status_badge}** : {detail_msg} 👉 링크를 직접 눌러 재고를 확인하세요: [도매처 바로가기]({w_url})")

        st.markdown("---")
        st.markdown("### 🌟 [네이버 블로그/카페 전용] 스마트스토어 상품 홍보 HTML 카드")
        st.write("기존 앱처럼 아래 코드를 복사(`Ctrl + C`)해 네이버 블로그나 카페 글쓰기(HTML 모드 또는 기본 에디터)에 붙여넣어 홍보용 배너로 활용하세요!")

        blog_promo_html = f"""
<div style="background-color:#ffffff; border:2px solid #03c75a; padding:22px; border-radius:12px; font-family:sans-serif; max-width:650px; margin:15px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
    <h3 style="color:#03c75a; text-align:center; margin-top:0; margin-bottom:12px;">🛍️ 스마트스토어 추천 상품 안내</h3>
    <hr style="border:1px solid #f0f0f0; margin-bottom:15px;">
    <p style="font-size:16px; margin:8px 0;"><b>📦 상품명:</b> {p_name}</p>
    <p style="font-size:15px; margin:8px 0;"><b>✨ 핵심 포인트:</b> {p_point}</p>
    <p style="font-size:16px; margin:8px 0;"><b>🏷️ 특별 할인가:</b> <span style="color:#e63946; font-weight:bold; font-size:18px;">{s_price:,}원</span></p>
    <div style="text-align:center; margin-top:20px;">
        <a href="{s_url}" target="_blank" style="background-color:#03c75a; color:#ffffff; padding:12px 28px; text-decoration:none; border-radius:6px; font-weight:bold; font-size:15px; display:inline-block;">👉 네이버 스마트스토어에서 상세 보기</a>
    </div>
</div>
"""
        st.code(blog_promo_html, language="html")

    # ------------------------------------------
    # TAB 3: 구글 시트 원본 데이터
    # ------------------------------------------
    with tab3:
        st.subheader("📊 구글 시트 등록 상품 원본 데이터")
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"앱 실행 중 오류가 발생했습니다. 상세 에러: {e}")
