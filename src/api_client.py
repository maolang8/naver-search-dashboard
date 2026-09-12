import os
import requests
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

CATEGORY_MAP = {
    "뉴스": "news",
    "블로그": "blog",
    "웹문서": "webkr",
    "이미지": "image",
    "지식iN": "kin",
    "지역": "local",
    "카페글": "cafearticle",
    "백과사전": "encyc"
}

def clean_html(raw_html):
    if not isinstance(raw_html, str):
        return ""
    cleaner = re.compile('<.*?>|&quot;|&amp;|&lt;|&gt;|<b>|</b>')
    return re.sub(cleaner, '', raw_html)

def fetch_naver_search(keyword, category="news", display=100, start=1, sort="sim"):
    client_id = os.getenv("NAVER_CLIENT_ID", NAVER_CLIENT_ID)
    client_secret = os.getenv("NAVER_CLIENT_SECRET", NAVER_CLIENT_SECRET)
    
    if not client_id or not client_secret or client_id == "your_naver_client_id_here":
        raise ValueError("네이버 클라우드 API 인증 정보가 환경변수에 설정되지 않았습니다.")
        
    # NCloud Naver API Hub 검색 Endpoint
    url = f"https://naverapihub.apigw.ntruss.com/search/v1/{category}"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id.strip(),
        "X-NCP-APIGW-API-KEY": client_secret.strip()
    }
    params = {
        "query": keyword,
        "display": display,
        "start": start,
        "sort": sort
    }
    
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        # 혹시 오픈 API로 시도하는 사용자를 위한 Fallback 처리
        fallback_url = f"https://openapi.naver.com/v1/search/{category}.json"
        fallback_headers = {
            "X-Naver-Client-Id": client_id.strip(),
            "X-Naver-Client-Secret": client_secret.strip()
        }
        res_fb = requests.get(fallback_url, headers=fallback_headers, params=params)
        if res_fb.status_code == 200:
            res = res_fb
        else:
            # 401 등 특정 API 미활성화 오류시 경고 로그 후 빈 DF 반환하여 전체 분석 중단 방지
            print(f"[{category}] API 호출 실패 ({res.status_code}): {res.text}")
            return pd.DataFrame()
        
    data = res.json()
    items = data.get("items", [])
    
    processed_items = []
    for item in items:
        title = clean_html(item.get("title", ""))
        description = clean_html(item.get("description", ""))
        link = item.get("link", "") or item.get("originallink", "")
        pub_date = item.get("pubDate", "") or item.get("postdate", "")
        
        processed_items.append({
            "검색어": keyword,
            "카테고리": category,
            "제목": title,
            "요약/내용": description,
            "링크": link,
            "날짜/일시": pub_date
        })
        
    return pd.DataFrame(processed_items)

def fetch_datalab_trend(keywords, start_date, end_date, time_unit="date", device=None, gender=None, ages=None):
    client_id = os.getenv("NAVER_CLIENT_ID", NAVER_CLIENT_ID)
    client_secret = os.getenv("NAVER_CLIENT_SECRET", NAVER_CLIENT_SECRET)
    
    if not client_id or not client_secret or client_id == "your_naver_client_id_here":
        raise ValueError("네이버 클라우드 API 인증 정보가 환경변수에 설정되지 않았습니다.")
        
    url = "https://naverapihub.apigw.ntruss.com/search-trend/v1/search"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id.strip(),
        "X-NCP-APIGW-API-KEY": client_secret.strip(),
        "Content-Type": "application/json"
    }
    
    keyword_groups = []
    for kw in keywords:
        kw_clean = kw.strip()
        if kw_clean:
            keyword_groups.append({
                "groupName": kw_clean,
                "keywords": [kw_clean]
            })
            
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups
    }
    if device and device != "전체":
        body["device"] = "pc" if device == "PC" else "mo"
    if gender and gender != "전체":
        body["gender"] = "m" if gender == "남성" else "f"
    if ages and "전체" not in ages:
        body["ages"] = ages
    
    res = requests.post(url, headers=headers, json=body)
    if res.status_code != 200:
        # 데이터랩 오픈 API Fallback
        fallback_url = "https://openapi.naver.com/v1/datalab/search"
        fallback_headers = {
            "X-Naver-Client-Id": client_id.strip(),
            "X-Naver-Client-Secret": client_secret.strip(),
            "Content-Type": "application/json"
        }
        res_fb = requests.post(fallback_url, headers=fallback_headers, json=body)
        if res_fb.status_code == 200:
            res = res_fb
        else:
            raise Exception(f"DataLab API 호출 실패 ({res.status_code}): {res.text}")
        
    data = res.json()
    results = data.get("results", [])
    
    records = []
    for result in results:
        group_name = result.get("title")
        for item in result.get("data", []):
            records.append({
                "날짜": item.get("period"),
                "검색어": group_name,
                "상대적 검색량": item.get("ratio")
            })
            
    return pd.DataFrame(records)
