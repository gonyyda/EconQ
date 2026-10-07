import streamlit as st
import altair as alt
import pandas as pd
import requests


# -----------------------------
# 관련 지표 목록 (Yahoo Finance)
# -----------------------------

INDICATORS = {
    "코스피": {"ticker": "^KS11", "unit": "", "decimals": 2},
    "코스닥": {"ticker": "^KQ11", "unit": "", "decimals": 2},
    "원/달러 환율": {"ticker": "KRW=X", "unit": "원", "decimals": 1},
    "미국 10년물 국채금리": {"ticker": "^TNX", "unit": "%", "decimals": 2},
    "S&P 500": {"ticker": "^GSPC", "unit": "", "decimals": 2},
    "나스닥": {"ticker": "^IXIC", "unit": "", "decimals": 2},
    "달러인덱스": {"ticker": "DX-Y.NYB", "unit": "", "decimals": 2},
    "WTI 유가": {"ticker": "CL=F", "unit": "달러", "decimals": 2},
    "금 가격": {"ticker": "GC=F", "unit": "달러", "decimals": 1}
}

# AI가 관련 지표를 고르지 못했을 때 카테고리별로 보여줄 기본 지표
DEFAULT_INDICATORS = {
    "금리": ["미국 10년물 국채금리", "원/달러 환율", "코스피"],
    "환율": ["원/달러 환율", "달러인덱스", "코스피"],
    "물가": ["WTI 유가", "미국 10년물 국채금리", "원/달러 환율"],
    "주식": ["코스피", "코스닥", "S&P 500"],
    "채권": ["미국 10년물 국채금리", "달러인덱스", "코스피"],
    "부동산": ["미국 10년물 국채금리", "코스피", "원/달러 환율"],
    "금융정책": ["미국 10년물 국채금리", "원/달러 환율", "코스피"],
    "재정정책": ["미국 10년물 국채금리", "원/달러 환율", "코스피"],
    "기업": ["코스피", "코스닥", "원/달러 환율"],
    "산업": ["코스피", "나스닥", "원/달러 환율"],
    "원자재": ["WTI 유가", "금 가격", "달러인덱스"],
    "국제경제": ["S&P 500", "달러인덱스", "원/달러 환율"],
    "기타": ["코스피", "원/달러 환율", "미국 10년물 국채금리"]
}

PERIODS = {
    "1개월": 30,
    "3개월": 91,
    "6개월": 182,
    "1년": 365
}

STAGE_COLORS = {
    "원인": "#D6E4F2",
    "전달경로": "#ECE8DF",
    "결과": "#F4DCCB"
}

DIRECTION_STYLES = {
    "상승 압력": ("▲", "blue"),
    "하락 압력": ("▼", "violet"),
    "긍정적 영향 가능": ("＋", "green"),
    "부정적 영향 가능": ("－", "red"),
    "변동성 확대 가능": ("↕", "orange"),
    "영향 불확실": ("？", "gray")
}


# -----------------------------
# 지표 데이터 불러오기
# -----------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def get_indicator_history(ticker):

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + requests.utils.quote(ticker)
    )

    response = requests.get(
        url,
        params={"range": "1y", "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10
    )

    response.raise_for_status()

    result = response.json()["chart"]["result"][0]

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(result["timestamp"], unit="s"),
            "close": result["indicators"]["quote"][0]["close"]
        }
    )

    df["date"] = df["date"].dt.normalize()

    return df.dropna().drop_duplicates("date", keep="last")


def is_dark_theme():

    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def wrap_label(text, width=13):

    lines = []
    line = ""

    for word in str(text).split():

        if line and len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()

    if line:
        lines.append(line)

    return "\\n".join(
        item.replace('"', "'")
        for item in lines
    )


# -----------------------------
# 핵심 수치
# -----------------------------

def show_key_figures(data):

    figures = [
        item
        for item in data.get("key_figures", [])
        if item.get("label") and item.get("value")
    ][:4]

    if not figures:
        return

    st.markdown("**기사 속 핵심 수치**")

    cols = st.columns(len(figures))

    for col, item in zip(cols, figures):

        with col:

            st.metric(
                item["label"],
                item["value"],
                item.get("change") or None,
                delta_color="off",
                border=True
            )


# -----------------------------
# 인과관계 지도
# -----------------------------

def build_causal_dot(data):

    graph = data.get("causal_graph") or {}

    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []

    # causal_graph가 없으면 causal_chain을 한 줄로 이어서 그린다
    if not nodes or not edges:

        chain = data.get("causal_chain", [])

        if len(chain) < 2:
            return None

        nodes = []

        for i, step in enumerate(chain):

            if i == 0:
                stage = "원인"
            elif i == len(chain) - 1:
                stage = "결과"
            else:
                stage = "전달경로"

            nodes.append(
                {"id": f"n{i}", "label": step, "stage": stage}
            )

        edges = [
            {"from": f"n{i}", "to": f"n{i + 1}"}
            for i in range(len(chain) - 1)
        ]

    ids = {
        str(node.get("id"))
        for node in nodes
    }

    lines = [
        "digraph {",
        'bgcolor="transparent"; rankdir=TB; nodesep=0.3; ranksep=0.4;',
        'node [shape=box, style="rounded,filled", color="#B9B2A2", '
        'fontcolor="#0b0b0b", fontsize=12, margin="0.18,0.1"];',
        'edge [color="#898781", arrowsize=0.7];'
    ]

    for node in nodes:

        stage = node.get("stage")

        if stage not in STAGE_COLORS:
            stage = "전달경로"

        lines.append(
            f'"{node.get("id")}" '
            f'[label="[{stage}]\\n{wrap_label(node.get("label", ""))}", '
            f'fillcolor="{STAGE_COLORS[stage]}"];'
        )

    for edge in edges:

        if str(edge.get("from")) in ids and str(edge.get("to")) in ids:

            lines.append(
                f'"{edge["from"]}" -> "{edge["to"]}";'
            )

    lines.append("}")

    return "\n".join(lines)


