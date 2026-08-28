import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import json


# -----------------------------
# 기본 설정
# -----------------------------

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# -----------------------------
# 한국경제 오늘 기사 목록 수집
# -----------------------------

def get_hankyung_today_articles():

    today = datetime.now().strftime("%Y/%m/%d")

    url = f"https://www.hankyung.com/sitemap/{today}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    articles = []

    for link in soup.find_all("a"):

        title = link.get_text(
            " ",
            strip=True
        )

        href = link.get("href")

        if not title or not href:
            continue

        # 기사 링크만 수집
        if "/article/" not in href:
            continue

        if href.startswith("/"):
            href = "https://www.hankyung.com" + href

        articles.append(
            {
                "title": title,
                "url": href
            }
        )

    # -----------------------------
    # 중복 제거
    # -----------------------------

    unique_articles = []

    seen = set()

    for article in articles:

        if article["url"] not in seen:

            seen.add(article["url"])

            unique_articles.append(article)

    return unique_articles


# -----------------------------
# 경제 관련 기사 후보 1차 필터링
# -----------------------------

def filter_economic_articles(articles):

    keywords = [
        "금리",
        "한국은행",
        "연준",
        "Fed",
        "환율",
        "달러",
        "원화",
        "물가",
        "CPI",
        "PCE",
        "인플레이션",
        "GDP",
        "성장률",
        "수출",
        "수입",
        "무역",
        "증시",
        "코스피",
        "코스닥",
        "주가",
        "채권",
        "국채",
        "부동산",
        "주택",
        "대출",
        "가계부채",
        "유가",
        "원유",
        "반도체",
        "관세",
        "재정",
        "세제",
        "금융",
        "은행",
        "보험",
        "정부",
        "기획재정부",
        "금융위원회"
    ]

    filtered = []

    for article in articles:

        title = article["title"]

        if any(
            keyword.lower() in title.lower()
            for keyword in keywords
        ):
            filtered.append(article)

    return filtered


# -----------------------------
# GPT가 오늘의 주요 경제 이슈 5개 선정
# -----------------------------

def select_top_economic_issues(articles):

    # 너무 많은 기사를 한 번에 보내지 않도록 제한
    articles = articles[:120]

    article_text = "\n".join(
        [
            f"{i + 1}. {article['title']} | {article['url']}"
            for i, article in enumerate(articles)
        ]
    )

    prompt = f"""
당신은 경제·금융 전문 뉴스 편집자입니다.

아래는 오늘 한국경제에 게시된 기사 후보 목록입니다.

경제·금융을 공부하는 사람이
오늘 반드시 알아둘 만한 핵심 경제 이슈를
정확히 5개 선정하세요.

단순히 기사 5개를 고르는 것이 아니라,
비슷한 사건을 다룬 기사들은 하나의 '이슈'로 묶어야 합니다.

예를 들어

- 한국은행 기준금리 관련 기사 여러 개
- 총재 기자회견 기사
- 채권시장 반응 기사

가 함께 있다면 이를

"한국은행 기준금리 결정과 향후 통화정책"

이라는 하나의 이슈로 묶을 수 있습니다.

## 중요도 판단 기준

1. 한국 경제 또는 글로벌 경제 전반에 미치는 영향
2. 금리·환율·물가·주식·채권 등 금융시장 파급효과
3. 한국은행·미 연준·정부 등 주요 정책기관 관련성
4. 일회성 기업 홍보보다 거시경제적으로 중요한 이슈 우선
5. 시장 참여자들이 당일 주목할 가능성이 높은 이슈
6. 비슷한 내용의 기사는 하나의 이슈로 통합
7. 연예·사건사고·생활정보 등은 제외
8. 지나치게 특정 기업에만 국한된 기사는 우선순위를 낮출 것
9. 서로 다른 분야의 이슈가 어느 정도 포함되도록 할 것

반드시 JSON만 출력하세요.

아래 구조를 정확히 사용하세요.

{{
  "issues": [
    {{
      "title": "",
      "category": "",
      "why_important": "",
      "article_title": "",
      "url": ""
    }}
  ]
}}

category는 반드시 아래 값 중 하나만 사용하세요.

- 금리
- 환율
- 물가
- 주식
- 채권
- 부동산
- 금융정책
- 재정정책
- 기업
- 산업
- 원자재
- 국제경제
- 기타

정확히 5개 이슈만 반환하세요.

article_title과 url에는
해당 이슈를 가장 잘 대표하는 기사 하나를 선택해서 넣으세요.

JSON 이외의 설명은 절대 출력하지 마세요.

### 오늘의 기사 후보

{article_text}
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    result_text = response.output_text

    data = json.loads(result_text)

    return data["issues"]


# -----------------------------
# 테스트 실행
# -----------------------------

if __name__ == "__main__":

    print("한국경제 오늘 기사 수집 중...")

    articles = get_hankyung_today_articles()

    print(
        f"전체 수집 기사 수: {len(articles)}"
    )

    filtered_articles = filter_economic_articles(
        articles
    )

    print(
        f"경제 관련 후보 기사 수: {len(filtered_articles)}"
    )

    if len(filtered_articles) == 0:

        print(
            "경제 관련 기사 후보를 찾지 못했습니다."
        )

    else:

        print()
        print("EconQ가 오늘의 주요 이슈를 선정합니다...")
        print()

        try:

            issues = select_top_economic_issues(
                filtered_articles
            )

            print(
                f"선정된 주요 이슈 수: {len(issues)}"
            )

            print()
            print("=" * 60)
            print("오늘의 EconQ")
            print("=" * 60)

            for i, issue in enumerate(
                issues,
                start=1
            ):

                print()
                print(
                    f"{i}. {issue['title']}"
                )

                print(
                    f"카테고리: {issue['category']}"
                )

                print(
                    f"중요한 이유: {issue['why_important']}"
                )

                print(
                    f"대표 기사: {issue['article_title']}"
                )

                print(
                    f"링크: {issue['url']}"
                )

                print("-" * 60)

        except json.JSONDecodeError:

            print(
                "GPT 응답을 JSON으로 변환하지 못했습니다."
            )

        except Exception as e:

            print(
                f"오류가 발생했습니다: {e}"
            )