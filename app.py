import streamlit as st
import pandas as pd

st.title("⚽ UO-Analyzer (언오버 전용 분석 앱)")
st.write("구글 시트 데이터를 연동하여 언오버 경기를 분석하는 대시보드입니다.")

# 구글 시트 CSV 내보내기 주소 변환
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
    
    st.success("데이터를 성공적으로 불러왔습니다!")
    
    # 데이터 미리보기
    st.subheader("📊 구글 시트 원본 데이터")
    st.dataframe(df)

except Exception as e:
    st.error(f"데이터를 불러오는 데 실패했습니다. 구글 시트가 '링크가 있는 모든 사용자에게 공개'되어 있는지 확인해 주세요.\n\n에러 내용: {e}")