def show_causal_map(data):

    st.markdown("**인과관계 지도**")

    dot = build_causal_dot(data)

    if not dot:
        st.caption("인과관계 정보가 없습니다.")
        return

    st.graphviz_chart(
        dot,
        width="stretch"
    )

    st.caption(
        "원인에서 출발해 전달경로를 거쳐 결과로 이어지는 흐름입니다. "
        "AI의 해석이며 실제 결과는 달라질 수 있습니다."
    )


# -----------------------------
# 시장 영향 보드
# -----------------------------

def show_impact_board(data):

    st.markdown("**시장 영향 한눈에 보기**")

    impacts = data.get("market_impacts", [])

    if not impacts:
        st.caption("시장 영향 정보가 없습니다.")
        return

    order = list(DIRECTION_STYLES)

    impacts = sorted(
        impacts,
        key=lambda x: (
            order.index(x.get("direction"))
            if x.get("direction") in order
            else len(order)
        )
    )

    for i, impact in enumerate(impacts):

        direction = impact.get("direction", "")

        icon, color = DIRECTION_STYLES.get(
            direction,
            ("•", "gray")
        )

        with st.container(border=True, key=f"card_board_{i}"):

            st.markdown(
                f"**{impact.get('market', '')}** "
                f":{color}-badge[{icon} {direction}]"
            )

            st.caption(
                impact.get("reason", "")
            )


# -----------------------------
# 관련 지표 추이
# -----------------------------

def format_value(value, info):

    return f"{value:,.{info['decimals']}f}{info['unit']}"


def show_indicator(name, days):

    info = INDICATORS[name]

    try:
        df = get_indicator_history(info["ticker"])
    except Exception:
        df = None

    with st.container(border=True, key=f"card_indicator_{info['ticker']}"):

        if df is None or len(df) < 2:

            st.markdown(f"**{name}**")
            st.caption("지표 데이터를 불러오지 못했습니다.")
            return

        start = df["date"].max() - pd.Timedelta(days=days)

        df = df[df["date"] >= start]

        first = df["close"].iloc[0]
        last = df["close"].iloc[-1]

        # 금리는 변화율이 아니라 %p 차이로 보여준다
        if info["unit"] == "%":
            change = f"{last - first:+.2f}%p"
        else:
            change = f"{(last / first - 1) * 100:+.1f}%"

        st.metric(
            name,
            format_value(last, info),
            change,
            delta_color="off"
        )

        color = "#3987e5" if is_dark_theme() else "#0F4C81"

        hover = alt.selection_point(
            nearest=True,
            on="pointerover",
            fields=["date"],
            empty=False
        )

        base = alt.Chart(df).encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(
                    format="%m/%d",
                    tickCount=3,
                    grid=False,
                    labelFlush=True
                )
            ),
            y=alt.Y(
                "close:Q",
                title=None,
                scale=alt.Scale(zero=False),
                axis=alt.Axis(tickCount=4)
            )
        )

        tooltip = [
            alt.Tooltip("date:T", title="날짜", format="%Y-%m-%d"),
            alt.Tooltip(
                "close:Q",
                title=name,
                format=f",.{info['decimals']}f"
            )
        ]

        line = base.mark_line(
            strokeWidth=2,
            color=color
        )

        rule = alt.Chart(df).mark_rule(
            color="#898781"
        ).encode(
            x="date:T",
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=tooltip
        ).add_params(hover)

        point = base.mark_point(
            size=70,
            filled=True,
            color=color
        ).encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0))
        )

        st.altair_chart(
            (line + rule + point).properties(height=150),
            width="stretch"
        )

        st.caption(
            f"{df['date'].iloc[-1]:%Y-%m-%d} 기준 · "
            f"변화는 선택한 기간의 첫날 대비"
        )


def show_indicators(data):

    names = [
        name
        for name in data.get("related_indicators", [])
        if name in INDICATORS
    ]

    if not names:

        names = DEFAULT_INDICATORS.get(
            data.get("category"),
            DEFAULT_INDICATORS["기타"]
        )

    names = list(dict.fromkeys(names))[:3]

    head, picker = st.columns(2)

    with head:
        st.markdown("**관련 지표 추이**")

    with picker:

        period = st.segmented_control(
            "기간",
            list(PERIODS),
            default="3개월",
            key="indicator_period",
            label_visibility="collapsed"
        )

    days = PERIODS.get(period, PERIODS["3개월"])

    cols = st.columns(len(names))

    for col, name in zip(cols, names):

        with col:
            show_indicator(name, days)

    st.caption(
        "출처: Yahoo Finance 일별 종가. 실제 시장 데이터이며 "
        "기사 내용과 별개로 참고용으로 제공됩니다."
    )


# -----------------------------
# 대시보드
# -----------------------------

def show_dashboard(data):

    show_key_figures(data)

    left, right = st.columns(2)

    with left:
        show_causal_map(data)

    with right:
        show_impact_board(data)

    show_indicators(data)
