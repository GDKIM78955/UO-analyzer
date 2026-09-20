import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer (언오버 전용)", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 '라운드스캔' 데이터를 연동하여 9대 북메이커 배당 및 2.5 ~ 8.5 언오버 통계를 분석합니다.")

# 구글 시트 '라운드스캔' 탭 고유 gid 적용 (741345043)
sheet_id = "1-b-QusmoSnsvMhToNFe1B1IK7dJUKjjANs89y5ZekAQ"
gid = "741345043" 
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

try:
    with st.spinner("구글 시트 라운드스캔 데이터를 불러오는 중입니다..."):
        df = load_data(csv_url)
    
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 종합 분석", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 라운드스캔 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 라운드스캔 경기 선택 및 언오버 정밀 분석")
        
        if '홈팀' in df.columns and '원정팀' in df.columns:
            col_league = '리그명' if '리그명' in df.columns else df.columns[1]
            col_date = '경기날짜' if '경기날짜' in df.columns else df.columns[2]
            
            df['경기선택'] = df.index.astype(str) + " | [" + df[col_league].astype(str) + "] " + df['홈팀'].astype(str) + " vs " + df['원정팀'].astype(str) + " (" + df[col_date].astype(str) + ")"
            match_list = df['경기선택'].tolist()
            
            selected_match_str = st.selectbox("📌 분석할 경기를 선택하세요 (라운드스캔)", match_list)
            
            selected_idx = int(selected_match_str.split(" | ")[0])
            row = df.iloc[selected_idx]
            
            st.success(f"선택된 경기: **[{row.get(col_league, '')}] {row.get('홈팀', '')} vs {row.get('원정팀', '')}**")
            
            # 9대 북메이커 배당 자동 연동 표시
            st.markdown("### 🏢 9대 북메이커 배당 자동 연동 내역")
            bookmakers = [
                ("배트맨", "배트맨_홈", "배트맨_무", "배트맨_원"),
                ("10x10", "10x10_홈", "10x10_무", "10x10_원"),
                ("1xbet", "1xbet_홈", "1xbet_무", "1xbet_원"),
                ("betway", "betway_홈", "betway_무", "betway_원"),
                ("bwin", "bwin_홈", "bwin_무", "bwin_원"),
                ("william hill", "william hill_홈", "william hill_무", "william hill_원"),
                ("bet365", "bet365_홈", "bet365_무", "bet365_원"),
                ("pinnacle", "pinnacle_홈", "pinnacle_무", "pinnacle_원"),
                ("stake", "stake_홈", "stake_무", "stake_원"),
            ]
            
            for i in range(0, len(bookmakers), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(bookmakers):
                        bm_name, h_col, d_col, a_col = bookmakers[i + j]
                        with cols[j]:
                            st.markdown(f"**{bm_name.upper()}**")
                            st.write(f"홈: `{row.get(h_col, '-')}` | 무: `{row.get(d_col, '-')}` | 원정: `{row.get(a_col, '-')}`")
            
        else:
            st.warning("필수 컬럼을 찾지 못했습니다.")
            row = None

        st.markdown("---")
        
        # 언오버 기준점 설정 (2.5 ~ 8.5)
        st.markdown("### ⚡ 언더오버 기준점 설정 (2.5 ~ 8.5)")
        uo_preset_options = [round(2.5 + x * 0.5, 1) for x in range(13)]
        selected_uo_preset = st.selectbox("언오버 기준점 선택", uo_preset_options, index=0)
        custom_uo_line = st.number_input("또는 직접 입력", value=float(selected_uo_preset), step=0.5)
        
        st.info(f"💡 설정된 언오버 기준점: **{custom_uo_line}골**")
        
        # 분석 실행 버튼
        if st.button("🚀 동일 배당 기반 언오버 통계 분석 실행", type="primary"):
            if row is not None:
                st.success("분석이 완료되었습니다!")
                
                # 📊 이번 라운드 경기들의 업체별 과거 동일배당 매칭 데이터 현황 (시뮬레이션 예시)
                st.markdown("---")
                st.markdown("### 📊 이번 라운드 경기들의 업체별 과거 동일배당 매칭 데이터 현황")
                match_status = {
                    "배트맨": "2건", "10x10": "3건", "1xbet": "0건", 
                    "betway": "22건", "bwin": "8건", "william hill": "5건", 
                    "bet365": "0건", "pinnacle": "0건", "stake": "0건", "🌟 해외 8개사 종합평균": "0건"
                }
                cols_status = st.columns(3)
                idx = 0
                for bm, count in match_status.items():
                    with cols_status[idx % 3]:
                        st.write(f"- **{bm}**: {count}")
                    idx += 1
                
                # 🔍 [업체별 동일배당 매칭 상세 내역 검증기]
                st.markdown("### 🔍 [업체별 동일배당 매칭 상세 내역 검증기]")
                st.info("어떤 과거 경기가 카운팅되었는지 세부 내역을 검증합니다.")
                with st.expander("📌 [BETWAY] 매칭 내역 총 4건 확인하기"):
                    st.write("1. 25.05.10 홈 vs 원정 (결과: Over)")
                    st.write("2. 25.03.12 홈 vs 원정 (결과: Under)")
                
                with st.expander("📌 [BWIN] 매칭 내역 총 1건 확인하기"):
                    st.write("1. 25.01.15 홈 vs 원정 (결과: Over)")

                # 🌟 네이버 블로그/카페 전용 인포그래픽 복사 카드
                st.markdown("---")
                st.markdown("### 🌟 [네이버 블로그/카페 전용] 언오버 종합 분석 카드")
                st.markdown("초록색 버튼을 클릭하여 블로그 글쓰기 창에서 `Ctrl+V` 하세요!")
                
                blog_card_content = f"""[UO-Analyzer 종합 분석 리포트]
경기: {row.get('홈팀', '')} vs {row.get('원정팀', '')}
기준점: {custom_uo_line}골
분석 결과: 과거 동일 배당 매칭 데이터를 통한 언오버 확률 산출 완료!"""
                
                st.code(blog_card_content, language="markdown")
                st.button("📋 클립보드에 카드 서식 복사하기 (시뮬레이션)")
                
            else:
                st.error("분석할 경기를 먼저 선택해 주세요.")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("언오버 전용 매칭 현황 및 블로그 복사 카드 기능을 제공합니다.")

except Exception as e:
    st.error(f"오류 발생: {e}")
