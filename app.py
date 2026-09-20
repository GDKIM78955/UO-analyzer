import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 라운드스캔 데이터를 연동하여 경기를 선택하고, 업체별 배당 및 언오버 기준점을 분석하는 대시보드입니다.")

# 구글 시트 데이터 로드 함수
sheet_id = "1-b-QusmoSnsvMhToNFe1B1IK7dJUKjjANs89y5ZekAQ"
gid = "1490461894"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    return df

try:
    with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
        df = load_data(csv_url)
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 분석 (라운드스캔)", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 라운드스캔 경기 선택 및 자동 배당 연동")
        
        # 1. 경기 목록 셀렉트박스 생성
        if '홈팀' in df.columns and '원정팀' in df.columns:
            df['경기선택'] = df.index.astype(str) + " | [" + df.get('리그명', '') + "] " + df['홈팀'] + " vs " + df['원정팀']
            match_list = df['경기선택'].tolist()
            
            selected_match_str = st.selectbox("📌 분석할 경기를 선택하세요 (라운드스캔)", match_list)
            
            # 선택된 행(경기) 추출
            selected_idx = int(selected_match_str.split(" | ")[0])
            row = df.iloc[selected_idx]
            
            st.success(f"선택된 경기: **[{row.get('리그명', '')}] {row.get('홈팀', '')} vs {row.get('원정팀', '')}** (날짜: {row.get('날짜', '')})")
            
            # 2. 구글 시트에 작성된 업체별 배당 자동 불러오기 표시
            st.markdown("### 🏢 구글 시트에 기록된 업체별 배당 자동 연동 내역")
            
            # 주요 업체 배당 컬럼이 시트에 존재할 경우 자동 추출하여 카드 형태로 보기 쉽게 배치
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🏟️ 베트맨")
                st.write(f"- 홈: {row.get('베트맨_홈', '정보 없음')}")
                st.write(f"- 무: {row.get('베트맨_무', '정보 없음')}")
                st.write(f"- 원정: {row.get('베트맨_원', '정보 없음')}")
                
            with col2:
                st.markdown("#### 📊 해당(기타) 배당")
                st.write(f"- 홈: {row.get('해당_홈', '정보 없음')}")
                st.write(f"- 무: {row.get('해당_무', '정보 없음')}")
                st.write(f"- 원정: {row.get('해당_원', '정보 없음')}")

            with col3:
                st.markdown("#### ⚽ 실제 경기 결과")
                st.write(f"- 홈스코어: {row.get('홈스코어', '-')}")
                st.write(f"- 원정스코어: {row.get('원정스코어', '-')}")
                st.write(f"- 점수합계: **{row.get('점수합계', '-')}**")

        else:
            st.warning("구글 시트 데이터에 '홈팀' 또는 '원정팀' 컬럼이 감지되지 않았습니다.")
            row = None

        st.markdown("---")
        
        # 3. 언오버 기준점 설정 (-5.5 ~ +5.5 및 직접 입력)
        st.markdown("### 🎯 언오버 분석 기준점 설정")
        col_preset, col_custom = st.columns(2)
        
        with col_preset:
            preset_options = [round(x * 0.5, 1) for x in range(-11, 12)]
            selected_preset = st.selectbox("기준점 선택 (Preset)", preset_options, index=15) # 기본 2.0~2.5 부근
            
        with col_custom:
            custom_line = st.number_input("또는 기준점 직접 입력 (-5.5 ~ +5.5)", value=float(selected_preset), step=0.5)
        
        st.info(f"💡 현재 설정된 언오버 분석 기준점: **{custom_line}**")
        
        # 4. 분석 실행 버튼
        if st.button("🚀 언오버 통계 분석 실행", type="primary"):
            if row is not None:
                st.success(f"[{row.get('홈팀', '')} vs {row.get('원정팀', '')}] 경기에 대한 기준점({custom_line}) 분석을 수행합니다!")
                
                # 점수합계와 기준점 비교 간단 시뮬레이션
                total_score = row.get('점수합계')
                if pd.notna(total_score):
                    result_uo = "Over (오버)" if total_score > custom_line else "Under (언더)"
                    st.metric(label="실제 점수합계 vs 기준점 결과", value=result_uo, delta=f"합계: {total_score}골")
                else:
                    st.info("해당 경기의 실제 점수합계 데이터가 아직 입력되지 않았습니다.")
            else:
                st.error("분석할 경기를 먼저 선택해 주세요.")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("구글 시트 라운드스캔 데이터와 연동되어, 경기를 선택하면 시트에 작성된 배당 및 결과가 자동으로 연동됩니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한이나 구조를 확인해 주세요.\n\nE: {e}")
