# 📈 네이버 마켓 인사이트 EDA 대시보드

네이버 클라우드 API HUB 기반 실시간 마켓 인사이트 탐색적 데이터 분석(EDA) 대시보드입니다.

## 주요 기능

- **다중 검색어 트렌드 분석** - 네이버 데이터랩 API를 활용한 검색어별 트렌드 시각화
- **카테고리별 검색 결과 수집** - 뉴스, 블로그, 쇼핑 등 8개 카테고리 데이터 수집
- **EDA 통계 분석** - 워드클라우드, 빈도 분석, 날짜별 분포 등
- **종합 보고서 자동 생성** - 마켓 인사이트 요약 보고서 (.md, CSV, Excel 내보내기)

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/maolang8/naver-search-dashboard.git
cd naver-search-dashboard
```

### 2. 가상환경 생성 및 패키지 설치

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 API 키를 입력합니다.

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 값을 입력하세요:

```
NAVER_CLIENT_ID=발급받은_클라이언트_ID
NAVER_CLIENT_SECRET=발급받은_클라이언트_시크릿
```

> 네이버 클라우드 플랫폼 API 키는 [https://www.ncloud.com/](https://www.ncloud.com/) 에서 발급받을 수 있습니다.

### 4. 앱 실행

```bash
streamlit run app.py
```

## 프로젝트 구조

```
naver-search-dashboard/
├── app.py                  # 메인 Streamlit 앱
├── src/
│   ├── api_client.py       # 네이버 API 클라이언트
│   ├── category_views.py   # 카테고리별 EDA 뷰
│   └── eda_utils.py        # EDA 유틸리티 함수
├── .streamlit/
│   └── config.toml         # Streamlit 테마 설정
├── .env.example            # 환경변수 예시
├── requirements.txt        # 패키지 의존성
└── .gitignore
```

## 사용 방법

1. 사이드바에서 **API 키 상태** 확인
2. **다중 검색어** 입력 (쉼표로 구분, 예: `인공지능, 빅데이터, 클라우드`)
3. **트렌드 조회 기간** 설정
4. **수집 카테고리** 선택
5. **🚀 데이터 수집 & 분석 시작** 버튼 클릭

## 기술 스택

- **Frontend**: Streamlit
- **데이터 처리**: Pandas, NumPy
- **시각화**: Plotly, Matplotlib, WordCloud
- **API**: 네이버 클라우드 플랫폼 (Search API, Datalab API)
