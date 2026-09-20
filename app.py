import streamlit as st
import pandas as pd

st.set_page_config(page_title="UO-Analyzer", layout="wide")

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 데이터를 연동하여 언오버 기준점 및 9대 북메이커 배당을 분석하는 대시보드입니다.")

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
    tab1, tab2, tab3 = st.tabs(["📊 원본 데이터", "🔍 언오버 배당 및 기준점 분석", "⚙️ 설정 및 안내"])
    
    with tab1:
        st.subheader("📊 구글 시트 원본 데이터")
        st.dataframe(df, use_container_width=True)
    
    with tab2:
        st.subheader("🎯 언오버 기준점 및 9대 북메이커 배당 입력")
        
        # 1. 언오버 기준점 설정 (-5.5 ~ +5.5 및 직접 입력)
        st.markdown("### 1️⃣ 언오버 기준점 설정")
        col_preset, col_custom = st.columns(2)
        
        with col_preset:
            preset_options = [round(x * 0.5, 1) for x in range(-11, 12)]
            selected_preset = st.selectbox("기준점 선택 (Preset)", preset_options, index=15) # 기본 2.0~2.5 부근
            
        with col_custom:
            custom_line = st.number_input("또는 기준점 직접 입력 (-5.5 ~ +5.5)", value=float(selected_preset), step=0.5)
        
        st.info(f"💡 현재 선택된 언오버 분석 기준점: **{custom_line}**")
        
        st.markdown("---")
        
        # 2. 9대 북메이커 언오버 배당 입력 폼
        st.markdown("### 2️⃣ 9대 북메이커 언오버 배당 입력")
        bookmakers = [
            "배트맨", "10X10", "1XBET", "BETWAY", "BWIN", 
            "WILLIAM HILL", "BET365", "PINNACLE", "STAKE"
        ]
        
        # 3열 구조로 북메이커 입력창 배치
        odds_data = {}
        for i in range(0, len(bookmakers), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(bookmakers):
                    bm = bookmakers[i + j]
                    with cols[j]:
                        st.markdown(f"**[{i+j+1}] {bm}**")
                        over_odd = st.number_input(f"{bm} 오버(Over) 배당", value=1.85, step=0.01, key=f"over_{bm}")
                        under_odd = st.number_input(f"{bm} 언더(Under) 배당", value=1.85, step=0.01, key=f"under_{bm}")
                        odds_data[bm] = {"over": over_odd, "under": under_odd}
        
        st.markdown("---")
        
        # 3. 분석 실행 버튼 및 결과 영역
        if st.button("🚀 동일 배당 및 언오버 확률 통계 분석 실행", type="primary"):
            st.success("분석이 완료되었습니다! (선택하신 기준점과 배당을 바탕으로 한 통계 결과가 여기에 출력됩니다.)")
            
            # 추후 블로그 복사 카드나 상세 통계표가 들어갈 자리
            st.markdown("#### 📊 [카드 1] 언오버 동일 배당 매칭 통계 인포그래픽")
            st.code("여기에 네이버 블로그/카페용 마크다운 또는 HTML 결과가 출력됩니다.", language="markdown")
            
    with tab3:
        st.subheader("⚙️ 앱 이용 안내")
        st.write("이 앱은 기존 승무패 구조에서 전환된 **언오버 전용 분석 시스템**입니다.")
        st.markdown("- **기준점 설정**: -5.5 ~ +5.5 범위 선택 및 직접 입력 지원")
        st.markdown("- **9대 북메이커**: 각사별 오버/언더 배당 입력 및 종합 분석 제공")

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 시트 권한을 확인해 주세요.\n\nE: {e}")
