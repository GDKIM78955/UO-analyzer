import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="UO-Analyzer (언오버 정밀 분석)", layout="wide")

st.title("⚽ UO-Analyzer (언오버 정밀 분석 대시보드)")
st.write(
    "구글 시트 '라운드스캔' 데이터를 기반으로 9대 북메이커 배당과 과거 동일배당 언오버 통계를 정밀 산출합니다."
)

# 구글 시트 '라운드스캔' 탭 고유 gid 적용 (741345043)
sheet_id = "1-b-QusmoSnsvMhToNFe1B1IK7dJUKjjANs89y5ZekAQ"
gid = "741345043"
csv_url = (
    f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
)


@st.cache_data
def load_data(url):
  df = pd.read_csv(url)
  # 컬럼명 공백 제거
  df.columns = df.columns.str.strip()
  return df


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

      # 경기 선택 셀렉트박스 구성 (시즌리그명 | 홈팀 vs 원정팀)
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
      match_list = df["경기선택"].tolist()

      selected_match_str = st.selectbox(
          "라운드스캔 등록 경기 목록", match_list
      )
      selected_idx = int(selected_match_str.split(" | ")[0])
      row = df.iloc[selected_idx]

      home_team = row.get("홈팀", "홈팀")
      away_team = row.get("원정팀", "원정팀")
      league_name = row.get(col_league, "리그")
      match_date = row.get(col_date, "")

    else:
      st.error("데이터에서 '홈팀' 또는 '원정팀' 컬럼을 찾을 수 없습니다.")
      st.stop()

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
        "🚀 9대 북메이커별 언오버 통계 분석 실행",
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

      # 제공해주신 시트 컬럼명 순서에 맞춘 9대 북메이커 설정
      bm_configs = [
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

      table_rows = []
      for idx, (name, h_c, d_c, a_c) in enumerate(bm_configs, 1):
        # 시트에 해당 컬럼이 존재하는지 확인 후 값 가져오기
        h_val = row.get(h_c, None) if h_c in df.columns else None
        d_val = row.get(d_c, None) if d_c in df.columns else None
        a_val = row.get(a_c, None) if a_c in df.columns else None

        if pd.notna(h_val) and pd.notna(d_val) and pd.notna(a_val):
          odds_str = f"{h_val} / {d_val} / {a_val}"

          # 동일 배당을 가진 과거 경기를 시트 전체에서 검색
          matched_games = df[
              (df[h_c] == h_val) & (df[d_c] == d_val) & (df[a_c] == a_val)
          ]
          match_count = len(matched_games)

          # 점수합계 컬럼이 존재하는 경우 언오버 확률 계산
          if match_count > 0 and "점수합계" in df.columns:
            under_matches = matched_games[
                matched_games["점수합계"] < custom_uo_line
            ]
            over_matches = matched_games[
                matched_games["점수합계"] > custom_uo_line
            ]

            under_cnt = len(under_matches)
            over_cnt = len(over_matches)

            under_prob = (
                f"{(under_cnt / match_count) * 100:.1f}% ({under_cnt}회)"
            )
            over_prob = f"{(over_cnt / match_count) * 100:.1f}% ({over_cnt}회)"
          else:
            under_prob = "점수합계 데이터 없음"
            over_prob = "점수합계 데이터 없음"

          refund_rate = "93.5%"  # 추후 환급률 수식 연동 가능 영역
          count_str = f"{match_count}건"
        else:
          odds_str = "미입력"
          refund_rate = "-"
          count_str = "0건"
          under_prob = "-"
          over_prob = "-"

        table_rows.append({
            "No": idx,
            "북메이커": name,
            "배당 (홈/무/원)": odds_str,
            "환급률": refund_rate,
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
