import pandas as pd
import streamlit as st

st.set_page_config(page_title="UO-Analyzer (언오버 정밀 분석)", layout="wide")

st.title("⚽ UO-Analyzer (언오버 정밀 분석 대시보드)")
st.write(
    "구글 시트 '라운드스캔' 데이터를 기반으로 9대 북메이커 배당과 과거"
    " 동일배당 언오버 통계를 정밀 산출합니다."
)

# 구글 시트 '라운드스캔' 탭 고유 gid 적용 (741345043)
sheet_id = "1-b-QusmoSnsvMhToNFe1B1IK7dJUKjjANs89y5ZekAQ"
gid = "741345043"
csv_url = (
    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
)


@st.cache_data(ttl=300, show_spinner=False)
def load_data(url):
  df = pd.read_csv(url)
  df.columns = df.columns.str.strip()
  return df


BOOKMAKERS = [
    "배트맨",
    "10x10",
    "1xbet",
    "betway",
    "bwin",
    "william hill",
    "bet365",
    "pinnacle",
    "stake",
]

try:
  with st.spinner("구글 시트에서 데이터를 불러오는 중입니다..."):
    df = load_data(csv_url)

  tab1, tab2 = st.tabs(["🔍 언오버 정밀 분석", "📊 라운드스캔 원본 데이터"])

  with tab1:
    st.subheader("📌 분석할 경기 선택 및 기준점 설정")

    if "홈팀" in df.columns and "원정팀" in df.columns:
      col_league = (
          "시즌리그명" if "시즌리그명" in df.columns else df.columns[0]
      )
      col_date = "경기날짜" if "경기날짜" in df.columns else df.columns[1]

      # 경기 선택 셀렉트박스 구성
      df["경기선택"] = (
          df.index.astype(str)
          + " | ["
          + df[col_league].astype(str)
          + "] "
          + df["홈팀"].astype(str)
          + " vs "
          + df["원정팀"].astype(str)
          + " ("
          + df[col_date].astype(str)
          + ")"
      )
      match_list = ["➕ [직접 선택 안 함 / 수동 확인]"] + df["경기선택"].tolist()

      selected_match_str = st.selectbox(
          "라운드스캔 등록 경기 목록 (선택 시 아래 배당 자동 연동)", match_list
      )

      # 선택된 경기가 있을 경우 해당 행 데이터 추출
      if selected_match_str != "➕ [직접 선택 안 함 / 수동 확인]":
        selected_idx = int(selected_match_str.split(" | ")[0])
        row = df.iloc[selected_idx]
      else:
        row = None

      home_team = (
          row.get("홈팀", "홈팀")
          if row is not None
          else st.text_input("🏠 홈팀명", value="본머스")
      )
      away_team = (
          row.get("원정팀", "원정팀")
          if row is not None
          else st.text_input("🚗 원정팀명", value="리버풀")
      )
      league_name = (
          row.get(col_league, "리그") if row is not None else "PL"
      )
      match_date = row.get(col_date, "") if row is not None else ""

    else:
      st.error("데이터에서 '홈팀' 또는 '원정팀' 컬럼을 찾을 수 없습니다.")
      st.stop()

    st.markdown("---")
    st.markdown("##### 🏢 9대 북메이커 배당 확인 및 세팅")

    odds_inputs = {}
    for i in range(0, len(BOOKMAKERS), 3):
      cols = st.columns(3)
      for j in range(3):
        idx = i + j
        if idx < len(BOOKMAKERS):
          bm = BOOKMAKERS[idx]
          with cols[j]:
            with st.container(border=True):
              st.markdown(f"**[{idx+1}] {bm.upper()}**")
              oh, od, oa = st.columns(3)

              # 시트에서 해당 업체의 배당 값 가져오기 (없으면 0.0)
              default_h = (
                  float(row.get(f"{bm}_홈", 0.0))
                  if row is not None and f"{bm}_홈" in df.columns
                  else 0.0
              )
              default_d = (
                  float(row.get(f"{bm}_무", 0.0))
                  if row is not None and f"{bm}_무" in df.columns
                  else 0.0
              )
              default_a = (
                  float(row.get(f"{bm}_원", 0.0))
                  if row is not None and f"{bm}_원" in df.columns
                  else 0.0
              )

              h_val = oh.number_input(
                  "홈",
                  value=default_h if default_h > 0 else 0.0,
                  step=0.01,
                  min_value=0.0,
                  key=f"uo_{bm}_h_{selected_match_str}",
              )
              d_val = od.number_input(
                  "무",
                  value=default_d if default_d > 0 else 0.0,
                  step=0.01,
                  min_value=0.0,
                  key=f"uo_{bm}_d_{selected_match_str}",
              )
              a_val = oa.number_input(
                  "원정",
                  value=default_a if default_a > 0 else 0.0,
                  step=0.01,
                  min_value=0.0,
                  key=f"uo_{bm}_a_{selected_match_str}",
              )
              odds_inputs[bm] = (h_val, d_val, a_val)

    st.markdown("---")

    # 언오버 기준점 설정 (2.5 ~ 8.5)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
      uo_preset_options = [round(2.5 + x * 0.5, 1) for x in range(13)]
      selected_uo_preset = st.selectbox(
          "⚡ 언오버 기준점 선택", uo_preset_options, index=0
      )
    with col_s2:
      custom_uo_line = st.number_input(
          "또는 직접 입력 (골)", value=float(selected_uo_preset), step=0.5
      )

    st.markdown("---")

    # 분석 실행 버튼
    if st.button(
        "🚀 9대 북메이커별 동일배당 언오버 정밀 분석 실행",
        type="primary",
        use_container_width=True,
    ):
      st.markdown(f"## 📊 [MATCH STATS & PROBABILITY REPORT]")
      st.markdown(
          f"### **{home_team} VS {away_team}** `[{league_name} /"
          f" {match_date}]`"
      )
      st.info(
          f"🎯 **적용된 언오버 기준점: {custom_uo_line}골** (기준점 초과 시 오버,"
          " 미만 시 언더)"
      )

      st.markdown("---")

      table_rows = []
      total_matches_count = 0
      total_over_count = 0
      total_under_count = 0

      for idx, bm in enumerate(BOOKMAKERS, 1):
        h, d, a = odds_inputs.get(bm, (0.0, 0.0, 0.0))

        if h > 1.0 and d > 1.0 and a > 1.0:
          odds_str = f"{h} / {d} / {a}"

          # 환급률 계산
          raw_inv = (1 / h) + (1 / d) + (1 / a)
          payout_rate = f"{(1 / raw_inv) * 100:.2f}%"

          # 라운드스캔 전체 시트에서 동일 배당을 가진 과거 경기 검색
          h_col, d_col, a_col = f"{bm}_홈", f"{bm}_무", f"{bm}_원"

          if h_col in df.columns and d_col in df.columns and a_col in df.columns:
            matched_games = df[
                (df[h_col] == h) & (df[d_col] == d) & (df[a_col] == a)
            ]
            match_count = len(matched_games)

            if match_count > 0 and "점수합계" in df.columns:
              under_matches = matched_games[
                  matched_games["점수합계"] < custom_uo_line
              ]
              over_matches = matched_games[
                  matched_games["점수합계"] > custom_uo_line
              ]

              under_cnt = len(under_matches)
              over_cnt = len(over_matches)

              total_matches_count += match_count
              total_over_count += over_cnt
              total_under_count += under_cnt

              under_prob = (
                  f"{(under_cnt / match_count) * 100:.1f}% ({under_cnt}회)"
              )
              over_prob = (
                  f"{(over_cnt / match_count) * 100:.1f}% ({over_cnt}회)"
              )
            else:
              under_prob = "점수합계 데이터 없음"
              over_prob = "점수합계 데이터 없음"
          else:
            match_count = 0
            under_prob = "컬럼 없음"
            over_prob = "컬럼 없음"

          count_str = f"{match_count}건"
        else:
          odds_str = "미입력"
          payout_rate = "-"
          count_str = "0건"
          under_prob = "-"
          over_prob = "-"

        table_rows.append({
            "No": idx,
            "북메이커": bm,
            "배당 (홈/무/원)": odds_str,
            "환급률": payout_rate,
            "매칭 건수": count_str,
            "언더 확률": under_prob,
            "오버 확률": over_prob,
        })

      df_stats = pd.DataFrame(table_rows)
      st.markdown(
          "### 📋 9대 북메이커별 동일배당 매칭 및 언오버 분석 현황표"
      )
      st.dataframe(df_stats, use_container_width=True, hide_index=True)

      # 네이버 블로그/카페 전용 복사 카드
      st.markdown("---")
      st.markdown(
          "### 🌟 [네이버 블로그/카페 전용] 언오버 종합 분석 인포그래픽 카드"
      )
      st.markdown(
          "아래 상자의 코드를 복사(`Ctrl + C`)하여 블로그 글쓰기 창에"
          " 붙여넣으세요!"
      )

      blog_html_card = f"""
            <div style="background-color:#ffffff; border:2px solid #2e6da4; padding:20px; border-radius:10px; font-family:sans-serif; max-width:700px; margin:0 auto;">
                <h3 style="color:#2e6da4; text-align:center; margin-top:0;">⚽ [UO-Analyzer] 언오버 정밀 분석 리포트</h3>
                <hr style="border:1px solid #eee;">
                <p><b>📌 대상 경기:</b> {home_team} VS {away_team} [{league_name}]</p>
                <p><b>⚡ 분석 기준점:</b> <span style="color:#d9534f; font-weight:bold;">{custom_uo_line}골 기준</span></p>
                <p><b>📊 분석 결과:</b> 라운드스캔 데이터 기반 9사 배당 매칭 및 언오버 확률 산출 완료</p>
                <p style="font-size:11px; color:#888; text-align:right; margin-bottom:0;">Generated by UO-Analyzer</p>
            </div>
            """

      st.code(blog_html_card, language="html")
      st.success("블로그용 HTML 카드가 성공적으로 생성되었습니다!")

  with tab2:
    st.subheader("📊 구글 시트 라운드스캔 원본 데이터")
    st.dataframe(df, use_container_width=True)

except Exception as e:
  st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 상세 에러: {e}")
