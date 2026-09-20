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
    
    # 탭 구성 (보기 편하게 분리)
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 분석", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🔍 언오버 기준점 통계 분석")
        
        # 기준점 선택 및 직접 입력 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            # -5.5부터 +5.5까지 0.5 단위 리스트 생성
            preset_options = [round(x * 0.5, 1) for x in range(-11, 12)]
            selected_preset = st.selectbox("기준점 선택 (Preset)", preset_options, index=11)
            
        with col2:
            custom_line = st.number_input("또는 기준점 직접 입력", value=float(selected_preset), step=0.5)
        
        st.info(f"현재 설정된 분석 기준점: **{custom_line}**")
        
        st.write("선택하신 기준점을 바탕으로 한 통계 및 매칭 결과가 여기에 표시됩니다.")
        
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("이 앱은 구글 시트와 연동되어 실시간으로 언오버 경기를 분석하는 도구입니다.")
        st.markdown("- **원본 데이터 탭**: 시트에 입력된 전체 데이터를 확인합니다.")
        st.markdown("- **언오버 분석 탭**: 원하는 기준(-5.5 ~ +5.5 및 직접 입력)을 통해 경기를 필터링하고 통계를 냅니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한을 확인해 주세요.\n\n에러 내용: {e}")
