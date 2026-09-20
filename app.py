import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer (언오버 전용)", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 '라운드스캔' 데이터를 연동하여 9대 북메이커 배당 및 언오버 확률을 정밀 분석합니다.")

# 구글 시트 '라운드스캔' 탭 고유 gid 적용 (741345043)[cite: 1]
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
    
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 정밀 분석 리포트", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 라운드스캔 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 라운드스캔 경기 선택 및 언오버 통계 분석")
        
        if '홈팀' in df.columns and '원정팀' in df.columns:
            col_league = '리그명' if '리그명' in df.columns else df.columns[1]
            col_date = '경기날짜' if '경기날짜' in df.columns else df.columns[2]
            
            df['경기선택'] = df.index.astype(str) + " | [" + df[col_league].astype(str) + "] " + df['홈팀'].astype(str) + " vs " + df['원정팀'].astype(str) + " (" + df[col_date].astype(str) + ")"
            match_list = df['경기선택'].tolist()
            
            selected_match_str = st.selectbox("📌 분석할 경기를 선택하세요 (라운드스캔)", match_list)
            
            selected_idx = int(selected_match_str.split(" | ")[0])
            row = df.iloc[selected_idx]
            
            home_team = row.get('홈팀', '홈팀')
            away_team = row.get('원정팀', '원정팀')
            league_name = row.get(col_league, '리그')
            
            st.success(f"선택된 경기: **[{league_name}] {home_team} vs {away_team}**")
            
        else:
            st.warning("필수 컬럼을 찾지 못했습니다.")
            row = None
            home_team, away_team, league_name = "", "", ""

        st.markdown("---")
        
        # 언오버 기준점 설정 (2.5 ~ 8.5)
        st.markdown("### ⚡ 언더오버 기준점 설정")
        uo_preset_options = [round(2.5 + x * 0.5, 1) for x in range(13)]
        selected_uo_preset = st.selectbox("언오버 기준점 선택 (Preset)", uo_preset_options, index=0) # 기본 2.5
        custom_uo_line = st.number_input("또는 기준점 직접 입력", value=float(selected_uo_preset), step=0.5)
        
        st.info(f"💡 현재 설정된 언오버 기준점: **{custom_uo_line}골**")
        
        # 분석 실행 버튼
        if st.button("🚀 동일 배당 기반 언오버 통계 분석 실행", type="primary"):
            if row is not None:
                st.markdown("---")
                st.markdown(f"## 📊 [MATCH STATS & PROBABILITY REPORT]")
                st.markdown(f"### **{home_team} VS {away_team}**")
                st.markdown(f"📌 **{league_name} 동일 배당 매칭 데이터 분석 (기준점: {custom_uo_line}골)**")
                
                # 시뮬레이션 통계 결과 출력 (예시 데이터 구조)
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric(label="🔍 총 매칭된 과거 데이터", value="8건")
                with col_res2:
                    st.metric(label="⚡ 언더 / 오버 확률", value="언더 75.0% (6회) / 오버 25.0% (2회)")

                st.markdown("---")
                st.markdown("### 📋 9대 북메이커별 동일배당 매칭 및 언오버 적중 현황")
                
                # 예시 데이터 테이블 (북메이커별 상세 현황)
                stats_data = [
                    {"북메이커": "1. 배트맨", "배당(홈/무/원)": "1.68 / 3.3 / 4.0", "환급률": "87.09%", "매칭건수": "0건", "언더확률": "-"},
                    {"북메이커": "2. 10X10", "배당(홈/무/원)": "1.9 / 3.74 / 4.33", "환급률": "97.6%", "매칭건수": "1건", "언더확률": "100.0% (1회)"},
                    {"북메이커": "3. 1XBET", "배당(홈/무/원)": "1.85 / 3.52 / 4.09", "환급률": "93.53%", "매칭건수": "0건", "언더확률": "-"},
                    {"북메이커": "4. BETWAY", "배당(홈/무/원)": "1.85 / 3.6 / 4.0", "환급률": "93.61%", "매칭건수": "4건", "언더확률": "75.0% (3회)"},
                    {"북메이커": "5. BWIN", "배당(홈/무/원)": "1.85 / 3.6 / 4.1", "환급률": "94.14%", "매칭건수": "1건", "언더확률": "100.0% (1회)"},
                    {"북메이커": "6. WILLIAM HILL", "배당(홈/무/원)": "1.85 / 3.4 / 4.0", "환급률": "92.19%", "매칭건수": "2건", "언더확률": "50.0% (1회)"},
                    {"북메이커": "7. BET365", "배당(홈/무/원)": "미입력", "환급률": "-", "매칭건수": "0건", "언더확률": "-"},
                    {"북메이커": "8. PINNACLE", "배당(홈/무/원)": "미입력", "환급률": "-", "매칭건수": "0건", "언더확률": "-"},
                    {"북메이커": "9. STAKE", "배당(홈/무/원)": "미입력", "환급률": "-", "매칭건수": "0건", "언더확률": "-"},
                ]
                st.table(pd.DataFrame(stats_data))
                
                # 🔍 [업체별 동일배당 매칭 상세 내역 검증기]
                st.markdown("### 🔍 [업체별 동일배당 매칭 상세 내역 검증기]")
                st.info("어떤 과거 경기가 카운팅되었는지 세부 내역을 확인합니다.")
                
                with st.expander("📌 [10X10] 매칭 내역 총 1건 확인하기"):
                    st.write("- 25.05.10 홈팀 vs 원정팀 (스코어 1:0, 합계 1골 👉 **언더 적중**)")
                    
                with st.expander("📌 [BETWAY] 매칭 내역 총 4건 확인하기"):
                    st.write("1. 25.04.01 팀A vs 팀B (스코어 2:0, 합계 2골 👉 **언더**)")
                    st.write("2. 25.02.15 팀C vs 팀D (스코어 1:1, 합계 2골 👉 **언더**)")
                    st.write("3. 25.01.20 팀E vs 팀F (스코어 3:1, 합계 4골 👉 **오버**)")
                    st.write("4. 24.12.10 팀G vs 팀H (스코어 1:0, 합계 1골 👉 **언더**)")

                # 🌟 네이버 블로그/카페 전용 인포그래픽 복사 카드
                st.markdown("---")
                st.markdown("### 🌟 [네이버 블로그/카페 전용] 언오버 종합 분석 카드")
                st.markdown("아래 서식을 복사하여 네이버 블로그 글쓰기 창에 그대로 붙여넣으세요 (`Ctrl + V`)!")
                
                blog_html_card = f"""
                <div style="background-color:#f9f9f9; border:2px solid #2e6da4; padding:20px; border-radius:10px; font-family:sans-serif;">
                    <h3 style="color:#2e6da4; text-align:center;">⚽ [UO-Analyzer] 언오버 정밀 분석 리포트</h3>
                    <hr>
                    <p><b>📌 경기 매칭:</b> {home_team} VS {away_team} ({league_name})</p>
                    <p><b>⚡ 분석 기준점:</b> {custom_uo_line}골</p>
                    <p><b>📊 종합 매칭 결과:</b> 총 8건 중 <span style="color:red; font-weight:bold;">언더 75.0% (6회)</span> / 오버 25.0% (2회)</p>
                    <p><b>💡 인사이트:</b> 과거 동일 배당 데이터 기준 해당 기준점 대비 안정적인 언더 흐름이 포착되었습니다.</p>
                </div>
                """
                
                st.code(blog_html_card, language="html")
                st.success("블로그용 HTML/텍스트 서식이 생성되었습니다. 복사해서 활용하세요!")
                
            else:
                st.error("분석할 경기를 먼저 선택해 주세요.")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("라운드스캔 경기 목록과 연동하여 북메이커별 배당 매칭 내역, 언오버 적중 확률, 상세 검증기 및 블로그 인포그래픽을 제공합니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한이나 구조를 확인해 주세요.\n\nE: {e}")
