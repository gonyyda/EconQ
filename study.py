import streamlit as st
import html
import random

from storage import (
    export_data,
    make_id,
    merge_data,
    remove_scrap,
    save,
    set_known
)


# -----------------------------
# 스크랩에서 학습 자료 모으기
# -----------------------------

def collect_flashcards(scraps):

    cards = []
    seen = set()

    for scrap in scraps:

        data = scrap["data"]

        raw = [
            (item.get("category"), item.get("front"), item.get("back"))
            for item in data.get("flashcards", [])
            if isinstance(item, dict)
        ]

        # 예전 분석에는 flashcards가 없으므로 경제 개념 설명을 카드로 쓴다
        if not raw:

            raw = [
                ("경제개념", item.get("term"), item.get("explanation"))
                for item in data.get("background", [])
                if isinstance(item, dict)
            ]

        for category, front, back in raw:

            front = str(front or "").strip()
            back = str(back or "").strip()

            if not front or not back or front in seen:
                continue

            seen.add(front)

            cards.append(
                {
                    "id": make_id(front),
                    "category": str(category or "경제개념"),
                    "front": front,
                    "back": back,
                    "source": data.get("title", "")
                }
            )

    return cards


def collect_quiz(scraps):

    questions = []
    seen = set()

    for scrap in scraps:

        data = scrap["data"]

        for item in data.get("ox_quiz", []):

            if not isinstance(item, dict):
                continue

            statement = str(item.get("statement") or "").strip()
            answer = str(item.get("answer") or "").strip().upper()

            if not statement or answer not in ("O", "X") or statement in seen:
                continue

            seen.add(statement)

            questions.append(
                {
                    "id": make_id(statement),
                    "statement": statement,
                    "answer": answer,
                    "explanation": str(item.get("explanation") or ""),
                    "source": data.get("title", "")
                }
            )

    return questions


# -----------------------------
# 스크랩 탭
# -----------------------------

def open_scrap(data):

    st.session_state["analysis"] = data

    st.toast("탭 아래에 분석 결과를 열었습니다.")


def import_backup():

    uploaded = st.session_state.get("scrap_upload")

    if uploaded is None:
        return

    try:
        text = uploaded.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        text = ""

    added = merge_data(text)

    save()

    st.toast(f"스크랩 {added}건을 가져왔습니다.")


def show_scrap_tab():

    scraps = st.session_state["scraps"]

    st.subheader("스크랩한 분석")

    st.caption(
        "스크랩은 지금 쓰는 브라우저에만 저장됩니다. "
        "다른 기기에서도 보려면 아래에서 백업 파일을 내려받아 가져오세요."
    )

    if not scraps:

        st.info(
            "아직 스크랩한 분석이 없습니다. "
            "기사를 분석한 뒤 결과 위의 '스크랩하기'를 눌러 보세요."
        )

    for scrap in scraps:

        data = scrap["data"]

        cards = len(collect_flashcards([scrap]))
        quiz = len(collect_quiz([scrap]))

        with st.container(border=True, key=f"card_scrap_{scrap['id']}"):

            info, actions = st.columns([3, 1])

            with info:

                st.markdown(
                    f"**{data.get('title', '제목 없음')}**"
                )

                st.caption(
                    f"{data.get('category', '기타')} · {scrap['saved_at']} 저장 · "
                    f"플래시카드 {cards}장 · OX 퀴즈 {quiz}문제"
                )

            with actions:

                st.button(
                    "열어보기",
                    key=f"open_{scrap['id']}",
                    on_click=open_scrap,
                    args=(data,),
                    width="stretch"
                )

                st.button(
                    "삭제",
                    key=f"remove_{scrap['id']}",
                    on_click=remove_scrap,
                    args=(scrap["id"],),
                    width="stretch"
                )

    with st.expander("백업 · 가져오기"):

        st.download_button(
            "백업 파일 내려받기",
            export_data(),
            file_name="econq_scraps.json",
            mime="application/json",
            disabled=not scraps
        )

        st.file_uploader(
            "백업 파일 가져오기",
            type="json",
            key="scrap_upload"
        )

        st.button(
            "가져오기",
            on_click=import_backup,
            disabled=st.session_state.get("scrap_upload") is None
        )


# -----------------------------
# 플래시카드
# -----------------------------

