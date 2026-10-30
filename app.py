import json
import uuid
from io import BytesIO

import streamlit as st

st.set_page_config(
    page_title="마트 장보기 도우미",
    page_icon="🛒",
    layout="wide",  # 넓은 화면을 활용해 선반과 사이드바 배치
    initial_sidebar_state="expanded",
)

# =====================================================================
# 마트 테마 스타일 설정 (신선한 마트 감성 색상 및 선반 느낌)
# =====================================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F6F4;
    }
    header[data-testid="stHeader"] {background: rgba(0,0,0,0);}
    
    /* 선반(Shelf) 스타일 박스 */
    .shelf-container {
        background: #FFFFFF;
        border: 3px solid #81C784;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .shelf-title {
        font-size: 1.2rem;
        font-weight: 900;
        color: #1B5E20;
        margin-bottom: 10px;
        border-bottom: 2px solid #E8F5E9;
        padding-bottom: 5px;
    }

    /* 상품 버튼 스타일 최적화 */
    .stButton button {
        border-radius: 10px;
        border: 1.5px solid #C8E6C9;
        font-weight: 700;
        color: #263238;
        background-color: #FFFFFF;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        border-color: #4CAF50;
        background-color: #F1F8E9;
        transform: translateY(-2px);
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #E8F5E9;
        border-right: 2px solid #C8E6C9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 상품 목록 데이터 (마트 진열 카테고리별)
# =====================================================================
RAW = {
    ("🥬", "신선야채"): """
        🥬 상추 2500
        🥦 브로콜리 3000
        🥕 당근 3000
        🧅 양파 3500
        🧄 마늘 6000
        🥔 감자 4500
        🥒 오이 2000
        🍅 방울토마토 6500
    """,
    ("🍎", "제철과일"): """
        🍎 사과 8000
        🍐 배 9000
        🍊 귤 6000
        🍌 바나나 3500
        🍇 포도 9000
        🍓 딸기 9000
        🍉 수박 20000
        🍑 복숭아 10000
    """,
    ("🥩", "정육·계란"): """
        🥩 소고기 25000
        🐖 삼겹살 17000
        🍖 목살 15000
        🍗 닭가슴살 6000
        🥚 계란30구 7500
        🥓 베이컨 5500
    """,
    ("🐟", "수산·해산물"): """
        🐟 고등어 5500
        🦑 오징어 6500
        🦐 새우 12000
        🐟 연어 15000
        🦀 꽃게 18000
        🟫 김 4000
    """,
    ("🥛", "유제품·간식"): """
        🥛 우유 2900
        🧀 치즈 5500
        🧈 버터 6500
        🥛 요거트 4500
        🍞 식빵 3500
        🍪 쿠키 3500
    """,
    ("🥤", "음료·가공식품"): """
        🥤 콜라 2500
        🧃 오렌지주스 4500
        ☕ 커피믹스 8000
        💧 생수 6000
        🍜 라면 4500
        🍚 즉석밥 3000
    """,
}


def _parse(raw):
    out = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        head, price = line.rsplit(" ", 1)
        emo, name = head.split(" ", 1)
        out.append((emo, name.strip(), int(price)))
    return out


CATALOG = {name: {"icon": icon, "items": _parse(raw)} for (icon, name), raw in RAW.items()}

# 세션 상태 초기화
S = st.session_state
S.setdefault("memo_items", [])  # 메모 및 장바구니 통합 관리
S.setdefault("budget", 30000)   # 기본 예산
S.setdefault("prices", {})      # 가격 수정 내역
S.setdefault("history", {})     # 구매 기록


def won(n):
    return f"{int(n):,}원"


def price_of(cat, name, base):
    return S.prices.get(f"{cat}|{name}", base)


def cart_total():
    return sum(i["price"] * i["qty"] for i in S.memo_items if i["status"] == "cart")


def new_item(cat, emoji, name, price, status="todo", qty=1):
    return {
        "id": uuid.uuid4().hex,
        "cat": cat,
        "emoji": emoji,
        "name": name,
        "status": status,  # "todo"(메모) 또는 "cart"(장바구니)
        "price": int(price),
        "qty": int(qty),
    }


def add_to_cart(cat, emoji, name, price):
    for item in S.memo_items:
        if item["name"] == name and item["status"] == "cart":
            item["qty"] += 1
            st.toast(f"🛒 {emoji} {name} 수량이 추가되었습니다!", icon="✅")
            return
    S.memo_items.append(new_item(cat, emoji, name, price, status="cart"))
    st.toast(f"🛒 {emoji} {name}을(를) 장바구니에 담았습니다!", icon="✨")


def add_to_memo(cat, emoji, name, price):
    if any(i["name"] == name for i in S.memo_items):
        st.toast(f"⚠️ {name}은(는) 이미 목록에 있습니다.", icon="📌")
        return
    S.memo_items.append(new_item(cat, emoji, name, price, status="todo"))
    st.toast(f"📌 {emoji} {name}을(를) 메모에 추가했습니다!", icon="📝")


# =====================================================================
# 팝업: 상품 상세 정보 및 담기
# =====================================================================
@st.dialog("🏷️ 상품 상세 정보")
def product_dialog(cat, emoji, name, base_price):
    price = price_of(cat, name, base_price)
    st.markdown(f"### {emoji} {name}")
    st.markdown(f"**분류:** {cat} &nbsp;|&nbsp; **기본 가격:** {won(price)}")
    st.markdown("마트 선반에서 이 상품을 어떻게 하시겠어요?")

    col1, col2 = st.columns(2)
    if col1.button("🛒 장바구니에 바로 담기", use_container_width=True, type="primary"):
        add_to_cart(cat, emoji, name, price)
        st.rerun()
    if col2.button("📝 메모장에 적어두기", use_container_width=True):
        add_to_memo(cat, emoji, name, price)
        st.rerun()


# =====================================================================
# 사이드바: 장바구니 & 메모장 (상시 확인 가능)
# =====================================================================
with st.sidebar:
    st.markdown("## 🛒 나의 장바구니 & 메모")

    # 예산 관리
    budget = st.number_input("🎯 오늘의 예산 (원)", min_value=0, step=5000, value=S.budget)
    S.budget = budget

    total = cart_total()
    left = S.budget - total

    # 예산 게이지바
    if S.budget > 0:
        pct = min(total / S.budget, 1.0)
        st.progress(pct, text=f"예산 사용률: {pct * 100:.1f}% (남은 금액: {won(left)})")
        if left < 0:
            st.error(f"🚨 예산을 {won(-left)} 초과했습니다!")

    st.markdown("---")

    # 탭으로 장바구니와 메모 구분
    sb_tab1, sb_tab2 = st.tabs(["🛒 장바구니", "📝 메모장"])

    with sb_tab1:
        carts = [i for i in S.memo_items if i["status"] == "cart"]
        if not carts:
            st.caption("장바구니가 비어 있습니다. 선반에서 상품을 클릭해 담아보세요!")
        for item in carts:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"**{item['emoji']} {item['name']}**<br>{won(item['price'] * item['qty'])}")
            c2.markdown(f"수량: {item['qty']}개")
            if c3.button("❌", key=f"del_cart_{item['id']}"):
                S.memo_items = [i for i in S.memo_items if i["id"] != item["id"]]
                st.rerun()

        if carts:
            st.markdown(f"**총 결제 예상금액: {won(total)}**")
            if st.button("🗑️ 장바구니 비우기", use_container_width=True):
                S.memo_items = [i for i in S.memo_items if i["status"] != "cart"]
                st.rerun()

    with sb_tab2:
        todos = [i for i in S.memo_items if i["status"] == "todo"]
        if not todos:
            st.caption("저장된 메모가 없습니다.")
        for item in todos:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"{item['emoji']} **{item['name']}**")
            if c2.button("🛒", key=f"move_{item['id']}", help="장바구니로 이동"):
                item["status"] = "cart"
                st.rerun()
            if c3.button("🗑️", key=f"del_todo_{item['id']}"):
                S.memo_items = [i for i in S.memo_items if i["id"] != item["id"]]
                st.rerun()

