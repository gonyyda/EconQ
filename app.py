import streamlit as st
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

st.set_page_config(
    page_title="EconQ",
    page_icon="📊",
    layout="wide"
)


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

## category 규칙

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

기사의 핵심 내용을 3~5개의 짧은 문장으로 정리하세요.

기사에 나온 사실을 중심으로 작성하세요.


## importance

이 이슈가 경제·금융 측면에서 왜 중요한지
2~4문장으로 설명하세요.


## facts

기사 본문에서 직접 확인할 수 있는 핵심 사실만 작성하세요.

가장 중요한 내용 5~7개만 선택하세요.

기사에 없는 해석이나 전망은 넣지 마세요.


## ai_interpretations

기사의 사실을 바탕으로 경제적으로 추가 해석할 수 있는 내용을 작성하세요.

가장 중요한 해석 3~5개만 작성하세요.

반드시 다음과 같은 불확실성 표현을 사용하세요.

- "~할 수 있다"
- "~가능성이 있다"
- "~압력이 생길 수 있다"

기사의 사실처럼 단정하지 마세요.


## background

이 기사를 이해하는 데 필요한 핵심 경제 개념을 1~4개 선택하세요.

각 항목에는 다음을 작성하세요.

- term
- explanation

경제 초중급자가 이해할 수 있도록 쉽게 설명하세요.


## causal_chain

경제적 인과관계를 단계별로 작성하세요.

각 배열 항목에는 하나의 단계만 작성하세요.

예:

[
  "물가 상승률이 예상보다 낮게 발표됨",
  "금리 인하 기대 확대",
  "국채금리 하락 압력",
  "달러 약세 압력"
]

각 문자열 안에 "→" 기호를 넣지 마세요.


## market_impacts

실제로 관련성이 높은 시장이나 경제주체만 분석하세요.

각 항목에는 다음을 작성하세요.

- market
- direction
- reason

direction은 가급적 다음 중 하나를 사용하세요.

- 긍정적 영향 가능
- 부정적 영향 가능
- 상승 압력
- 하락 압력
- 변동성 확대 가능
- 영향 불확실


## questions

독자가 해당 기사를 읽은 뒤
자연스럽게 떠올릴 가능성이 높은 질문을 정확히 7개 생성하세요.

type은 반드시 다음 중 하나만 사용하세요.

- 개념
- 인과관계
- 확장
- 반대상황
- 한국경제
- 투자시장

여러 유형이 최대한 골고루 섞이도록 구성하세요.

단순 사실 확인 질문보다 다음 질문을 우선하세요.

- 왜?
- 어떻게?
- 그렇다면?
- 반대로?
- 한국에는 어떤 영향?
- 어떤 조건에서는 결과가 달라질까?

각 질문에는 다음을 모두 작성하세요.

- type
- question
- why_important
- answer

answer는 경제 초중급자가 이해할 수 있도록 설명하세요.


## further_thinking

정확히 2개만 작성하세요.

기사를 단순 반복하지 말고
한 단계 더 생각해볼 수 있는 포인트를 제시하세요.


## 전체 원칙

1. 기사에 없는 사실을 임의로 만들지 마세요.
2. 기사에서 확인된 사실과 AI의 추가 해석을 구분하세요.
3. 숫자는 임의로 변경하지 마세요.
4. 전망은 단정하지 마세요.
5. JSON 이외의 텍스트는 출력하지 마세요.
6. trailing comma를 사용하지 마세요.
7. 반드시 파싱 가능한 JSON만 출력하세요.


### 입력 기사

{news_text}
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    result_text = response.output_text

    return json.loads(result_text)


# -----------------------------
# 화면
# -----------------------------

st.title("📊 EconQ")

st.subheader("경제 뉴스를 읽고, 다음 질문까지 생각합니다.")

st.write(
    """
    경제·금융 기사 내용을 입력하면  
    **핵심 내용 → 경제적 배경 → 시장 영향 → 예상 질문과 답변**까지 분석합니다.
    """
)

st.divider()


# -----------------------------
# 기사 입력
# -----------------------------

news_text = st.text_area(
    "📰 분석할 경제 기사 또는 시사 이슈를 입력하세요.",
    height=300,
    placeholder="여기에 기사 본문을 붙여넣으세요."
)


# -----------------------------
# 분석 버튼
# -----------------------------

if st.button("🔍 분석하기", type="primary"):

    if not news_text.strip():

        st.warning("분석할 기사 내용을 입력해주세요.")

    else:

        with st.spinner("EconQ가 기사를 분석하고 있습니다..."):

            try:
                data = analyze_news(news_text)

                st.session_state["analysis"] = data

            except json.JSONDecodeError:

                st.error(
                    "AI 응답을 JSON으로 변환하지 못했습니다. "
                    "다시 한 번 분석해주세요."
                )

            except Exception as e:

                st.error(f"오류가 발생했습니다: {e}")


# -----------------------------
# 분석 결과 출력
# -----------------------------

if "analysis" in st.session_state:

    data = st.session_state["analysis"]

    st.divider()

    # 제목 + 카테고리
    st.header(data["title"])

    st.caption(f"카테고리: {data['category']}")

    st.info(data["importance"])


    # -------------------------
    # 탭
    # -------------------------

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

            st.markdown(
                f"""
                **{impact['market']}**

                방향: **{impact['direction']}**

                {impact['reason']}
                """
            )


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

            for interpretation in data["ai_interpretations"]:
                st.write(f"• {interpretation}")


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

        st.subheader("이 기사를 읽으면 이런 점이 궁금할 수 있어요.")

        st.caption(
            "질문을 클릭하면 EconQ가 해당 질문이 왜 중요한지와 답변을 설명합니다."
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