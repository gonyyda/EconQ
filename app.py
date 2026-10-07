import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from hankyung_news import (
    get_hankyung_today_articles,
    filter_economic_articles,
    select_top_economic_issues
)

from dashboard import INDICATORS, show_dashboard
from style import apply_style, show_masthead
from storage import add_scrap, init_storage, is_scrapped, remove_scrap, scrap_id
from study import show_scrap_tab, show_study_tab

# -----------------------------
# 기본 설정
# -----------------------------

st.set_page_config(
    page_title="EconQ",
    page_icon="📊",
    layout="wide"
)

load_dotenv()

# 로컬에서는 .env 우선
api_key = os.getenv("OPENAI_API_KEY")

# 배포 환경에서는 Streamlit Secrets
if not api_key:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("OpenAI API 키를 찾을 수 없습니다.")
    st.stop()

client = OpenAI(api_key=api_key)


# -----------------------------
# 오늘의 주요 이슈 불러오기
# -----------------------------

@st.cache_data(ttl=1800)
def get_today_issues():

    articles = get_hankyung_today_articles()

    filtered_articles = filter_economic_articles(
        articles
    )

    if not filtered_articles:
        return []

    issues = select_top_economic_issues(
        filtered_articles
    )

    return issues


# -----------------------------
# EconQ 분석 함수
# -----------------------------

