import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 데이터를 연동하여 언오버 경기를 분석하는 대시보드입니다.")

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
        st.subheader("🔍 라운드스캔 경기 선택 및 언오버 분석")
        
        # 1. 경기 목록 구성 (컬럼명에 따라 '홈팀', '원정팀' 등이 있다고 가정, 데이터에 맞춰 유연하게 처리)
        # 만약 시트에 '홈팀', '원정팀' 또는 경기명을 조합할 수 있는 컬럼이 있다면 이를 활용합니다.
        # 예시로 '홈팀', '원정팀' 컬럼이 존재할 경우를 대비한 코드입니다.
        if '홈팀' in df.columns and '원정팀' in df.columns:
            df['경기선택'] = df.index.astype(str) + " | " + df.get('리그명', '') + " : " + df['홈팀'] + " vs " + df['원정팀']
            match_list = df['경기선택'].tolist()
            
            selected_match_str = st.selectbox("📌 분석할 경기를 선택하세요 (라운드스캔)", match_list)
            
            # 선택된 행 추출
            selected_idx = int(selected_match_str.split(" | ")[0])
            selected_row = df.iloc[selected_idx]
            
            st.success(f"선택된 경기: **{selected_row.get('홈팀', '')} vs {selected_row.get('원정팀', '')}**")
            
            # 선택된 경기 상세 정보 표시
            st.markdown("#### 📋 선택된 경기 상세 정보")
            st.json(selected_row.to_dict())
            
        else:
            st.warning("구글 시트 데이터에 '홈팀' 또는 '원정팀' 컬럼이 감지되지 않았습니다. 원본 데이터 탭에서 컬럼명을 확인해 주세요.")
            selected_row = None

        st.markdown("---")
        
        # 2. 언오버 기준점 설정 (-5.5 ~ +5.5 및 직접 입력)
        st.markdown("### 🎯 언오버 기준점 설정")
        col_preset, col_custom = st.columns(2)
        
        with col_preset:
            preset_options = [round(x * 0.5, 1) for x in range(-11, 12)]
            selected_preset = st.selectbox("기준점 선택 (Preset)", preset_options, index=15) # 기본 2.0~2.5 부근
            
        with col_custom:
            custom_line = st.number_input("또는 기준점 직접 입력 (-5.5 ~ +5.5)", value=float(selected_preset), step=0.5)
        
        st.info(f"💡 현재 설정된 분석 기준점: **{custom_line}**")
        
        # 3. 분석 실행 버튼
        if st.button("🚀 언오버 통계 분석 실행", type="primary"):
            if selected_row is not None:
                st.success(f"[{selected_row.get('홈팀', '')} vs {selected_row.get('원정팀', '')}] 경기에 대해 기준점 {custom_line} 기준 분석을 수행합니다!")
                # 추후 분석 로직 추가 자리
            else:
                st.error("분석할 경기를 먼저 올바르게 선택해 주세요.")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("구글 시트의 라운드스캔 데이터를 연동하여 경기를 선택하고, 언오버 기준점(-5.5 ~ +5.5)을 설정하여 분석하는 공간입니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한이나 구조를 확인해 주세요.\n\nE: {e}")