# =====================================================================
# 메인 화면: 마트 진열대 (선반 레이아웃)
# =====================================================================
st.markdown("# 🏬 우리동네 스마트 마트 진열대")
st.markdown("원하시는 상품을 클릭하여 **상세 정보**를 확인하고 장바구니나 메모장에 담아보세요!")

# 검색 기능
search_query = st.text_input("🔍 마트 내 상품 검색", placeholder="예: 사과, 삼겹살, 우유 등 입력...")

if search_query:
    st.markdown("### 🔎 검색 결과")
    found_items = []
    for cat_name, info in CATALOG.items():
        for emo, name, base in info["items"]:
            if search_query in name:
                found_items.append((cat_name, emo, name, base))

    if found_items:
        cols = st.columns(4)
        for idx, (cat_name, emo, name, base) in enumerate(found_items):
            price = price_of(cat_name, name, base)
            with cols[idx % 4]:
                if st.button(f"{emo}\n{name}\n{won(price)}", key=f"search_{name}", use_container_width=True):
                    product_dialog(cat_name, emo, name, base)
    else:
        st.info("검색 결과가 없습니다.")
    st.markdown("---")

# 카테고리별 마트 선반 진열
for cat_name, info in CATALOG.items():
    icon = info["icon"]
    items = info["items"]

    st.markdown(f'<div class="shelf-title">{icon} {cat_name} 진열대</div>', unsafe_allow_html=True)

    # 4열 선반 구조
    cols = st.columns(4)
    for idx, (emo, name, base) in enumerate(items):
        price = price_of(cat_name, name, base)
        col_idx = idx % 4
        with cols[col_idx]:
            if st.button(f"{emo}\n{name}\n{won(price)}", key=f"shelf_{cat_name}_{name}", use_container_width=True):
                product_dialog(cat_name, emo, name, base)

    st.markdown("<br>", unsafe_allow_html=True)
