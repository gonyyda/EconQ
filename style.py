import streamlit as st
from datetime import datetime, timedelta, timezone


WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

CSS = """
<style>
[data-testid="stMainBlockContainer"] { padding-top: 4.5rem !important; max-width: 1180px; }

.eq-masthead { border-top: 3px solid #16202B; border-bottom: 1px solid #16202B; padding: 14px 0 16px; margin-bottom: 8px; }
.eq-masthead .eq-eyebrow { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px 16px; font-size: 12.5px; letter-spacing: 0.06em; color: #5B6470; }
.eq-masthead .eq-title { font-family: 'Noto Serif KR', serif; font-size: clamp(34px, 6vw, 52px); font-weight: 700; line-height: 1.1; letter-spacing: -0.02em; color: #16202B; margin: 6px 0 4px; }
.eq-masthead .eq-title span { color: #0F4C81; }
.eq-masthead .eq-tagline { font-size: 16px; color: #3A4552; margin: 0; }

/* 카드(테두리 있는 컨테이너, 수치 타일)는 종이 위에 흰 면으로 띄운다 */
[class*="st-key-card_"], [data-testid="stMetric"] { background: #FFFFFF; }
[data-testid="stExpander"] details { background: #FFFFFF; }

[data-testid="stMetricValue"] { font-family: 'Noto Serif KR', serif; font-weight: 600; font-size: 1.8rem; }

/* 탭은 신문 섹션 메뉴처럼 */
[data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #D8D2C4; }
[data-baseweb="tab"] p { font-size: 15px; font-weight: 500; }
</style>
"""


def apply_style():

    st.html(CSS)


def show_masthead():

    now = datetime.now(
        timezone(timedelta(hours=9))
    )

    today = f"{now:%Y.%m.%d} {WEEKDAYS[now.weekday()]}요일"

    st.html(
        f"""
<div class="eq-masthead">
  <div class="eq-eyebrow"><span>{today}</span><span>경제 뉴스 분석 · AI 리서치 노트</span></div>
  <div class="eq-title">Econ<span>Q</span></div>
  <p class="eq-tagline">경제 뉴스를 읽고, 다음 질문까지 생각합니다.</p>
</div>
"""
    )
