import re
from collections import Counter
import pandas as pd
from urllib.parse import urlparse
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from wordcloud import WordCloud

# 한국어 폰트 설정
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

STOPWORDS = set([
    "의", "가", "이", "은", "들", "는", "좀", "잘", "걍", "과", "도", "를", "으로", "자", "에", "와", "한", "하다",
    "입니다", "있습니다", "수", "등", "및", "네이버", "검색", "관련", "위한", "대한", "통해", "위해", "있는", "하는", "있어", "그"
])

POSITIVE_WORDS = set(["추천", "좋은", "최고", "혁신", "성장", "상승", "우수", "혜택", "인기", "강추", "성공", "만족", "발전", "유용", "쉬운", "편리"])
NEGATIVE_WORDS = set(["문제", "우려", "하락", "위험", "손실", "부족", "어려운", "불만", "피해", "비판", "오류", "경고", "논란", "감소", "부담"])

NAVER_MUTED_CMAP = LinearSegmentedColormap.from_list(
    "naver_muted",
    ["#DCE6DB", "#A8BEA3", "#759685", "#527A5D", "#667F8F"],
)

def extract_tokens(text_list, custom_stopwords=None):
    full_text = " ".join([str(t) for t in text_list if pd.notna(t)])
    words = re.findall(r'[가-힣a-zA-Z0-9]{2,}', full_text)
    
    combined_stopwords = set(STOPWORDS)
    if custom_stopwords:
        for sw in custom_stopwords:
            if sw.strip():
                combined_stopwords.add(sw.strip())
                
    filtered_words = [w for w in words if w.lower() not in combined_stopwords and not w.isdigit()]
    return Counter(filtered_words)

def generate_wordcloud(word_counts):
    if not word_counts:
        return None
    font_path = "C:/Windows/Fonts/malgun.ttf"
    try:
        wc = WordCloud(
            font_path=font_path,
            background_color="white",
            width=800,
            height=400,
            max_words=100,
            colormap=NAVER_MUTED_CMAP,
        ).generate_from_frequencies(word_counts)
        return wc
    except Exception:
        wc = WordCloud(
            background_color="white",
            width=800,
            height=400,
            max_words=100,
            colormap=NAVER_MUTED_CMAP,
        ).generate_from_frequencies(word_counts)
        return wc

def analyze_sentiment(text):
    if not isinstance(text, str) or not text:
        return "중립"
    
    pos_score = sum(1 for w in POSITIVE_WORDS if w in text)
    neg_score = sum(1 for w in NEGATIVE_WORDS if w in text)
    
    if pos_score > neg_score:
        return "긍정"
    elif neg_score > pos_score:
        return "부정"
    else:
        return "중립"

def extract_domain(url):
    if not isinstance(url, str) or not url:
        return "기타/알수없음"
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc or parsed.path.split('/')[0]
        netloc = netloc.replace("www.", "")
        return netloc if netloc else "기타/알수없음"
    except Exception:
        return "기타/알수없음"

def compute_descriptive_stats(df):
    if df.empty:
        return pd.DataFrame()
    
    # 텍스트 길이 산출
    df_calc = df.copy()
    df_calc["제목_길이"] = df_calc["제목"].astype(str).str.len()
    df_calc["내용_길이"] = df_calc["요약/내용"].astype(str).str.len()
    df_calc["전체_글자수"] = df_calc["제목_길이"] + df_calc["내용_길이"]
    
    stats = df_calc[["제목_길이", "내용_길이", "전체_글자수"]].describe().T
    stats = stats.rename(columns={
        "count": "데이터 수",
        "mean": "평균",
        "std": "표준편차",
        "min": "최소값",
        "25%": "1사분위수(25%)",
        "50%": "중앙값(50%)",
        "75%": "3사분위수(75%)",
        "max": "최대값"
    })
    return stats.round(2)

def compute_sentiment_crosstab(df):
    if df.empty or "감성" not in df.columns:
        return pd.DataFrame()
    
    ct = pd.crosstab(df["검색어"], df["감성"], margins=True, margins_name="합계")
    ct_prop = pd.crosstab(df["검색어"], df["감성"], normalize='index').round(4) * 100
    
    return ct, ct_prop

def compute_domain_pivot(df):
    if df.empty or "출처_도메인" not in df.columns:
        return pd.DataFrame()
    
    pivot = pd.pivot_table(
        df,
        index="출처_도메인",
        columns="검색어",
        values="제목",
        aggfunc="count",
        fill_value=0,
        margins=True,
        margins_name="총계"
    )
    return pivot.sort_values(by="총계", ascending=False).head(15)

