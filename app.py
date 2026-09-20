import streamlit as st
import pandas as pd
import numpy as np
from database import load_sheet_data

def render_uo_analysis(spreadsheet_id, bookmakers, overseas_bookmakers, tol):
    st.subheader("⚽ UO-Analyzer: 9대 북메이커 배당 연동 & 언오버 정밀 분석")

    scanner_sheet_name = "라운드스캔"
    
    df_scan = pd.DataFrame()
    try:
        df_scan = load_sheet_data(scanner_sheet_name, spreadsheet_id)
    except Exception:
        pass
    
    def safe_flt(val, default):
        try:
            res = float(str(val).replace("%", "").strip())
            return res if res > 0 else default
        except:
            return default

    # 1. 라운드스캔 경기 선택 시 배당 자동 세팅 콜백
    def on_match_load():
        sel_match = st.session_state.get("sel_uo_match_loader", "➕ [직접 수동 입력하기]")
        if sel_match != "➕ [직접 수동 입력하기]":
            if not df_scan.empty:
                for _, r in df_scan.iterrows():
                    match_lbl = f"[{r.get('시즌리그명', r.get('리그명', ''))}] {r.get('홈팀', '')} vs {r.get('원정팀', '')} ({r.get('경기날짜', '')})"
                    if match_lbl == sel_match:
                        st.session_state.uo_target_league = str(r.get("시즌리그명", r.get("리그명", "PL")))
                        st.session_state.uo_home_team = str(r.get("홈팀", ""))
                        st.session_state.uo_away_team = str(r.get("원정팀", ""))
                        
                        # 배트맨 배당 세팅
                        st.session_state["uo_배트맨_h"] = float(safe_flt(r.get("배트맨_홈"), 0.0))
                        st.session_state["uo_배트맨_d"] = float(safe_flt(r.get("배트맨_무"), 0.0))
                        st.session_state["uo_배트맨_a"] = float(safe_flt(r.get("배트맨_원"), 0.0))
                        
                        # 해외 북메이커 배당 세팅
                        for obm in overseas_bookmakers:
                            st.session_state[f"uo_{obm}_h"] = float(safe_flt(r.get(f"{obm}_홈"), 0.0))
                            st.session_state[f"uo_{obm}_d"] = float(safe_flt(r.get(f"{obm}_무"), 0.0))
                            st.session_state[f"uo_{obm}_a"] = float(safe_flt(r.get(f"{obm}_원"), 0.0))
                        break

    # 경기 선택 컨테이너
    with st.container(border=True):
        if not df_scan.empty and "홈팀" in df_scan.columns:
            st.markdown("##### 🔍 [라운드스캔 시트에서 경기 불러오기] (선택 시 9개사 배당 자동 세팅)")
            match_labels = ["➕ [직접 수동 입력하기]"] + [f"[{r.get('시즌리그명', r.get('리그명', ''))}] {r.get('홈팀', '')} vs {r.get('원정팀', '')} ({r.get('경기날짜', '')})" for _, r in df_scan.iterrows()]
            st.selectbox(
                "분석할 경기를 선택하세요.",
                match_labels,
                index=0,
                key="sel_uo_match_loader",
                on_change=on_match_load
            )
        else:
            st.caption("💡 '라운드스캔' 탭에 등록된 경기가 있으면 목록이 나타납니다.")

    # 기본 정보 입력
    c_l1, c_l2, c_l3 = st.columns([1, 1, 1])
    target_league = c_l1.text_input("🔍 리그명", value="PL", key="uo_target_league")
    home_team = c_l2.text_input("🏠 홈팀명", value="", placeholder="예: 본머스", key="uo_home_team")
    away_team = c_l3.text_input("🚗 원정팀명", value="", placeholder="예: 리버풀", key="uo_away_team")

    st.markdown("##### 🏢 9대 북메이커 배당 입력 현황")
    odds_inputs = {}
    for i in range(0, len(bookmakers), 3):
        cols = st.columns(3)
        for j in range(3):
            idx = i + j
            if idx < len(bookmakers):
                bm = bookmakers[idx]
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"**[{idx+1}] {bm.upper()}**")
                        oh, od, oa = st.columns(3)
                        h_val = oh.number_input("홈", value=0.0, step=0.01, min_value=0.0, key=f"uo_{bm}_h")
                        d_val = od.number_input("무", value=0.0, step=0.01, min_value=0.0, key=f"uo_{bm}_d")
                        a_val = oa.number_input("원정", value=0.0, step=0.01, min_value=0.0, key=f"uo_{bm}_a")
                        odds_inputs[bm] = (h_val, d_val, a_val)

    # 🎯 언오버 기준점 설정 영역
    st.markdown("---")
    st.markdown("##### ⚡ 언오버 기준점 선택 (골 수)")
    ou_options = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
    sel_ou_line = st.selectbox("분석할 기준점 골 수", ou_options, index=ou_options.index(2.5) if 2.5 in ou_options else 2, key="uo_line_select")
    custom_ou_line = float(sel_ou_line)

    st.markdown("---")

    # 분석 실행 로직
    if st.button("🚀 9대 북메이커별 동일배당 언오버 정밀 분석 실행", type="primary", use_container_width=True):
        with st.spinner("개별 업체 탭의 과거 데이터를 불러와 언오버 확률을 산출 중입니다..."):
            
            table_rows = []
            total_matches_count = 0
            total_over_count = 0
            total_under_count = 0
            valid_bm_count = 0

            for idx, bm in enumerate(bookmakers, 1):
                h, d, a = odds_inputs.get(bm, (0.0, 0.0, 0.0))
                if h <= 1.0 or d <= 1.0 or a <= 1.0:
                    table_rows.append({
                        "No": idx, "북메이커": bm.upper(), "입력 배당 (홈/무/원)": "미입력",
                        "환급률": "-", "매칭 건수": "0건", "언더 확률": "-", "오버 확률": "-"
                    })
                    continue

                # 환급률 계산
                raw_inv = (1/h) + (1/d) + (1/a)
                payout = (1 / raw_inv) * 100
                valid_bm_count += 1

                # 각 북메이커별 탭 데이터 로드
                df_bm = load_sheet_data(bm, spreadsheet_id)
                
                over_str, under_str = "-", "-"
                match_count = 0

                if not df_bm.empty:
                    try:
                        cols = list(df_bm.columns)
                        # 데이터베이스 저장 구조에 따른 컬럼 자동 탐색
                        h_col = next((c for c in cols if any(k in c for k in ["해당_홈", "배당_홈", "홈배당", "H_ODDS"])), None)
                        d_col = next((c for c in cols if any(k in c for k in ["해당_무", "배당_무", "무배당", "D_ODDS"])), None)
                        a_col = next((c for c in cols if any(k in c for k in ["해당_원", "배당_원", "원정배당", "A_ODDS"])), None)
                        total_score_col = next((c for c in cols if "점수합계" in c or "Score_Total" in c), None)

                        # 인덱스 기반 예외 처리 (데이터베이스 구조 기준)
                        if not h_col and len(cols) > 14:
                            h_col, d_col, a_col = cols[12], cols[13], cols[14]
                        if not total_score_col and len(cols) > 31:
                            total_score_col = cols[31] # database.py 저장 순서상 점수합계 위치

                        if h_col and d_col and a_col:
                            df_work = df_bm.copy()
                            df_work["H_num"] = pd.to_numeric(df_work[h_col], errors="coerce").fillna(0.0)
                            df_work["D_num"] = pd.to_numeric(df_work[d_col], errors="coerce").fillna(0.0)
                            df_work["A_num"] = pd.to_numeric(df_work[a_col], errors="coerce").fillna(0.0)

                            # 동일 배당 매칭 (오차 범위 ±tol 적용)
                            cond = (
                                (df_work["H_num"] >= h - tol) & (df_work["H_num"] <= h + tol) &
                                (df_work["D_num"] >= d - tol) & (df_work["D_num"] <= d + tol) &
                                (df_work["A_num"] >= a - tol) & (df_work["A_num"] <= a + tol)
                            )
                            matched_df = df_work[cond]
                            match_count = len(matched_df)

                            if match_count > 0 and total_score_col:
                                matched_df["Score_Sum"] = pd.to_numeric(matched_df[total_score_col], errors="coerce")
                                valid_score_df = matched_df.dropna(subset=["Score_Sum"])
                                valid_cnt = len(valid_score_df)

                                if valid_cnt > 0:
                                    over_matches = valid_score_df[valid_score_df["Score_Sum"] > custom_ou_line]
                                    under_matches = valid_score_df[valid_score_df["Score_Sum"] < custom_ou_line]
                                    
                                    ov_cnt = len(over_matches)
                                    un_cnt = len(under_matches)

                                    total_matches_count += valid_cnt
                                    total_over_count += ov_cnt
                                    total_under_count += un_cnt

                                    over_str = f"{(ov_cnt / valid_cnt) * 100:.1f}% ({ov_cnt}회)"
                                    under_str = f"{(un_cnt / valid_cnt) * 100:.1f}% ({un_cnt}회)"
                    except Exception:
                        pass

                table_rows.append({
                    "No": idx,
                    "북메이커": bm.upper(),
                    "입력 배당 (홈/무/원)": f"{h} / {d} / {a}",
                    "환급률": f"{payout:.2f}%",
                    "매칭 건수": f"{match_count}건",
                    "언더 확률": under_str,
                    "오버 확률": over_str
                })

            df_stats = pd.DataFrame(table_rows)
            st.session_state["uo_analyzed"] = True
            st.session_state["uo_df_stats"] = df_stats
            st.session_state["uo_summary"] = {
                "total_matches": total_matches_count,
                "total_over": total_over_count,
                "total_under": total_under_count,
                "line": custom_ou_line
            }

    # 분석 결과 출력
    if st.session_state.get("uo_analyzed", False):
        df_stats = st.session_state["uo_df_stats"]
        summary = st.session_state["uo_summary"]

        st.markdown("---")
        st.subheader(f"📊 [언오버 정밀 분석 리포트] 기준점: {summary['line']}골")
        
        # 종합 요약 메트릭
        tot_m = summary["total_matches"]
        if tot_m > 0:
            ov_p = (summary["total_over"] / tot_m) * 100
            un_p = (summary["total_under"] / tot_m) * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("총 매칭 검증 경기수", f"{tot_m}건")
            m2.metric(f"오버({summary['line']}골 초과) 확률", f"{ov_p:.1f}% ({summary['total_over']}회)", delta_color="normal")
            m3.metric(f"언더({summary['line']}골 미만) 확률", f"{un_p:.1f}% ({summary['total_under']}회)", delta_color="inverse")
        else:
            st.warning("선택한 배당 조건과 일치하는 과거 경기 데이터가 부족합니다.")

        st.markdown("### 📋 9대 북메이커별 동일배당 언오버 분석 현황표")
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

        # 네이버 블로그/카페 전용 인포그래픽 카드 섹션
        st.markdown("---")
        st.markdown("### 🌟 [네이버 블로그/카페 전용] 언오버 분석 인포그래픽 카드")
        st.caption("아래 HTML 코드를 복사하여 블로그에 활용하세요.")

        blog_card_html = f"""
        <div style="background-color:#ffffff; border:2px solid #2e6da4; padding:20px; border-radius:10px; font-family:sans-serif; max-width:700px; margin:0 auto;">
            <h3 style="color:#2e6da4; text-align:center; margin-top:0;">⚽ [UO-Analyzer] 언오버 정밀 분석 리포트</h3>
            <hr style="border:1px solid #eee;">
            <p><b>📌 대상 경기:</b> {home_team} VS {away_team} [{target_league}]</p>
            <p><b>⚡ 분석 기준점:</b> <span style="color:#d9534f; font-weight:bold;">{summary['line']}골 기준</span></p>
            <p><b>📊 통계 결과:</b> 총 {tot_m}건의 동일배당 경기 중 <b>오버 {summary['total_over']}회 ({ov_p:.1f}%)</b> / <b>언더 {summary['total_under']}회 ({un_p:.1f}%)</b></p>
            <p style="font-size:11px; color:#888; text-align:right; margin-bottom:0;">Generated by UO-Analyzer Hub</p>
        </div>
        """
        st.code(blog_card_html, language="html")
        st.success("블로그용 HTML 카드가 성공적으로 생성되었습니다!")
