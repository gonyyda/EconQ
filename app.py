import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# -----------------------------
# 기본 설정
# -----------------------------

load_dotenv()

api_key = st.secrets.get(
    "OPENAI_API_KEY",
    os.getenv("OPENAI_API_KEY")
)

client = OpenAI(api_key=api_key)

st.set_page_config(
    page_title="EconQ",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# 오늘의 이슈 데이터
# 텔레그램 자동연결 전 임시 수동 입력
# -----------------------------

today_issues = [
    {
        "title": "한국은행 기준금리 인상",
        "category": "금리",
        "content": """
한국은행이 기준금리를 인상했다.
강한 성장세와 물가 압력을 고려해 선제적 인상이 필요하다는 입장을 밝혔다.
향후 추가 금리 인상 가능성에도 시장의 관심이 집중되고 있다.
"""
    },
    {
        "title": "미국 물가 둔화와 연준 금리 전망",
        "category": "물가",
        "content": """
미국 물가 지표가 시장 예상보다 낮게 발표되면서
연방준비제도의 금리 인하 가능성에 대한 기대가 확대됐다.
이에 미국 국채금리와 달러화가 하락 압력을 받았다.
"""
    },
    {
        "title": "국제유가 상승과 물가 부담",
        "category": "원자재",
        "content": """
국제유가가 상승하면서 글로벌 물가 압력이 다시 높아질 수 있다는 우려가 제기됐다.
유가 상승은 기업의 비용과 소비자물가에 영향을 줄 수 있어
주요국 통화정책에도 변수로 작용할 가능성이 있다.
"""
    }
]

# -----------------------------
# EconQ 분석 함수
# -----------------------------

def analyze_news(news_text):

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
  "further_thinking": []
}}

category는 반드시 다음 중 하나만 사용하세요.

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

summary는 기사 핵심 내용을 3~5개의 짧은 문장으로 정리하세요.

importance는 이 이슈가 경제·금융 측면에서 왜 중요한지
2~4문장으로 설명하세요.

facts는 기사에서 직접 확인되는 핵심 사실 5~7개만 작성하세요.
기사에 없는 해석이나 전망은 넣지 마세요.

ai_interpretations는 기사 내용을 바탕으로 한 핵심 해석 3~5개만 작성하세요.

반드시 다음과 같은 불확실성 표현을 사용하세요.

- "~할 수 있다"
- "~가능성이 있다"
- "~압력이 생길 수 있다"

기사에서 확인된 사실처럼 단정하지 마세요.

background는 기사 이해에 필요한 경제 개념 1~4개만 작성하세요.

causal_chain은 경제적 인과관계를 단계별로 나누세요.
각 문자열 안에 "→" 기호를 넣지 마세요.

market_impacts는 실제 관련성이 높은 시장이나 경제주체만 분석하세요.

direction은 가급적 아래 중 하나를 사용하세요.

- 긍정적 영향 가능
- 부정적 영향 가능
- 상승 압력
- 하락 압력
- 변동성 확대 가능
- 영향 불확실

questions는 정확히 7개 생성하세요.

question의 type은 반드시 다음 중 하나만 사용하세요.

- 개념
- 인과관계
- 확장
- 반대상황
- 한국경제
- 투자시장

질문은 서로 최대한 중복되지 않게 작성하세요.

각 질문에는 다음을 모두 작성하세요.

- type
- question
- why_important
- answer

further_thinking은 정확히 2개만 작성하세요.

기사에 없는 사실을 임의로 만들지 마세요.
기사에서 확인된 사실과 AI의 추가 해석을 반드시 구분하세요.
숫자는 임의로 변경하지 마세요.
전망은 단정하지 마세요.
JSON 이외의 텍스트는 출력하지 마세요.
trailing comma를 사용하지 마세요.
반드시 파싱 가능한 올바른 JSON만 출력하세요.

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
# 분석 결과 출력 함수
# -----------------------------