def generate_summary_report(df, trend_df=None, keywords=None):
    if df.empty:
        return "수집된 데이터가 없어 종합 보고서를 생성할 수 없습니다."
    
    now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    total_records = len(df)
    kw_list_str = ", ".join(keywords) if keywords else "알 수 없음"
    
    # 카테고리별 수집 현황
    cat_summary = df.groupby("카테고리명").size().to_dict()
    cat_summary_str = "\n".join([f"- **{cat}**: {count:,}건" for cat, count in cat_summary.items()])
    
    # 검색어별 점유 현황
    kw_summary = df.groupby("검색어").size().to_dict()
    kw_summary_str = "\n".join([f"- **{kw}**: {count:,}건 ({count/total_records*100:.1f}%)" for kw, count in kw_summary.items()])
    
    # 감성 분석 계산
    df_calc = df.copy()
    if "감성" not in df_calc.columns:
        df_calc["감성"] = df_calc["요약/내용"].apply(analyze_sentiment)
    if "출처_도메인" not in df_calc.columns:
        df_calc["출처_도메인"] = df_calc["링크"].apply(extract_domain)
        
    sent_counts = df_calc["감성"].value_counts().to_dict()
    pos_cnt = sent_counts.get("긍정", 0)
    neg_cnt = sent_counts.get("부정", 0)
    neu_cnt = sent_counts.get("중립", 0)
    pos_pct = (pos_cnt / total_records) * 100
    neg_pct = (neg_cnt / total_records) * 100
    neu_pct = (neu_cnt / total_records) * 100
    sent_str = f"- 긍정: {pos_cnt:,}건 ({pos_pct:.1f}%)\n- 중립: {neu_cnt:,}건 ({neu_pct:.1f}%)\n- 부정: {neg_cnt:,}건 ({neg_pct:.1f}%)"
        
    # 주요 출처 도메인 Top 5
    top_domains = df_calc["출처_도메인"].value_counts().head(5).to_dict()
    domain_str = "\n".join([f"- **{dom}**: {cnt:,}건" for dom, cnt in top_domains.items()])
        
    # 주요 키워드 Top 10
    all_texts = df["제목"].tolist() + df["요약/내용"].tolist()
    tokens = extract_tokens(all_texts)
    top10_tokens = tokens.most_common(10)
    token_str = "\n".join([f"{i+1}. **{word}** ({cnt}회)" for i, (word, cnt) in enumerate(top10_tokens)])
    
    report_md = f"""# 📊 네이버 마켓 인사이트 EDA 종합 분석 보고서

**작성 일시**: `{now_str}`  
**분석 대상 검색어**: `{kw_list_str}`  
**총 수집 데이터 건수**: `{total_records:,}건`

---

## 1. 📌 수집 및 분석 개요
본 보고서는 네이버 클라우드 플랫폼(NAVER API HUB)에서 수집된 검색 데이터 및 데이터랩 트렌드 지표를 바탕으로 작성된 탐색적 데이터 분석(EDA) 종합 보고서입니다.

---

## 2. 📊 카테고리 및 검색어별 점유 현황

### 2.1 카테고리별 데이터 수집 건수
{cat_summary_str}

### 2.2 검색어별 데이터 비중
{kw_summary_str}

---

## 3. 💡 감성 반응 및 시장 평판 분석
전체 수집된 텍스트(제목 및 본문 요약문)의 키워드 감성 반응 분석 결과입니다.

{sent_str}

**인사이트 종합 해석**:
- 긍정 감성 비중이 {pos_pct:.1f}%로 가장 주된 반응을 형성하고 있으며, 부정적 여론 비중은 {neg_pct:.1f}% 수준으로 집계되었습니다.

---

## 4. 🌐 주요 정보 출처 도메인 Top 5
{domain_str}

---

## 5. 🔥 최다 빈출 핵심 키워드 Top 10
{token_str}

---

## 6. 📝 종합 결론 및 제안
1. **검색 관심도 추이**: 입력된 검색어 그룹 중 `{max(kw_summary, key=kw_summary.get)}` 관련 정보가 가장 높은 게시물 수와 사용자 관심도를 기록하고 있습니다.
2. **채널 마케팅 전략**: 주요 출처 도메인 분석에 의거하여 Top 채널 플랫폼을 중심으로 콘텐츠 확산 전략을 집중할 필요가 있습니다.
3. **콘텐츠 핵심 단어 활용**: 빈출 단어 상위 10개 키워드를 모니터링하여 고객이 많이 찾는 핵심 테마에 부합하는 홍보 텍스트 생성을 권장합니다.

---
*본 보고서는 네이버 마켓 인사이트 대시보드 자동 분석 엔진에 의해 생성되었습니다.*
"""
    return report_md
