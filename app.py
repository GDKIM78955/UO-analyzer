import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 '라운드스캔' 데이터를 연동하여 경기를 선택하고, 2.5~8.5 언오버 기준점에 따른 통계를 분석하는 대시보드입니다.")

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
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 분석 (라운드스캔)", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 라운드스캔 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 라운드스캔 경기 선택 및 배당 자동 연동")
        
        if '홈팀' in df.columns and '원정팀' in df.columns:
            col_league = '리그명' if '리그명' in df.columns else df.columns[1]
            col_date = '경기날짜' if '경기날짜' in df.columns else df.columns[2]
            
            # 보기 편하게 경기 선택용 문자열 조합
            df['경기선택'] = df.index.astype(str) + " | [" + df[col_league].astype(str) + "] " + df['홈팀'].astype(str) + " vs " + df['원정팀'].astype(str) + " (" + df[col_date].astype(str) + ")"
            match_list = df['경기선택'].tolist()
            
            selected_match_str = st.selectbox("📌 분석할 경기를 선택하세요 (라운드스캔)", match_list)
            
            # 선택된 행(경기) 추출
            selected_idx = int(selected_match_str.split(" | ")[0])
            row = df.iloc[selected_idx]
            
            st.success(f"선택된 경기: **[{row.get(col_league, '')}] {row.get('홈팀', '')} vs {row.get('원정팀', '')}** (일시: {row.get(col_date, '')})")
            
            # 9대 북메이커 배당 자동 연동 정보 표시
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
            
            # 3열 구조로 깔끔하게 북메이커 배당 배치
            for i in range(0, len(bookmakers), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(bookmakers):
                        bm_name, h_col, d_col, a_col = bookmakers[i + j]
                        with cols[j]:
                            st.markdown(f"**{bm_name.upper()}**")
                            h_val = row.get(h_col, '-')
                            d_val = row.get(d_col, '-')
                            a_val = row.get(a_col, '-')
                            st.write(f"홈: `{h_val}` | 무: `{d_val}` | 원정: `{a_val}`")
            
        else:
            st.warning(f"구글 시트에서 '홈팀' 또는 '원정팀' 컬럼을 찾지 못했습니다.")
            row = None

        st.markdown("---")
        
        # 언오버 기준점 설정 (2.5 ~ 8.5 0.5단위 및 직접 입력)
        st.markdown("### 🎯 언오버 분석 기준점 설정")
        col_preset, col_custom = st.columns(2)
        
        with col_preset:
            # 2.5부터 8.5까지 0.5 단위 리스트 생성
            uo_preset_options = [round(2.5 + x * 0.5, 1) for x in range(13)] # 2.5, 3.0, ..., 8.5
            selected_uo_preset = st.selectbox("언오버 기준점 선택 (Preset)", uo_preset_options, index=0) # 기본 2.5
            
        with col_custom:
            custom_uo_line = st.number_input("또는 언오버 기준점 직접 입력 (2.5 ~ 8.5)", value=float(selected_uo_preset), min_value=0.5, max_value=15.0, step=0.5)
        
        st.info(f"💡 현재 설정된 언오버 분석 기준점: **{custom_uo_line}골**")
        
        # 분석 실행 버튼
        if st.button("🚀 동일 배당 기반 언오버 통계 분석 실행", type="primary"):
            if row is not None:
                st.success(f"[{row.get('홈팀', '')} vs {row.get('원정팀', '')}] 경기의 북메이커 배당과 기준점({custom_uo_line}골)을 매칭하여 과거 동일 배당 통계 분석을 수행합니다!")
                # 추후 각 업체별 배당과 과거 점수합계를 매칭하는 통계 로직이 들어갈 자리입니다.
            else:
                st.error("분석할 경기를 먼저 선택해 주세요.")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("라운드스캔 경기 목록과 9대 북메이커 배당을 자동 연동하고, 2.5 ~ 8.5 언오버 기준점에 따른 과거 동일 배당 매칭 통계를 산출합니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한이나 구조를 확인해 주세요.\n\nE: {e}")