def show_analysis(data):

    st.divider()

    st.header(data["title"])
    st.caption(f"카테고리: {data['category']}")

    st.info(data["importance"])

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

        for impact in data["market_impacts"]:

            st.markdown(f"**{impact['market']}**")
            st.write(f"방향: {impact['direction']}")
            st.write(impact["reason"])
            st.write("")

    # -------------------------
    # TAB 2 : 사실 vs AI 해석
    # -------------------------

    with tab2:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("📰 기사에서 확인된 사실")

            for fact in data["facts"]:
                st.write(f"• {fact}")

        with col2:

            st.subheader("🤖 AI의 추가 해석")

            for item in data["ai_interpretations"]:
                st.write(f"• {item}")

    # -------------------------
    # TAB 3 : 인과관계
    # -------------------------

    with tab3:

        st.subheader("경제적 흐름")

        causal_chain = data["causal_chain"]

        for i, step in enumerate(causal_chain):

            st.markdown(f"### {i + 1}. {step}")

            if i < len(causal_chain) - 1:
                st.markdown("↓")

    # -------------------------
    # TAB 4 : 궁금한 질문
    # -------------------------

    with tab4:

        st.subheader("이 이슈를 이해하면 이런 점이 궁금할 수 있어요.")

        st.caption(
            "질문을 클릭하면 EconQ가 왜 중요한 질문인지와 답변을 설명합니다."
        )

        for q in data["questions"]:

            title = f"[{q['type']}] {q['question']}"

            with st.expander(title):

                st.markdown("**왜 이 질문이 중요할까요?**")
                st.write(q["why_important"])

                st.markdown("**답변**")
                st.write(q["answer"])

    # -------------------------
    # TAB 5 : 한 단계 더
    # -------------------------

    with tab5:

        st.subheader("한 단계 더 생각해보기")

        for item in data["further_thinking"]:
            st.write(f"💡 {item}")


# -----------------------------
# 메인 화면
# -----------------------------

st.title("📊 EconQ")

st.subheader(
    "경제 뉴스를 읽고, 다음 질문까지 생각합니다."
)

st.write(
    """
    오늘의 주요 경제 이슈를 선택하거나,
    직접 읽고 싶은 경제 기사를 입력해보세요.
    """
)

st.divider()


# -----------------------------
# 메인 진입 탭
# -----------------------------

main_tab1, main_tab2 = st.tabs(
    [
        "🔥 오늘의 주요 이슈",
        "📰 직접 기사 분석"
    ]
)


# -----------------------------
# 오늘의 주요 이슈
# -----------------------------

with main_tab1:

    st.subheader("오늘 꼭 알아둘 경제 이슈")

    st.caption(
        "주요 경제 이슈 중 하나를 선택하면 EconQ가 자동으로 분석합니다."
    )

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
"""
    )

    if st.button(
        "🔥 이 이슈 분석하기",
        type="primary"
    ):

        with st.spinner(
            "EconQ가 오늘의 이슈를 분석하고 있습니다..."
        ):

            try:

                data = analyze_news(
                    selected_issue["content"]
                )

                st.session_state["analysis"] = data

            except json.JSONDecodeError:

                st.error(
                    "AI 응답을 JSON으로 변환하지 못했습니다. "
                    "다시 한 번 분석해주세요."
                )

            except Exception as e:

                st.error(
                    f"오류가 발생했습니다: {e}"
                )


# -----------------------------
# 직접 기사 분석
# -----------------------------

with main_tab2:

    st.subheader("직접 기사 입력")

    news_text = st.text_area(
        "분석할 경제 기사 또는 시사 이슈를 입력하세요.",
        height=300,
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

                    data = analyze_news(news_text)

                    st.session_state["analysis"] = data

                except json.JSONDecodeError:

                    st.error(
                        "AI 응답을 JSON으로 변환하지 못했습니다. "
                        "다시 한 번 분석해주세요."
                    )

                except Exception as e:

                    st.error(
                        f"오류가 발생했습니다: {e}"
                    )


# -----------------------------
# 분석 결과
# -----------------------------

if "analysis" in st.session_state:

    show_analysis(
        st.session_state["analysis"]
    )