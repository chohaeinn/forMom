import uuid
from io import BytesIO

import streamlit as st

st.set_page_config(
    page_title="장보기 알림 메모",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- 스타일: 스마트폰에서 스크롤 없이 보이도록 여백 최소화 ----------
st.markdown(
    """
    <style>
    header[data-testid="stHeader"], footer {display:none;}
    .block-container {padding: 0.6rem 0.8rem 0.4rem 0.8rem; max-width: 520px;}
    div[data-testid="stVerticalBlock"] {gap: 0.35rem;}
    div[data-testid="stMetric"] {background:#f4f8f5; border-radius:10px; padding:4px 8px;}
    div[data-testid="stMetricLabel"] p {font-size:0.72rem;}
    div[data-testid="stMetricValue"] {font-size:1.15rem;}
    div[data-testid="stForm"] {padding: 0.5rem 0.6rem; border-radius:12px;}
    .stButton button {padding: 0.1rem 0.4rem; min-height: 2rem;}
    label {font-size:0.75rem !important; margin-bottom:0 !important;}
    p {margin-bottom: 0.1rem;}
    h1 {font-size:1.25rem !important; padding:0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORIES = {
    "🥬 야채": "야채",
    "🍎 과일": "과일",
    "🥩 육류": "육류",
    "🐟 수산물": "수산물",
    "🥛 유제품·계란": "유제품·계란",
    "🍞 빵·간식": "빵·간식",
    "🧴 생활용품": "생활용품",
    "🥫 기타": "기타",
}
IMP_LABEL = {1: "1 가격 봐서", 2: "2 보통", 3: "3 꼭 사기"}
IMP_BADGE = {1: "🟢", 2: "🟡", 3: "🔴"}

# ---------- 상태 ----------
if "memo_items" not in st.session_state:
    st.session_state.memo_items = []  # dict: id, cat, name, imp, limit, status, price, qty
if "budget" not in st.session_state:
    st.session_state.budget = 0


def todo_items():
    items = [i for i in st.session_state.memo_items if i["status"] == "todo"]
    return sorted(items, key=lambda x: -x["imp"])


def cart_items():
    return [i for i in st.session_state.memo_items if i["status"] == "cart"]


def find(item_id):
    for i in st.session_state.memo_items:
        if i["id"] == item_id:
            return i
    return None


def won(n):
    return f"{int(n):,}원"


# ---------- 카트에 담기 팝업 (가격·수량 입력) ----------
@st.dialog("🛒 카트에 담기")
def buy_dialog(item_id):
    it = find(item_id)
    if it is None:
        st.rerun()
    st.markdown(f"**{it['name']}**  ·  {it['cat']}  ·  {IMP_BADGE[it['imp']]} 중요도 {it['imp']}")

    c1, c2 = st.columns(2)
    price = c1.number_input(
        "1개 가격(원)", min_value=0, step=100, value=int(it["limit"] or 0)
    )
    qty = c2.number_input("수량", min_value=1, step=1, value=1)

    limit = int(it["limit"] or 0)
    too_expensive = False
    if it["imp"] == 3:
        st.success("🔴 중요도 3 — 가격 상관없이 사도 되는 물건이에요.")
    elif limit > 0 and price > limit:
        too_expensive = True
        over = int(price - limit)
        if it["imp"] == 1:
            st.error(f"기준가보다 {won(over)} 비싸요. 이번엔 패스 추천!")
        else:
            st.warning(f"기준가보다 {won(over)} 비싸요. 꼭 필요할 때만 사요.")
    elif limit > 0 and price > 0:
        st.success("기준가 이내예요. 담아도 좋아요 👍")

    st.markdown(f"**합계: {won(price * qty)}**")

    b1, b2 = st.columns(2)
    if b1.button("✅ 담기", type="primary", use_container_width=True):
        it["status"] = "cart"
        it["price"] = int(price)
        it["qty"] = int(qty)
        st.rerun()
    if it["imp"] < 3:
        label = "🚫 패스" if too_expensive else "패스(안 사요)"
        if b2.button(label, use_container_width=True):
            st.session_state.memo_items = [
                i for i in st.session_state.memo_items if i["id"] != item_id
            ]
            st.rerun()


# ---------- QR 팝업 ----------
def qr_png(url):
    import qrcode

    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------- 상단: 제목 + 카트 / QR ----------
carts = cart_items()
total = sum(i["price"] * i["qty"] for i in carts)
todos = todo_items()

h1, h2, h3 = st.columns([3, 1.3, 1])
h1.markdown("### 🛒 장보기 메모")
with h2.popover("🧾 카트", use_container_width=True):
    st.markdown(f"**카트 총액 {won(total)}**")
    if not carts:
        st.caption("아직 담은 물건이 없어요.")
    for it in carts:
        a, b = st.columns([5, 1])
        a.markdown(
            f"{it['name']} · {won(it['price'])} × {it['qty']} = **{won(it['price'] * it['qty'])}**"
        )
        if b.button("↩", key=f"undo_{it['id']}", help="카트에서 빼고 메모로 되돌리기"):
            it["status"] = "todo"
            st.rerun()
    st.session_state.budget = st.number_input(
        "예산(원, 0이면 사용 안 함)", min_value=0, step=1000, value=st.session_state.budget
    )
with h3.popover("📱", use_container_width=True):
    st.caption("배포된 앱 주소를 넣으면 QR이 만들어져요.")
    url = st.text_input("앱 주소", placeholder="https://내앱.streamlit.app")
    if url:
        try:
            st.image(qr_png(url), width=200)
        except Exception:
            st.error("QR 생성 실패: requirements.txt에 qrcode[pil]이 있는지 확인해 주세요.")

# ---------- 총액 요약 ----------
m1, m2, m3 = st.columns(3)
m1.metric("카트 총액", won(total))
m2.metric("담음 / 남음", f"{len(carts)} / {len(todos)}")
budget = st.session_state.budget
if budget > 0:
    m3.metric("남은 예산", won(budget - total))
else:
    m3.metric("남은 메모", f"{len(todos)}개")

# ---------- 메모 추가 ----------
with st.form("add", clear_on_submit=True):
    c1, c2 = st.columns([2, 3])
    cat_label = c1.selectbox("카테고리", list(CATEGORIES.keys()))
    name = c2.text_input("상품명", placeholder="예: 대파 1단, 청포도")
    d1, d2 = st.columns([3, 2])
    imp = d1.radio(
        "중요도",
        [1, 2, 3],
        index=1,
        horizontal=True,
        format_func=lambda x: IMP_LABEL[x],
    )
    limit = d2.number_input("기준가(선택)", min_value=0, step=100, value=0)
    if st.form_submit_button("➕ 메모 추가", use_container_width=True):
        if name.strip():
            st.session_state.memo_items.append(
                {
                    "id": uuid.uuid4().hex,
                    "cat": CATEGORIES[cat_label],
                    "name": name.strip(),
                    "imp": imp,
                    "limit": int(limit),
                    "status": "todo",
                    "price": 0,
                    "qty": 0,
                }
            )
            st.rerun()
        else:
            st.warning("상품명을 적어 주세요.")

# ---------- 메모 목록 (고정 높이: 화면 전체는 스크롤 안 됨) ----------
with st.container(height=210, border=True):
    if not todos:
        st.caption("남은 메모가 없어요. 🎉" if carts else "위에서 살 물건을 추가해 보세요.")
    for it in todos:
        a, b, c = st.columns([6, 1, 1])
        extra = f" <span style='color:#888;font-size:0.75rem'>≤{won(it['limit'])}</span>" if it["limit"] else ""
        a.markdown(
            f"{IMP_BADGE[it['imp']]} **{it['name']}** "
            f"<span style='color:#888;font-size:0.75rem'>{it['cat']}</span>{extra}",
            unsafe_allow_html=True,
        )
        if b.button("🛒", key=f"buy_{it['id']}", help="카트에 담기"):
            buy_dialog(it["id"])
        if c.button("🗑", key=f"del_{it['id']}", help="메모 삭제"):
            st.session_state.memo_items = [
                i for i in st.session_state.memo_items if i["id"] != it["id"]
            ]
            st.rerun()
