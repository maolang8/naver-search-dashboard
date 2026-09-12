import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from src.eda_utils import (
    extract_tokens,
    generate_wordcloud,
    analyze_sentiment,
    extract_domain,
    compute_descriptive_stats,
    compute_sentiment_crosstab,
    compute_domain_pivot
)

CHART_COLORS = [
    "#527A5D", "#759685", "#809BAC", "#9DB2BE",
    "#A8BEA3", "#C4D3C5", "#667F8F", "#DCE6DB",
]

def render_category_eda(df_cat, category_name, min_len=0, custom_stopwords=None):
    st.header(f"📌 {category_name} 세부 EDA 및 데이터 탐색")
    
    if df_cat.empty:
        st.info(f"[{category_name}] 수집된 데이터가 없거나 해당 API 서비스 권한이 설정되지 않았습니다.")
        return

    # 전처리 및 열 파생
    df_cat = df_cat.copy()
    df_cat["제목_길이"] = df_cat["제목"].astype(str).str.len()
    df_cat["내용_길이"] = df_cat["요약/내용"].astype(str).str.len()
    df_cat["전체_글자수"] = df_cat["제목_길이"] + df_cat["내용_길이"]
    
    # 최소 글자수 필터 적용
    if min_len > 0:
        df_cat = df_cat[df_cat["전체_글자수"] >= min_len]
        if df_cat.empty:
            st.warning(f"최소 글자수 필터 ({min_len}자 이상) 조건에 맞는 데이터가 없습니다.")
            return

    df_cat["감성"] = df_cat["요약/내용"].apply(analyze_sentiment)
    df_cat["출처_도메인"] = df_cat["링크"].apply(extract_domain)

    # 지표 렌더링
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("총 수집 건수", f"{len(df_cat):,}건")
    with col_m2:
        st.metric("평균 제목 글자수", f"{df_cat['제목_길이'].mean():.1f}자")
    with col_m3:
        st.metric("평균 본문 글자수", f"{df_cat['내용_길이'].mean():.1f}자")
    with col_m4:
        pos_ratio = (df_cat['감성'] == '긍정').mean() * 100
        st.metric("긍정 감성 비율", f"{pos_ratio:.1f}%")

    st.divider()

    # ---------------------------------------------------------
    # SECTION 1: 5개 이상의 시각화 차트 (파이 차트 제외)
    # ---------------------------------------------------------
    st.subheader(f"📊 1. {category_name} 인터랙티브 시각화 차트 (5종)")
    
    c1, c2 = st.columns(2)
    
    with c1:
        # Chart 1: 검색어별 수집 건수 막대 차트 (Bar Chart)
        st.markdown("**Chart 1. 검색어별 수집 데이터량 (Grouped Bar)**")
        kw_counts = df_cat.groupby("검색어").size().reset_index(name="수집건수")
        fig1 = px.bar(
            kw_counts,
            x="검색어",
            y="수집건수",
            color="검색어",
            color_discrete_sequence=CHART_COLORS,
            text="수집건수",
            title=f"검색어별 {category_name} 데이터 수집량",
            template="plotly_white"
        )
        st.plotly_chart(fig1, width="stretch")
        with st.expander("📋 Chart 1 수치 데이터표 및 CSV 다운로드"):
            st.dataframe(kw_counts, width="stretch")
            st.download_button(
                "📥 Chart 1 CSV 다운로드",
                data=kw_counts.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"{category_name}_chart1_data.csv",
                mime="text/csv",
                key=f"dl_chart1_{category_name}"
            )
        
        # Chart 2: 감성 분석 분포 막대 차트 (Sentiment Distribution Bar)
        st.markdown("**Chart 2. 검색어별 감성(긍정/부정/중립) 분포 (Stacked Bar)**")
        sent_counts = df_cat.groupby(["검색어", "감성"]).size().reset_index(name="건수")
        fig2 = px.bar(
            sent_counts,
            x="검색어",
            y="건수",
            color="감성",
            color_discrete_map={"긍정": "#5F9271", "부정": "#B97870", "중립": "#8798A5"},
            title=f"{category_name} 검색어별 감성 구성비",
            barmode="stack",
            template="plotly_white"
        )
        fig2.update_layout(barnorm="percent")
        fig2.update_yaxes(title="감성 구성비 (%)", ticksuffix="%")
        st.plotly_chart(fig2, width="stretch")
        with st.expander("📋 Chart 2 수치 데이터표 및 CSV 다운로드"):
            st.dataframe(sent_counts, width="stretch")
            st.download_button(
                "📥 Chart 2 CSV 다운로드",
                data=sent_counts.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"{category_name}_chart2_data.csv",
                mime="text/csv",
                key=f"dl_chart2_{category_name}"
            )

    with c2:
        # Chart 3: 텍스트 글자수 분포 히스토그램 (Histogram)
        st.markdown("**Chart 3. 검색어별 콘텐츠 정보량 비교 (Box Plot)**")
        fig3 = px.box(
            df_cat,
            x="검색어",
            y="전체_글자수",
            color="검색어",
            color_discrete_sequence=CHART_COLORS,
            points="outliers",
            title=f"{category_name} 검색어별 콘텐츠 정보량",
            template="plotly_white"
        )
        st.plotly_chart(fig3, width="stretch")
        with st.expander("📋 Chart 3 수치 데이터표 및 CSV 다운로드"):
            char_stat_df = df_cat[["검색어", "제목_길이", "내용_길이", "전체_글자수"]]
            st.dataframe(char_stat_df, width="stretch")
            st.download_button(
                "📥 Chart 3 CSV 다운로드",
                data=char_stat_df.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"{category_name}_chart3_data.csv",
                mime="text/csv",
                key=f"dl_chart3_{category_name}"
            )

        # Chart 4: 상위 15개 빈출 키워드 수평 막대 차트 (Horizontal Bar Chart)
        st.markdown("**Chart 4. Top 15 핵심 단어/키워드 빈도 (Horizontal Bar)**")
        all_texts = df_cat["제목"].tolist() + df_cat["요약/내용"].tolist()
        tokens = extract_tokens(all_texts, custom_stopwords=custom_stopwords)
        top15_df = pd.DataFrame(tokens.most_common(15), columns=["단어", "빈도"])
        fig4 = px.bar(
            top15_df,
            x="빈도",
            y="단어",
            orientation="h",
            color_discrete_sequence=CHART_COLORS,
            text="빈도",
            title=f"{category_name} 전체 주요 출현 단어 Top 15",
            template="plotly_white"
        )
        fig4.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig4, width="stretch")
        with st.expander("📋 Chart 4 수치 데이터표 및 CSV 다운로드"):
            st.dataframe(top15_df, width="stretch")
            st.download_button(
                "📥 Chart 4 CSV 다운로드",
                data=top15_df.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"{category_name}_chart4_data.csv",
                mime="text/csv",
                key=f"dl_chart4_{category_name}"
            )

    # Chart 5: 출처 도메인/플랫폼 Top 10 분포 차트 (Top Domain Distribution)
    st.markdown("**Chart 5. 주요 출처 도메인/플랫폼 분포 Top 10 (Bar Chart)**")
    domain_df = df_cat.groupby("출처_도메인").size().reset_index(name="게시물수").sort_values(by="게시물수", ascending=False).head(10)
    domain_df["누적점유율"] = (domain_df["게시물수"].cumsum() / domain_df["게시물수"].sum() * 100).round(1)
    fig5 = go.Figure()
    fig5.add_bar(
        x=domain_df["출처_도메인"], y=domain_df["게시물수"],
        name="게시물 수", marker_color="#759685", text=domain_df["게시물수"]
    )
    fig5.add_scatter(
        x=domain_df["출처_도메인"], y=domain_df["누적점유율"],
        name="누적 점유율", mode="lines+markers", marker_color="#667F8F", yaxis="y2"
    )
    fig5.update_layout(
        title=f"{category_name} 출처 집중도 (Pareto)", template="plotly_white",
        yaxis=dict(title="게시물 수"),
        yaxis2=dict(title="누적 점유율 (%)", overlaying="y", side="right", range=[0, 105]),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig5, width="stretch")
    with st.expander("📋 Chart 5 수치 데이터표 및 CSV 다운로드"):
        st.dataframe(domain_df, width="stretch")
        st.download_button(
            "📥 Chart 5 CSV 다운로드",
            data=domain_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"{category_name}_chart5_data.csv",
            mime="text/csv",
            key=f"dl_chart5_{category_name}"
        )

    st.divider()

    # ---------------------------------------------------------
    # SECTION 2: 5개 이상의 고급 통계표 (기술통계, 교차표, 피봇테이블)
    # ---------------------------------------------------------
    st.subheader(f"🔢 2. {category_name} 수치 통계 & 분석표 (5종)")

    # Table 1: 기술 통계량 표 (Descriptive Statistics)
    st.markdown("#### 📄 Table 1. 텍스트 수치 데이터 주요 기술통계량 (Mean, Std, Min, Max 등)")
    desc_stats = compute_descriptive_stats(df_cat)
    st.dataframe(desc_stats, width="stretch")
    st.download_button("📥 Table 1 CSV 다운로드", desc_stats.to_csv(encoding="utf-8-sig"), f"{category_name}_table1.csv", "text/csv", key=f"tbl1_{category_name}")

    # Table 2: 검색어 x 감성 교차표 (Crosstab Counts)
    st.markdown("#### 📄 Table 2. 검색어별 감성 교차 빈도표 (Crosstab Count Table)")
    ct_counts, ct_props = compute_sentiment_crosstab(df_cat)
    st.dataframe(ct_counts, width="stretch")
    st.download_button("📥 Table 2 CSV 다운로드", ct_counts.to_csv(encoding="utf-8-sig"), f"{category_name}_table2.csv", "text/csv", key=f"tbl2_{category_name}")

    # Table 3: 검색어 x 감성 교차 비율표 (Crosstab Proportion Table)
    st.markdown("#### 📄 Table 3. 검색어별 감성 비율 교차표 (%)")
    st.dataframe(ct_props, width="stretch")
    st.download_button("📥 Table 3 CSV 다운로드", ct_props.to_csv(encoding="utf-8-sig"), f"{category_name}_table3.csv", "text/csv", key=f"tbl3_{category_name}")

    # Table 4: 출처 도메인 x 검색어 피봇테이블 (Pivot Table)
    st.markdown("#### 📄 Table 4. 출처 도메인 및 검색어별 작성 게시물 수 피봇테이블 (Pivot Table)")
    pivot_domain = compute_domain_pivot(df_cat)
    st.dataframe(pivot_domain, width="stretch")
    st.download_button("📥 Table 4 CSV 다운로드", pivot_domain.to_csv(encoding="utf-8-sig"), f"{category_name}_table4.csv", "text/csv", key=f"tbl4_{category_name}")

    # Table 5: 주요 단어 빈도 및 비율 통계표
    st.markdown("#### 📄 Table 5. 키워드 출현 빈도 및 점유 비율 통계표 (Top 20 Words)")
    total_token_count = sum(tokens.values()) if tokens else 1
    freq_table_df = pd.DataFrame(tokens.most_common(20), columns=["키워드/단어", "출현 빈도"])
    freq_table_df["전체 대비 점유율 (%)"] = (freq_table_df["출현 빈도"] / total_token_count * 100).round(2)
    st.dataframe(freq_table_df, width="stretch")
    st.download_button("📥 Table 5 CSV 다운로드", freq_table_df.to_csv(index=False, encoding="utf-8-sig"), f"{category_name}_table5.csv", "text/csv", key=f"tbl5_{category_name}")

    st.divider()

    # ---------------------------------------------------------
    # SECTION 3: WordCloud & Raw Data
    # ---------------------------------------------------------
    st.subheader("☁️ WordCloud & Raw Data View")
    
    col_wc, col_raw = st.columns([5, 5])
    
    with col_wc:
        st.markdown("**키워드 워드클라우드 (WordCloud)**")
        wc = generate_wordcloud(tokens)
        if wc:
            fig_wc, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig_wc)
        else:
            st.info("워드클라우드를 생성할 텍스트가 없습니다.")
            
    with col_raw:
        st.markdown("**카테고리 수집 Raw 데이터 표**")
        st.dataframe(df_cat[["검색어", "제목", "요약/내용", "출처_도메인", "감성", "링크"]], width="stretch")