def reset_flashcards():

    st.session_state["fc_idx"] = 0
    st.session_state["fc_flipped"] = False


def shuffle_flashcards():

    st.session_state["fc_seed"] = random.randint(1, 10 ** 6)

    reset_flashcards()


def move_flashcard(step):

    st.session_state["fc_idx"] = st.session_state.get("fc_idx", 0) + step
    st.session_state["fc_flipped"] = False


def flip_flashcard():

    st.session_state["fc_flipped"] = not st.session_state.get("fc_flipped", False)


def mark_flashcard(card_id, known):

    set_known(card_id, known)

    st.session_state["fc_flipped"] = False

    # '못 외운 카드만' 볼 때 외운 카드는 목록에서 빠지므로 그대로 두면 다음 카드가 된다
    if not (known and st.session_state.get("fc_unknown")):
        st.session_state["fc_idx"] = st.session_state.get("fc_idx", 0) + 1


def show_flashcards(cards):

    if not cards:

        st.info("선택한 스크랩에 플래시카드가 없습니다.")
        return

    known = set(st.session_state["known_cards"])

    learned = sum(
        card["id"] in known
        for card in cards
    )

    st.progress(
        learned / len(cards),
        text=f"외운 카드 {learned} / {len(cards)}"
    )

    left, right = st.columns([2, 1])

    with left:

        category = st.segmented_control(
            "분류",
            ["전체"] + sorted({card["category"] for card in cards}),
            default="전체",
            key="fc_category",
            on_change=reset_flashcards,
            label_visibility="collapsed"
        )

    with right:

        only_unknown = st.toggle(
            "아직 못 외운 카드만",
            key="fc_unknown",
            on_change=reset_flashcards
        )

    deck = [
        card
        for card in cards
        if category in (None, "전체", card["category"])
        and not (only_unknown and card["id"] in known)
    ]

    if not deck:

        st.success("이 조건의 카드는 모두 외웠습니다.")
        return

    if st.session_state.get("fc_seed"):

        random.Random(
            st.session_state["fc_seed"]
        ).shuffle(deck)

    index = st.session_state.get("fc_idx", 0) % len(deck)

    card = deck[index]

    flipped = st.session_state.get("fc_flipped", False)

    status = "외운 카드" if card["id"] in known else "학습 중"

    if flipped:
        answer = f'<div class="eq-card-back">{html.escape(card["back"])}</div>'
    else:
        answer = '<div class="eq-card-hint">답을 떠올린 뒤 카드를 뒤집어 보세요.</div>'

    st.html(
        f"""
<div class="eq-card">
  <div class="eq-card-meta"><span>{html.escape(card["category"])} · {index + 1} / {len(deck)}</span><span>{status}</span></div>
  <div class="eq-card-front">{html.escape(card["front"])}</div>
  {answer}
  <div class="eq-card-source">출처: {html.escape(card["source"])}</div>
</div>
"""
    )

    prev_col, flip_col, next_col = st.columns(3)

    prev_col.button(
        "← 이전",
        on_click=move_flashcard,
        args=(-1,),
        width="stretch"
    )

    flip_col.button(
        "앞면 보기" if flipped else "뒤집기",
        type="primary",
        on_click=flip_flashcard,
        width="stretch"
    )

    next_col.button(
        "다음 →",
        on_click=move_flashcard,
        args=(1,),
        width="stretch"
    )

    if flipped:

        known_col, again_col = st.columns(2)

        known_col.button(
            "✅ 외웠어요",
            on_click=mark_flashcard,
            args=(card["id"], True),
            width="stretch"
        )

        again_col.button(
            "🔁 다시 볼게요",
            on_click=mark_flashcard,
            args=(card["id"], False),
            width="stretch"
        )

    st.button(
        "카드 섞기",
        on_click=shuffle_flashcards,
        type="tertiary"
    )


# -----------------------------
# OX 퀴즈
# -----------------------------

def reset_quiz(ids):

    order = list(ids)

    random.shuffle(order)

    st.session_state["ox_ids"] = sorted(ids)
    st.session_state["ox_order"] = order
    st.session_state["ox_answers"] = {}
    st.session_state["ox_idx"] = 0


def answer_quiz(question_id, choice):

    st.session_state["ox_answers"][question_id] = choice


