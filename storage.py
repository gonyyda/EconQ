import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import uuid


# -----------------------------
# 브라우저 저장소 (localStorage)
# -----------------------------

STORAGE_NAME = "econq_v1"

_storage_component = components.declare_component(
    "econq_storage",
    path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "storage_component"
    )
)


def make_id(text):

    return hashlib.md5(
        str(text).encode("utf-8")
    ).hexdigest()[:12]


def scrap_id(data):

    summary = data.get("summary") or [""]

    return make_id(
        f"{data.get('title', '')}|{summary[0]}"
    )


def export_data():

    return json.dumps(
        {
            "scraps": st.session_state["scraps"],
            "known_cards": st.session_state["known_cards"]
        },
        ensure_ascii=False
    )


def save():

    # 브라우저에 저장된 값을 읽기 전에는 덮어쓰지 않는다
    if not st.session_state.get("store_loaded"):
        return

    st.session_state["store_payload"] = export_data()
    st.session_state["store_nonce"] = uuid.uuid4().hex


def merge_data(text):

    try:
        stored = json.loads(text) if text else {}
    except (TypeError, ValueError):
        return 0

    if not isinstance(stored, dict):
        return 0

    scraps = st.session_state["scraps"]

    ids = {
        scrap["id"]
        for scrap in scraps
    }

    added = 0

    for scrap in stored.get("scraps", []):

        if (
            isinstance(scrap, dict)
            and isinstance(scrap.get("data"), dict)
            and scrap.get("id")
            and scrap["id"] not in ids
        ):

            ids.add(scrap["id"])

            scraps.append(
                {
                    "id": str(scrap["id"]),
                    "saved_at": str(scrap.get("saved_at", "")),
                    "data": scrap["data"]
                }
            )

            added += 1

    scraps.sort(
        key=lambda x: x["saved_at"],
        reverse=True
    )

    known = set(st.session_state["known_cards"])

    known.update(
        str(item)
        for item in stored.get("known_cards", [])
    )

    st.session_state["known_cards"] = sorted(known)

    return added


def init_storage():

    state = st.session_state

    state.setdefault("scraps", [])
    state.setdefault("known_cards", [])
    state.setdefault("store_payload", None)
    state.setdefault("store_nonce", "")
    state.setdefault("store_loaded", False)
    state.setdefault("store_token", uuid.uuid4().hex)

    with st.container(key="econq_store_slot"):

        result = _storage_component(
            name=STORAGE_NAME,
            payload=state["store_payload"],
            nonce=state["store_nonce"],
            token=state["store_token"],
            key="econq_store",
            default=None
        )

    # 이 세션이 요청한 값일 때만 받아들인다
    if (
        result is not None
        and result.get("token") == state["store_token"]
        and not state["store_loaded"]
    ):

        # 불러오기 전에 이미 스크랩한 것이 있으면 합쳐서 다시 저장한다
        had_local = bool(
            state["scraps"] or state["known_cards"]
        )

        merge_data(result.get("data"))

        state["store_loaded"] = True

        if had_local:
            save()
            st.rerun()


# -----------------------------
# 스크랩
# -----------------------------

def is_scrapped(data):

    target = scrap_id(data)

    return any(
        scrap["id"] == target
        for scrap in st.session_state["scraps"]
    )


def add_scrap(data):

    if is_scrapped(data):
        return

    now = datetime.now(
        timezone(timedelta(hours=9))
    )

    st.session_state["scraps"].insert(
        0,
        {
            "id": scrap_id(data),
            "saved_at": f"{now:%Y-%m-%d %H:%M}",
            "data": data
        }
    )

    save()


def remove_scrap(target):

    st.session_state["scraps"] = [
        scrap
        for scrap in st.session_state["scraps"]
        if scrap["id"] != target
    ]

    save()


def set_known(card_id, known):

    cards = set(st.session_state["known_cards"])

    if known:
        cards.add(card_id)
    else:
        cards.discard(card_id)

    st.session_state["known_cards"] = sorted(cards)

    save()
