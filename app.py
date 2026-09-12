import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 소스 모듈 불러오기
from src.api_client import fetch_naver_search, fetch_datalab_trend, CATEGORY_MAP
from src.category_views import render_category_eda
from src.eda_utils import generate_summary_report

load_dotenv()

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="네이버 마켓 인사이트 EDA 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --naver-green: #03C75A;
        --naver-green-dark: #00A84D;
        --naver-mint: #EAF9F0;
        --ink: #121212;
        --muted: #66706A;
        --line: #E2E8E4;
        --surface: #FFFFFF;
    }

    .stApp {
        background: #F5F7F6;
        color: var(--ink);
    }
    [data-testid="stHeader"] {
        background: rgba(245, 247, 246, 0.88);
        backdrop-filter: blur(10px);
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1480px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--ink);
        letter-spacing: -0.03em;
    }

    .naver-hero {
        position: relative;
        overflow: hidden;
        padding: 2.1rem 2.35rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #DDE5E0;
        border-left: 6px solid var(--naver-green);
        border-radius: 18px;
        background: linear-gradient(120deg, #FFFFFF 58%, #E9FFF1 100%);
        box-shadow: 0 10px 32px rgba(19, 60, 38, 0.06);
    }
    .naver-hero::after {
        content: "N";
        position: absolute;
        right: 2.2rem;
        top: -2.3rem;
        color: rgba(3, 199, 90, 0.08);
        font-size: 10rem;
        font-weight: 900;
        line-height: 1;
    }
    .hero-eyebrow {
        color: var(--naver-green-dark);
        font-size: .73rem;
        font-weight: 800;
        letter-spacing: .16em;
        text-transform: uppercase;
        margin-bottom: .65rem;
    }
    .main-title {
        position: relative;
        z-index: 1;
        font-size: clamp(1.75rem, 3vw, 2.55rem);
        line-height: 1.18;
        font-weight: 850;
        letter-spacing: -0.055em;
        color: var(--ink);
        margin: 0;
    }
    .main-title .accent { color: var(--naver-green-dark); }
    .sub-title {
        position: relative;
        z-index: 1;
        font-size: .98rem;
        color: var(--muted);
        margin-top: .7rem;
        margin-bottom: 0;
    }
    .hero-tags {
        position: relative;
        z-index: 1;
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin-top: 1.2rem;
    }
    .hero-tag {
        padding: .36rem .68rem;
        border: 1px solid #CDEDD9;
        border-radius: 999px;
        background: rgba(255,255,255,.76);
        color: #247345;
        font-size: .76rem;
        font-weight: 650;
    }

    .stButton > button[kind="primary"] {
        border: 0;
        border-radius: 10px;
        background: var(--naver-green) !important;
        color: white !important;
        font-weight: 750;
        box-shadow: 0 6px 16px rgba(3, 199, 90, .2);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--naver-green-dark) !important;
        transform: translateY(-1px);
        box-shadow: 0 9px 22px rgba(3, 199, 90, .26);
    }
    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div,
    [data-testid="stDateInput"] [data-baseweb="input"] > div {
        border-color: #D9E1DC !important;
        border-radius: 9px !important;
        background: #FAFBFA !important;
    }
    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--naver-green) !important;
        box-shadow: 0 0 0 1px var(--naver-green) !important;
    }
    [data-testid="stMetric"] {
        padding: 1.05rem 1.15rem;
        border: 1px solid var(--line);
        border-top: 3px solid var(--naver-green);
        border-radius: 12px;
        background: var(--surface);
        box-shadow: 0 5px 18px rgba(27, 45, 35, .04);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); font-weight: 800; }
    .stTabs [data-baseweb="tab-list"] {
        gap: .25rem;
        padding: .3rem;
        border: 1px solid var(--line);
        border-radius: 11px;
        background: white;
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.55rem;
        border-radius: 8px;
        color: #59635D;
        font-weight: 650;
    }
    .stTabs [aria-selected="true"] {
        background: var(--naver-mint);
        color: var(--naver-green-dark) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background: var(--naver-green); }
    [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: white;
        box-shadow: 0 6px 20px rgba(27, 45, 35, .04);
    }
    hr { border-color: var(--line) !important; }
    h1, h2, h3 { letter-spacing: -0.035em !important; }
    a { color: var(--naver-green-dark); }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
        .naver-hero { padding: 1.5rem 1.25rem; border-radius: 14px; }
        .naver-hero::after { display: none; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<section class="naver-hero">
    <div class="hero-eyebrow">NAVER DATA INSIGHT</div>
    <h1 class="main-title">검색 데이터를 <span class="accent">인사이트</span>로</h1>
    <p class="sub-title">네이버 검색·트렌드 데이터를 한곳에서 수집하고, 비교하고, 해석합니다.</p>
    <div class="hero-tags">
        <span class="hero-tag">실시간 API</span>
        <span class="hero-tag">검색 트렌드</span>
        <span class="hero-tag">콘텐츠 분석</span>
        <span class="hero-tag">EDA 리포트</span>
    </div>
</section>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 사이드바 설정 영역
# ---------------------------------------------------------
with st.sidebar:
    st.caption("NAVER SEARCH ANALYTICS")
    st.header("검색 분석 설정")
    
    # 1. API 키 상태 확인 및 설정
    st.subheader("1. API 키 상태 (.env 파일)")
    load_dotenv(override=True)
    env_client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    env_client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    
    if env_client_id and env_client_secret and env_client_id != "your_naver_client_id_here":
        st.success("✅ .env API Key 감지됨")
        st.caption(f"Client ID: `{env_client_id[:4]}******`")
    else:
        st.warning("⚠️ .env 파일에 올바른 API Key를 입력해 주세요.")
        
    st.divider()
    
    # 2. 검색어 입력 (쉼표 구분)
    st.subheader("2. 다중 검색어 입력")
    raw_keywords = st.text_input("검색어 (쉼표 `,` 구분)", value="인공지능, 빅데이터, 클라우드")
    keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    
    st.divider()
    
    # 3. 기간 설정 (데이터랩 트렌드용)
    st.subheader("3. 트렌드 조회 기간 설정")
    default_end = datetime.today().date()
    default_start = default_end - timedelta(days=90)
    
    date_range = st.date_input(
        "조회 기간",
        value=(default_start, default_end),
        max_value=default_end
    )
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date_str = date_range[0].strftime("%Y-%m-%d")
        end_date_str = date_range[1].strftime("%Y-%m-%d")
    else:
        start_date_str = default_start.strftime("%Y-%m-%d")
        end_date_str = default_end.strftime("%Y-%m-%d")
        
    # 4. 수집 대상 카테고리 선택
    st.subheader("4. 수집 대상 카테고리 선택")
    selected_categories = st.multiselect(
        "수집할 카테고리 선택",
        options=list(CATEGORY_MAP.keys()),
        default=list(CATEGORY_MAP.keys())
    )
    
    st.divider()
    
    # 5. 데이터랩 세부 필터 (기기, 성별, 연령대)
    st.subheader("5. 데이터랩 세부 필터")
    dl_device = st.selectbox("조회 기기", options=["전체", "PC", "모바일"])
    dl_gender = st.selectbox("성별", options=["전체", "남성", "여성"])
    
    age_options = ["전체", "10대", "20대", "30대", "40대", "50대", "60대 이상"]
    age_map = {"10대": "1", "20대": "2", "30대": "3", "40대": "4", "50대": "5", "60대 이상": "6"}
    selected_ages_raw = st.multiselect("연령대 선택", options=age_options, default=["전체"])
    
    if "전체" in selected_ages_raw or not selected_ages_raw:
        dl_ages = None
    else:
        dl_ages = [age_map[a] for a in selected_ages_raw if a in age_map]

    st.divider()
    
    # 6. 수집 및 전처리 필터
    st.subheader("6. 수집 & 텍스트 필터")
    display_count = st.slider("카테고리당 수집 건수", min_value=10, max_value=100, value=50, step=10)
    sort_option = st.selectbox("검색 정렬 기준", options=["관련도순 (sim)", "최신순 (date)"])
    sort_code = "sim" if "sim" in sort_option else "date"
    
    min_text_len = st.number_input("최소 전체 글자수 필터", min_value=0, max_value=500, value=0, step=10)
    raw_stopwords = st.text_input("사용자 정의 불용어 (쉼표 `,` 구분)", value="")
    custom_stopwords_list = [s.strip() for s in raw_stopwords.split(",") if s.strip()]
    
    btn_fetch = st.button("🚀 데이터 수집 & 분석 시작", type="primary", use_container_width=True)

# ---------------------------------------------------------
# 메인 데이터 수집 실행
# ---------------------------------------------------------
if btn_fetch:
    if not keywords_list:
        st.error("최소 1개 이상의 검색어를 입력해주세요.")
    elif not selected_categories:
        st.error("최소 1개 이상의 수집 카테고리를 선택해주세요.")
    elif not os.getenv("NAVER_CLIENT_ID") or not os.getenv("NAVER_CLIENT_SECRET"):
        st.error("유효한 네이버 클라우드 API Client ID와 Secret을 .env 파일에 입력해주세요.")
    else:
        with st.spinner("네이버 클라우드 API에서 데이터를 수집하고 EDA 통계를 계산 중입니다..."):
            # 1. 데이터랩 트렌드 수집
            trend_df = pd.DataFrame()
            try:
                trend_df = fetch_datalab_trend(
                    keywords_list,
                    start_date_str,
                    end_date_str,
                    device=dl_device,
                    gender=dl_gender,
                    ages=dl_ages
                )
            except Exception as e:
                st.warning(f"데이터랩 트렌드 수집 안내: {e}")

            # 2. 선택된 카테고리 검색 데이터 수집
            all_search_dfs = []
            
            progress_bar = st.progress(0)
            total_steps = len(keywords_list) * len(selected_categories)
            current_step = 0
            
            for kw in keywords_list:
                for cat_name in selected_categories:
                    cat_code = CATEGORY_MAP[cat_name]
                    try:
                        df_cat = fetch_naver_search(kw, category=cat_code, display=display_count, sort=sort_code)
                        if not df_cat.empty:
                            df_cat["카테고리명"] = cat_name
                            all_search_dfs.append(df_cat)
                    except Exception as e:
                        st.caption(f"[{kw}] [{cat_name}] 수집 중 제외됨: {e}")
                    current_step += 1
                    progress_bar.progress(current_step / total_steps)
                    
            progress_bar.empty()
            
            if all_search_dfs:
                combined_df = pd.concat(all_search_dfs, ignore_index=True)
            else:
                combined_df = pd.DataFrame()

            # 세션 상태 보존
            st.session_state["trend_df"] = trend_df
            st.session_state["combined_df"] = combined_df
            st.session_state["keywords_list"] = keywords_list
            st.session_state["min_text_len"] = min_text_len
            st.session_state["custom_stopwords_list"] = custom_stopwords_list
            st.session_state["selected_categories"] = selected_categories

# ---------------------------------------------------------
# 최상위 탭 렌더링 (통합 트렌드 및 8개 카테고리 세부 탭)
# ---------------------------------------------------------
if "combined_df" in st.session_state and not st.session_state["combined_df"].empty:
    combined_df = st.session_state["combined_df"]
    trend_df = st.session_state.get("trend_df", pd.DataFrame())
    keywords_list = st.session_state.get("keywords_list", [])

    # 카테고리 목록 정의 (선택된 카테고리만)
    selected_categories = st.session_state.get("selected_categories", list(CATEGORY_MAP.keys()))
    min_text_len = st.session_state.get("min_text_len", 0)
    custom_stopwords_list = st.session_state.get("custom_stopwords_list", [])
    
    tab_titles = ["🌐 통합 검색어 트렌드"] + [f"📂 {c}" for c in selected_categories] + ["📑 종합 분석 보고서", "📋 전체 Raw 데이터 & 내보내기"]
    
    tabs = st.tabs(tab_titles)

    # ---------------------------------------------------------
    # TAB 0: 통합 검색어 트렌드
    # ---------------------------------------------------------
    with tabs[0]:
        st.subheader("🗓️ 네이버 데이터랩 검색어 통합 트렌드 (Line Chart)")
        if not trend_df.empty:
            fig_trend = px.line(
                trend_df,
                x="날짜",
                y="상대적 검색량",
                color="검색어",
                title=f"검색어별 상대적 검색량 추이 ({start_date_str} ~ {end_date_str})",
                markers=True,
                template="plotly_white"
            )
            fig_trend.update_layout(hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("데이터랩 트렌드 데이터가 없습니다.")

        st.subheader("📊 전체 수집 카테고리 및 검색어별 분포 (Bar Chart)")
        c_overall1, c_overall2 = st.columns(2)
        with c_overall1:
            counts_cat = combined_df.groupby(["검색어", "카테고리명"]).size().reset_index(name="수집건수")
            fig_ov1 = px.bar(
                counts_cat,
                x="카테고리명",
                y="수집건수",
                color="검색어",
                barmode="group",
                title="카테고리 및 검색어별 데이터 수집 건수",
                template="plotly_white"
            )
            st.plotly_chart(fig_ov1, use_container_width=True)
            
        with c_overall2:
            counts_kw = combined_df.groupby("검색어").size().reset_index(name="총 수집건수")
            fig_ov2 = px.bar(
                counts_kw,
                x="검색어",
                y="총 수집건수",
                color="검색어",
                text="총 수집건수",
                title="검색어별 총 데이터 수집량 비교 (Bar Chart)",
                template="plotly_white"
            )
            st.plotly_chart(fig_ov2, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 1~N: 선택한 카테고리별 세부 EDA 페이지 렌더링
    # ---------------------------------------------------------
    for idx, c_name in enumerate(selected_categories):
        with tabs[idx + 1]:
            df_sub = combined_df[combined_df["카테고리명"] == c_name]
            render_category_eda(df_sub, c_name, min_len=min_text_len, custom_stopwords=custom_stopwords_list)

    # ---------------------------------------------------------
    # TAB N+1: 종합 분석 보고서
    # ---------------------------------------------------------
    with tabs[len(selected_categories) + 1]:
        st.subheader("📑 자동 생성된 마켓 인사이트 종합 보고서")
        report_md = generate_summary_report(combined_df, trend_df, keywords_list)
        
        st.markdown(report_md)
        st.divider()
        
        st.download_button(
            label="📥 종합 보고서 (.md 파일) 다운로드",
            data=report_md,
            file_name=f"naver_market_insight_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )

    # ---------------------------------------------------------
    # TAB N+2: 전체 Raw 데이터 & 다운로드
    # ---------------------------------------------------------
    with tabs[len(selected_categories) + 2]:
        st.subheader("📄 수집 전체 Raw 데이터 및 데이터 내보내기")
        st.dataframe(combined_df, use_container_width=True)
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_data = combined_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 전체 데이터 CSV 다운로드",
                data=csv_data,
                file_name=f"naver_market_insight_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        with col_dl2:
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                combined_df.to_excel(writer, index=False, sheet_name="AllData")
            excel_data = output.getvalue()
            st.download_button(
                label="📥 전체 데이터 Excel 다운로드",
                data=excel_data,
                file_name=f"naver_market_insight_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👈 사이드바에서 검색어와 기간을 선택 후 **[🚀 데이터 수집 & 분석 시작]** 버튼을 클릭하세요.")