def next_quiz():

    st.session_state["ox_idx"] += 1


def show_quiz(questions):

    if not questions:

        st.info(
            "선택한 스크랩에 OX 퀴즈가 없습니다. "
            "퀴즈는 이 기능이 추가된 뒤에 분석한 기사부터 만들어집니다."
        )
        return

    by_id = {
        question["id"]: question
        for question in questions
    }

    # 학습 범위가 바뀌면 퀴즈를 새로 시작한다
    if st.session_state.get("ox_ids") != sorted(by_id):
        reset_quiz(list(by_id))

    order = st.session_state["ox_order"]
    answers = st.session_state["ox_answers"]
    index = st.session_state["ox_idx"]

    if index >= len(order):

        wrong = [
            by_id[question_id]
            for question_id in order
            if answers.get(question_id) != by_id[question_id]["answer"]
        ]

        st.metric(
            "점수",
            f"{len(order) - len(wrong)} / {len(order)}",
            border=True
        )

        if wrong:

            st.markdown("**틀린 문제 다시 보기**")

            for question in wrong:

                with st.container(border=True, key=f"card_wrong_{question['id']}"):

                    st.markdown(
                        f"**{question['statement']}**"
                    )

                    st.write(
                        f"정답: {question['answer']}"
                    )

                    st.caption(
                        question["explanation"]
                    )

        else:

            st.success("모든 문제를 맞혔습니다.")

        st.button(
            "다시 풀기",
            type="primary",
            on_click=reset_quiz,
            args=(list(by_id),)
        )

        return

    question = by_id[order[index]]

    choice = answers.get(question["id"])

    st.progress(
        index / len(order),
        text=f"문제 {index + 1} / {len(order)}"
    )

    st.html(
        f"""
<div class="eq-card">
  <div class="eq-card-meta"><span>OX 퀴즈</span><span>맞으면 O, 틀리면 X</span></div>
  <div class="eq-card-front">{html.escape(question["statement"])}</div>
  <div class="eq-card-source">출처: {html.escape(question["source"])}</div>
</div>
"""
    )

    if choice is None:

        o_col, x_col = st.columns(2)

        o_col.button(
            "O",
            key="ox_o",
            on_click=answer_quiz,
            args=(question["id"], "O"),
            width="stretch"
        )

        x_col.button(
            "X",
            key="ox_x",
            on_click=answer_quiz,
            args=(question["id"], "X"),
            width="stretch"
        )

        return

    if choice == question["answer"]:
        st.success(f"정답입니다. 답은 {question['answer']}입니다.")
    else:
        st.error(f"틀렸습니다. 답은 {question['answer']}입니다.")

    st.write(
        question["explanation"]
    )

    st.button(
        "결과 보기" if index == len(order) - 1 else "다음 문제 →",
        type="primary",
        on_click=next_quiz
    )


# -----------------------------
# 학습 탭
# -----------------------------

def show_study_tab():

    scraps = st.session_state["scraps"]

    st.subheader("스크랩으로 공부하기")

    if not scraps:

        st.info(
            "스크랩한 분석이 있어야 학습할 수 있습니다. "
            "기사를 분석하고 스크랩하면 플래시카드와 OX 퀴즈가 여기에 모입니다."
        )
        return

    titles = {
        scrap["id"]: scrap["data"].get("title", "제목 없음")
        for scrap in scraps
    }

    selected = st.multiselect(
        "학습 범위",
        list(titles),
        format_func=lambda x: titles.get(x, x),
        placeholder="전체 스크랩 (특정 기사만 고르려면 선택하세요)",
        key="study_scope",
        on_change=reset_flashcards
    )

    scope = [
        scrap
        for scrap in scraps
        if not selected or scrap["id"] in selected
    ]

    cards = collect_flashcards(scope)
    questions = collect_quiz(scope)

    mode = st.segmented_control(
        "학습 방식",
        ["플래시카드", "OX 퀴즈"],
        default="플래시카드",
        key="study_mode",
        label_visibility="collapsed"
    )

    st.caption(
        f"플래시카드 {len(cards)}장 · OX 퀴즈 {len(questions)}문제"
    )

    if mode == "OX 퀴즈":
        show_quiz(questions)
    else:
        show_flashcards(cards)