def analyze_news(news_text):

    indicator_list = "\n".join(
        f"- {name}"
        for name in INDICATORS
    )

    prompt = f"""
당신은 경제·금융 시사 이슈를 분석하고 설명하는 AI입니다.

사용자가 제공한 경제 뉴스 기사 또는 시사 이슈를 바탕으로,
단순 요약이 아니라 경제적 배경, 인과관계, 시장 영향,
그리고 독자가 자연스럽게 떠올릴 만한 후속 질문과 답변까지 생성하세요.

반드시 유효한 JSON 형식만 출력하세요.

아래 JSON 구조와 key 이름을 그대로 사용하세요.

{{
  "title": "",
  "category": "",
  "summary": [],
  "importance": "",
  "facts": [],
  "ai_interpretations": [],
  "background": [
    {{
      "term": "",
      "explanation": ""
    }}
  ],
  "causal_chain": [],
  "causal_graph": {{
    "nodes": [
      {{
        "id": "",
        "label": "",
        "stage": ""
      }}
    ],
    "edges": [
      {{
        "from": "",
        "to": ""
      }}
    ]
  }},
  "key_figures": [
    {{
      "label": "",
      "value": "",
      "change": ""
    }}
  ],
  "related_indicators": [],
  "market_impacts": [
    {{
      "market": "",
      "direction": "",
      "reason": ""
    }}
  ],
  "questions": [
    {{
      "type": "",
      "question": "",
      "why_important": "",
      "answer": ""
    }}
  ],
  "further_thinking": [],
  "flashcards": [
    {{
      "category": "",
      "front": "",
      "back": ""
    }}
  ],
  "ox_quiz": [
    {{
      "statement": "",
      "answer": "",
      "explanation": ""
    }}
  ]
}}

## category

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

여러 카테고리를 결합하지 마세요.

## summary

기사 또는 이슈의 핵심 내용을 3~5개의 짧은 문장으로 정리하세요.

## importance

이 이슈가 경제·금융 측면에서 왜 중요한지 2~4문장으로 설명하세요.

## facts

입력 자료에서 직접 확인할 수 있는 핵심 사실 5~7개만 작성하세요.

기사에 없는 내용은 사실처럼 작성하지 마세요.

## ai_interpretations

입력된 사실을 바탕으로 한 핵심 경제적 해석을 3~5개 작성하세요.

반드시 아래와 같은 불확실성 표현을 사용하세요.

- "~할 수 있다"
- "~가능성이 있다"
- "~압력이 생길 수 있다"

기사에서 직접 확인된 사실처럼 단정하지 마세요.

## background

내용을 이해하는 데 필요한 핵심 경제 개념을 1~4개 선택하세요.

각 항목에는 다음을 작성하세요.

- term
- explanation

경제 초중급자가 이해할 수 있도록 쉽게 설명하세요.

## causal_chain

경제적 인과관계를 단계별로 작성하세요.

각 배열 항목에는 하나의 단계만 작성하세요.

각 문자열 안에 "→" 기호를 넣지 마세요.

## causal_graph

causal_chain의 흐름을 그림으로 그릴 수 있도록 노드와 화살표로 표현하세요.

- nodes는 5~8개, 각 label은 20자 이내의 짧은 명사형 표현
- id는 "n1", "n2"처럼 작성
- stage는 반드시 "원인", "전달경로", "결과" 중 하나
- edges의 from, to에는 nodes의 id만 사용
- 하나의 원인이 여러 결과로 갈라지면 화살표를 여러 개로 나누세요.

## key_figures

입력 자료에 숫자로 명시된 핵심 수치를 최대 4개 작성하세요.

- label: 수치 이름 (예: "기준금리")
- value: 단위를 포함한 값 (예: "3.0%")
- change: 자료에 명시된 변화폭 (예: "+0.25%p"), 없으면 빈 문자열

입력 자료에 없는 숫자는 절대 만들지 마세요. 수치가 없으면 빈 배열로 두세요.

## related_indicators

이 이슈와 관련성이 높은 시장 지표를 아래 목록에서 2~3개 고르세요.

목록에 있는 이름을 그대로 사용하세요.

{indicator_list}

## market_impacts

관련성이 높은 시장이나 경제주체만 분석하세요.

각 항목에는 다음을 작성하세요.

- market
- direction
- reason

direction은 가급적 아래 중 하나를 사용하세요.

- 긍정적 영향 가능
- 부정적 영향 가능
- 상승 압력
- 하락 압력
- 변동성 확대 가능
- 영향 불확실

## questions

독자가 해당 내용을 읽은 뒤 자연스럽게 떠올릴 가능성이 높은 질문을
정확히 7개 생성하세요.

type은 반드시 아래 중 하나만 사용하세요.

- 개념
- 인과관계
- 확장
- 반대상황
- 한국경제
- 투자시장

여러 유형이 골고루 섞이도록 구성하세요.

질문은 최대한 중복되지 않게 작성하세요.

단순 사실 확인 질문보다 아래 형태를 우선하세요.

- 왜?
- 어떻게?
- 그렇다면?
- 반대로?
- 한국에는 어떤 영향이 있을까?
- 어떤 조건에서는 결과가 달라질까?

각 질문에는 다음을 모두 작성하세요.

- type
- question
- why_important
- answer

## further_thinking

정확히 2개만 작성하세요.

단순 내용 반복이 아니라 한 단계 더 생각해볼 수 있는 포인트를 작성하세요.

## flashcards

이 이슈를 계기로 외워둘 만한 지식을 암기용 카드로 5~7개 만드세요.

- category는 반드시 "경제개념", "금융상품", "시사상식" 중 하나
- front: 짧은 질문 또는 용어 (예: "기준금리란?")
- back: 2~3문장의 정확하고 쉬운 설명
- background에서 다룬 핵심 개념을 포함하세요.
- 이 기사가 아니어도 통하는 일반 지식을 다루세요.
  특정 날짜의 수치처럼 금방 바뀌는 내용은 넣지 마세요.

## ox_quiz

같은 지식을 확인하는 OX 문제를 5~6개 만드세요.

- statement: 참 또는 거짓이 분명히 갈리는 한 문장
- answer: "O" 또는 "X"
- explanation: 왜 그런지 1~2문장으로 설명
- O와 X가 비슷한 비율로 섞이게 하세요.
- 의견이 갈리거나 전망에 해당하는 내용은 문제로 내지 마세요.

## 전체 원칙

1. 입력된 자료에 없는 사실을 임의로 만들지 마세요.
2. 확인된 사실과 AI의 추가 해석을 반드시 구분하세요.
3. 숫자는 임의로 변경하지 마세요.
4. 전망은 단정하지 마세요.
5. 경제적 인과관계를 지나치게 단순화하지 마세요.
6. JSON 이외의 텍스트는 출력하지 마세요.
7. trailing comma를 사용하지 마세요.
8. 반드시 파싱 가능한 올바른 JSON만 출력하세요.

### 입력 기사 또는 이슈

{news_text}
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    result_text = response.output_text

    return json.loads(result_text)


# -----------------------------
# 분석 결과 표시 함수
# -----------------------------

def show_analysis(data):

    st.divider()

    st.header(data["title"])

    st.caption(
        f"카테고리: {data['category']}"
    )

    if is_scrapped(data):

        st.button(
            "📌 스크랩됨 · 해제하기",
            on_click=remove_scrap,
            args=(scrap_id(data),)
        )

    else:

        st.button(
            "📌 스크랩하기",
            type="primary",
            on_click=add_scrap,
            args=(data,)
        )

    st.info(
        data["importance"]
    )

    show_dashboard(data)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📝 핵심 정리",
            "🔎 사실 vs AI 해석",
            "🔗 인과관계",
            "🤔 궁금한 질문",
            "💡 한 단계 더"
        ]
    )

    # -------------------------
    # TAB 1 : 핵심 정리
    # -------------------------

    with tab1:

        st.subheader("핵심 요약")

        for item in data["summary"]:
            st.write(f"• {item}")

        st.divider()

        st.subheader("알아두면 좋은 경제 개념")

        for item in data["background"]:

            with st.expander(item["term"]):
                st.write(item["explanation"])

        st.divider()

        st.subheader("시장 영향")

        for i, impact in enumerate(data["market_impacts"]):

            with st.container(border=True, key=f"card_impact_{i}"):

                st.markdown(
                    f"**{impact['market']}**"
                )

                st.write(
                    f"방향: {impact['direction']}"
                )

                st.write(
                    impact["reason"]
                )


    # -------------------------
    # TAB 2 : 사실 vs AI 해석
    # -------------------------

    with tab2:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "📰 확인된 사실"
            )

            for fact in data["facts"]:

                st.write(
                    f"• {fact}"
                )

        with col2:

            st.subheader(
                "🤖 AI의 추가 해석"
            )

            for item in data[
                "ai_interpretations"
            ]:

                st.write(
                    f"• {item}"
                )


    # -------------------------
    # TAB 3 : 인과관계
    # -------------------------

    with tab3:

        st.subheader("경제적 흐름")

        causal_chain = data["causal_chain"]

        for i, step in enumerate(causal_chain):

            with st.container(border=True, key=f"card_step_{i}"):

                st.caption(
                    f"STEP {i + 1}"
                )

                st.markdown(
                    f"**{step}**"
                )

            if i < len(causal_chain) - 1:

                st.markdown(
                    "<div style='text-align:center; font-size:24px;'>↓</div>",
                    unsafe_allow_html=True
                )


    # -------------------------
    # TAB 4 : 궁금한 질문
    # -------------------------

    with tab4:

        st.subheader(
            "이 내용을 읽으면 이런 점이 궁금할 수 있어요."
        )

        st.caption(
            "질문을 클릭하면 EconQ가 왜 중요한 질문인지와 답변을 설명합니다."
        )

        question_icons = {
            "개념": "💡",
            "인과관계": "🔗",
            "확장": "🔭",
            "반대상황": "🔄",
            "한국경제": "🇰🇷",
            "투자시장": "📈"
        }

        for q in data["questions"]:

            icon = question_icons.get(
                q["type"],
                "❓"
            )

            title = (
                f"{icon} [{q['type']}] "
                f"{q['question']}"
            )

            with st.expander(title):

                st.markdown(
                    "🎯 **왜 이 질문이 중요할까요?**"
                )

                st.write(
                    q["why_important"]
                )

                st.markdown(
                    "💬 **EconQ의 답변**"
                )

                st.write(
                    q["answer"]
                )


    # -------------------------
    # TAB 5 : 한 단계 더
    # -------------------------

    with tab5:

        st.subheader(
            "한 단계 더 생각해보기"
        )

        for i, item in enumerate(
            data["further_thinking"]
        ):

            with st.container(border=True, key=f"card_think_{i}"):

                st.write(
                    f"💡 {item}"
                )


# -----------------------------
# 메인 화면
# -----------------------------

apply_style()

init_storage()

show_masthead()

st.write(
    """
