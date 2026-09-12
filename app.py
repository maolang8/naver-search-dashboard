import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 소스 모듈 불러오기
from src.api_client import fetch_naver_search, fetch_datalab_trend, CATEGORY_MAP
from src.category_views import render_category_eda
from src.eda_utils import generate_summary_report, analyze_sentiment

load_dotenv()

# 톤다운된 네이버 그린 기반 차트 팔레트
NAVER_CHART_COLORS = [
    "#527A5D", "#759685", "#809BAC", "#9DB2BE",
    "#A8BEA3", "#C4D3C5", "#667F8F", "#DCE6DB",
]
px.defaults.color_discrete_sequence = NAVER_CHART_COLORS

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
        --naver-green: #69A97C;
        --naver-green-dark: #437955;
        --naver-mint: #E8F1E9;
        --naver-pale: #F2F6F1;
        --ink: #252A26;
        --muted: #69716B;
        --line: #D7E0D8;
        --surface: #FCFDFC;
    }

    .stApp {
        background: #F6F7F4;
        color: var(--ink);
    }
    [data-testid="stHeader"] {
        background: rgba(246, 247, 244, 0.9);
        backdrop-filter: blur(10px);
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1480px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stSidebar"] {
        background: #FDFEFC;
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
        padding: 1rem 0 1.35rem;
        margin-bottom: 1.5rem;
        border: 0;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
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
        border: 1px solid #BDD3C2;
        border-radius: 999px;
        background: #EFF5EF;
        color: #466E52;
        font-size: .76rem;
        font-weight: 650;
    }

    .stButton > button[kind="primary"] {
        border: 0;
        border-radius: 10px;
        background: var(--naver-green) !important;
        color: white !important;
        font-weight: 750;
        box-shadow: 0 6px 16px rgba(67, 121, 85, .16);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--naver-green-dark) !important;
        transform: translateY(-1px);
        box-shadow: 0 9px 22px rgba(67, 121, 85, .22);
    }
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] {
        border: 1px solid var(--naver-green) !important;
        border-radius: 9px !important;
        background: #FFFFFF !important;
        box-shadow: 0 0 0 1px rgba(67, 121, 85, .08) !important;
    }
    div[data-baseweb="input"]:hover,
    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="textarea"]:hover,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border: 1px solid var(--naver-green) !important;
        box-shadow: 0 0 0 2px rgba(67, 121, 85, .16) !important;
    }
    span[data-baseweb="tag"] {
        border: 1px solid var(--naver-green-dark) !important;
        border-radius: 8px !important;
        background: #6FA77E !important;
        color: #FFFFFF !important;
        font-weight: 700;
    }
    span[data-baseweb="tag"] span,
    span[data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }
    [data-testid="stMetric"] {
        padding: 1.05rem 1.15rem;
        border: 1px solid var(--line);
        border-top: 3px solid var(--naver-green);
        border-radius: 12px;
        background: var(--surface);
        box-shadow: 0 5px 18px rgba(46, 68, 52, .04);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); font-weight: 800; }
    .stTabs [data-baseweb="tab-list"] {
        gap: .25rem;
        padding: .3rem;
        border: 1px solid var(--line);
        border-radius: 11px;
        background: var(--surface);
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
        background: var(--surface);
        box-shadow: 0 6px 20px rgba(46, 68, 52, .04);
    }
    [data-testid="stExpander"],
    [data-testid="stAlert"],
    [data-testid="stForm"],
    [data-testid="stFileUploaderDropzone"] {
        border: 1px solid #D3DDD7 !important;
        border-radius: 11px !important;
        background: var(--surface);
    }
    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stExpander"] {
        outline: 1px solid rgba(18, 18, 18, .015);
        outline-offset: -2px;
    }
    hr { border-color: var(--line) !important; }
    h1, h2, h3 { letter-spacing: -0.035em !important; }
    a { color: var(--naver-green-dark); }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
        .naver-hero { padding: .75rem 0 1rem; }
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
    st.subheader("1. API 연결 상태")
    load_dotenv(override=True)
    env_client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    env_client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    
    if env_client_id and env_client_secret and env_client_id != "your_naver_client_id_here":
        st.success("✅ API 인증 정보가 안전하게 연결되었습니다.")
    else:
        st.warning("⚠️ 환경변수에 API 인증 정보를 설정해 주세요.")
        
    st.divider()
    
    # 2. 검색어 입력 (태그형 직접 입력)
    st.subheader("2. 다중 검색어 입력")
    keywords_list = st.multiselect(
        "검색어 (입력 후 Enter)",
        options=["인공지능", "빅데이터", "클라우드"],
        default=["인공지능", "빅데이터", "클라우드"],
        placeholder="검색어를 입력하고 Enter를 누르세요",
        accept_new_options=True,
    )
    
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
        st.error("유효한 네이버 클라우드 API 인증 정보를 환경변수에 설정해주세요.")
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
    
    selected_view = st.selectbox(
        "분석 화면 선택",
        options=[
            "통합 검색어 트렌드",
            "애플리케이션별 분석",
            "종합 분석 보고서",
            "Raw 데이터 내보내기",
        ],
        label_visibility="collapsed",
    )

    # ---------------------------------------------------------
    # TAB 0: 통합 검색어 트렌드
    # ---------------------------------------------------------
    if selected_view == "통합 검색어 트렌드":
        st.subheader("🗓️ 네이버 데이터랩 검색어 통합 트렌드 (Line Chart)")
        if not trend_df.empty:
            fig_trend = px.line(
                trend_df,
                x="날짜",
                y="상대적 검색량",
                color="검색어",
                color_discrete_sequence=NAVER_CHART_COLORS,
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
                color_discrete_sequence=NAVER_CHART_COLORS,
                barmode="stack",
                title="카테고리별 검색어 콘텐츠 구성비",
                template="plotly_white"
            )
            fig_ov1.update_layout(barnorm="percent")
            fig_ov1.update_yaxes(title="구성비 (%)", ticksuffix="%")
            st.plotly_chart(fig_ov1, use_container_width=True)
            
        with c_overall2:
            if not trend_df.empty:
                interest_kw = trend_df.groupby("검색어", as_index=False)["상대적 검색량"].mean()
                interest_kw["평균 관심도"] = interest_kw["상대적 검색량"].round(1)
                fig_ov2 = px.bar(
                    interest_kw,
                    x="검색어",
                    y="평균 관심도",
                    color="검색어",
                    color_discrete_sequence=NAVER_CHART_COLORS,
                    text="평균 관심도",
                    title="검색어별 기간 평균 관심도",
                    template="plotly_white"
                )
            else:
                counts_kw = combined_df.groupby("검색어").size().reset_index(name="총 수집건수")
                fig_ov2 = px.bar(
                    counts_kw, x="검색어", y="총 수집건수", color="검색어",
                    color_discrete_sequence=NAVER_CHART_COLORS,
                    text="총 수집건수", title="검색어별 확보 콘텐츠", template="plotly_white"
                )
            st.plotly_chart(fig_ov2, use_container_width=True)

        st.subheader("채널별 수집 결과 비교")
        channel_df = combined_df.copy()
        channel_df["콘텐츠 글자수"] = (
            channel_df["제목"].fillna("").astype(str).str.len()
            + channel_df["요약/내용"].fillna("").astype(str).str.len()
        )
        channel_df["감성"] = channel_df["요약/내용"].fillna("").apply(analyze_sentiment)

        channel_volume = channel_df.groupby("카테고리명", as_index=False).size()
        channel_volume.columns = ["채널", "수집 결과"]
        channel_depth = (
            channel_df.groupby("카테고리명", as_index=False)["콘텐츠 글자수"].mean()
            .rename(columns={"카테고리명": "채널", "콘텐츠 글자수": "평균 글자수"})
        )
        channel_depth["평균 글자수"] = channel_depth["평균 글자수"].round(0)
        channel_sentiment = channel_df.groupby(["카테고리명", "감성"]).size().reset_index(name="건수")

        channel_col1, channel_col2, channel_col3 = st.columns(3)
        with channel_col1:
            fig_channel_volume = px.bar(
                channel_volume, x="채널", y="수집 결과", color="채널", text="수집 결과",
                color_discrete_sequence=NAVER_CHART_COLORS,
                title="채널별 확보 콘텐츠", template="plotly_white"
            )
            fig_channel_volume.update_layout(showlegend=False)
            st.plotly_chart(fig_channel_volume, use_container_width=True)

        with channel_col2:
            fig_channel_depth = px.bar(
                channel_depth, x="채널", y="평균 글자수", color="채널", text="평균 글자수",
                color_discrete_sequence=NAVER_CHART_COLORS,
                title="채널별 평균 콘텐츠 정보량", template="plotly_white"
            )
            fig_channel_depth.update_layout(showlegend=False)
            st.plotly_chart(fig_channel_depth, use_container_width=True)

        with channel_col3:
            fig_channel_sentiment = px.bar(
                channel_sentiment, x="카테고리명", y="건수", color="감성",
                color_discrete_map={"긍정": "#5F9271", "부정": "#B97870", "중립": "#8798A5"},
                barmode="stack",
                title="채널별 감성 구성비", template="plotly_white"
            )
            fig_channel_sentiment.update_layout(barnorm="percent")
            fig_channel_sentiment.update_yaxes(title="구성비 (%)", ticksuffix="%")
            fig_channel_sentiment.update_xaxes(title="채널")
            st.plotly_chart(fig_channel_sentiment, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 1~N: 선택한 카테고리별 세부 EDA 페이지 렌더링
    # ---------------------------------------------------------
    elif selected_view == "애플리케이션별 분석":
        c_name = st.selectbox(
            "분석할 애플리케이션 선택",
            options=selected_categories,
        )
        df_sub = combined_df[combined_df["카테고리명"] == c_name]
        render_category_eda(df_sub, c_name, min_len=min_text_len, custom_stopwords=custom_stopwords_list)

    # ---------------------------------------------------------
    # TAB N+1: 종합 분석 보고서
    # ---------------------------------------------------------
    elif selected_view == "종합 분석 보고서":
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
    elif selected_view == "Raw 데이터 내보내기":
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
