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

/* 브라우저 저장소 컴포넌트는 화면에 자리를 차지하지 않게 한다 */
.st-key-econq_store_slot { position: absolute; height: 0; overflow: hidden; }

/* 플래시카드 · OX 퀴즈 카드 */
/* 뒤집히는 플래시카드 */
.eq-flip { display: block; position: relative; perspective: 1400px; cursor: pointer; margin: 6px 0 4px; }
.eq-flip input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.eq-flip-inner { display: grid; transform-style: preserve-3d; transition: transform 0.55s cubic-bezier(.2,.7,.2,1); }
.eq-flip input:checked ~ .eq-flip-inner { transform: rotateY(180deg); }
.eq-flip input:focus-visible ~ .eq-flip-inner { outline: 3px solid #C4622D; outline-offset: 4px; border-radius: 14px; }
.eq-flip-face { grid-area: 1 / 1; min-height: 300px; display: flex; flex-direction: column; gap: 16px; padding: 22px 28px 20px; border-radius: 14px; backface-visibility: hidden; -webkit-backface-visibility: hidden; box-shadow: 0 1px 2px rgba(22,32,43,.08), 0 14px 30px -14px rgba(22,32,43,.35); }
.eq-flip-front { background: #0F4C81; color: #FFFFFF; }
.eq-flip-back { background: #FFFFFF; color: #16202B; border: 1px solid #D8D2C4; transform: rotateY(180deg); }
.eq-flip-meta { display: flex; justify-content: space-between; gap: 12px; font-size: 12.5px; letter-spacing: 0.05em; opacity: 0.8; }
.eq-flip-term { flex: 1; display: flex; align-items: center; justify-content: center; text-align: center; font-family: 'Noto Serif KR', serif; font-size: clamp(24px, 4.4vw, 36px); font-weight: 700; line-height: 1.4; }
.eq-flip-answer { flex: 1; display: flex; align-items: center; font-size: clamp(16px, 2.2vw, 18.5px); line-height: 1.8; }
.eq-flip-hint { text-align: center; font-size: 12.5px; opacity: 0.7; }
.eq-flip:hover .eq-flip-face { box-shadow: 0 1px 2px rgba(22,32,43,.08), 0 20px 36px -14px rgba(22,32,43,.45); }
@media (prefers-reduced-motion: reduce) { .eq-flip-inner { transition: none; } }

.eq-quiz-card { background: #FFFFFF; color: #16202B; border: 1px solid #D8D2C4; border-top: 4px solid #0F4C81; min-height: 240px; margin: 6px 0 4px; }
.eq-quiz-card .eq-flip-term { font-size: clamp(20px, 3.4vw, 27px); }

.eq-card { background: #FFFFFF; border: 1px solid #D8D2C4; border-top: 3px solid #0F4C81; border-radius: 4px; padding: 22px 26px 18px; min-height: 230px; display: flex; flex-direction: column; gap: 14px; }
.eq-card-meta { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px 12px; font-size: 12.5px; letter-spacing: 0.04em; color: #5B6470; }
.eq-card-front { font-family: 'Noto Serif KR', serif; font-size: clamp(20px, 3.2vw, 26px); font-weight: 700; line-height: 1.45; color: #16202B; }
.eq-card-back { font-size: 16px; line-height: 1.75; color: #16202B; border-top: 1px dashed #D8D2C4; padding-top: 14px; }
.eq-card-hint { font-size: 14px; color: #5B6470; }
.eq-card-source { margin-top: auto; font-size: 12.5px; color: #5B6470; }

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