오늘의 주요 경제 이슈를 선택하거나,
직접 읽고 싶은 경제 기사를 입력해보세요.
"""
)


# -----------------------------
# 메인 탭
# -----------------------------

main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(
    [
        "🔥 오늘의 주요 이슈",
        "📰 직접 기사 분석",
        "📌 스크랩",
        "🧠 학습"
    ]
)


# -----------------------------
# 오늘의 주요 이슈
# -----------------------------

with main_tab1:

    st.subheader(
        "오늘 꼭 알아둘 경제 이슈"
    )

    st.caption(
        "한국경제의 오늘 기사 중 EconQ가 중요한 경제·금융 이슈를 선정합니다."
    )

    try:

        with st.spinner(
            "오늘의 주요 이슈를 불러오는 중..."
        ):

            today_issues = get_today_issues()

        if not today_issues:

            st.warning(
                "오늘의 주요 이슈를 찾지 못했습니다."
            )

        else:

            issue_titles = [
                issue["title"]
                for issue in today_issues
            ]

            selected_title = st.selectbox(
                "분석할 이슈를 선택하세요.",
                issue_titles
            )

            selected_issue = next(
                issue
                for issue in today_issues
                if issue["title"] == selected_title
            )

            st.markdown(
                f"""
**카테고리:** {selected_issue['category']}

**왜 중요한가?**  
{selected_issue['why_important']}

**대표 기사:**  
{selected_issue['article_title']}
"""
            )

            st.link_button(
                "📰 원문 기사 보기",
                selected_issue["url"]
            )

            if st.button(
                "🔥 이 이슈 분석하기",
                type="primary"
            ):

                issue_text = f"""
오늘의 주요 경제 이슈를 분석하세요.

이슈 제목:
{selected_issue['title']}

대표 기사 제목:
{selected_issue['article_title']}

이 이슈가 중요한 이유:
{selected_issue['why_important']}
"""

                with st.spinner(
                    "EconQ가 이 이슈를 분석하고 있습니다..."
                ):

                    try:

                        data = analyze_news(
                            issue_text
                        )

                        st.session_state[
                            "analysis"
                        ] = data

                    except json.JSONDecodeError:

                        st.error(
                            "AI 응답을 JSON으로 변환하지 못했습니다. 다시 시도해주세요."
                        )

                    except Exception as e:

                        st.error(
                            f"오류가 발생했습니다: {e}"
                        )

    except Exception as e:

        st.error(
            f"오늘의 주요 이슈를 불러오지 못했습니다: {e}"
        )


# -----------------------------
# 직접 기사 분석
# -----------------------------

with main_tab2:

    st.subheader(
        "직접 기사 입력"
    )

    news_text = st.text_area(
        "분석할 경제 기사 또는 시사 이슈를 입력하세요.",
        height=200,
        placeholder="여기에 기사 본문을 붙여넣으세요."
    )

    if st.button(
        "🔍 기사 분석하기"
    ):

        if not news_text.strip():

            st.warning(
                "분석할 기사 내용을 입력해주세요."
            )

        else:

            with st.spinner(
                "EconQ가 기사를 분석하고 있습니다..."
            ):

                try:

                    data = analyze_news(
                        news_text
                    )

                    st.session_state[
                        "analysis"
                    ] = data

                except json.JSONDecodeError:

                    st.error(
                        "AI 응답을 JSON으로 변환하지 못했습니다. 다시 시도해주세요."
                    )

                except Exception as e:

                    st.error(
                        f"오류가 발생했습니다: {e}"
                    )


# -----------------------------
# 스크랩 · 학습
# -----------------------------

with main_tab3:

    show_scrap_tab()

with main_tab4:

    show_study_tab()


# -----------------------------
# 분석 결과 출력
# -----------------------------

if "analysis" in st.session_state:

    show_analysis(
        st.session_state["analysis"]
    )