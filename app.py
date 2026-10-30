import json
import uuid
from io import BytesIO

import streamlit as st

st.set_page_config(
    page_title="장보기 알림 메모",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 스타일: 진하고 알아보기 쉬운 색 / 스마트폰 한 화면용 compact 레이아웃
# =====================================================================
st.markdown(
    """
    <style>
    header[data-testid="stHeader"], footer, #MainMenu {display:none;}
    .block-container {padding:0.5rem 0.6rem 0.3rem 0.6rem; max-width:520px;}
    div[data-testid="stVerticalBlock"] {gap:0.3rem;}
    /* 스마트폰에서도 열이 세로로 쌓이지 않도록 */
    div[data-testid="stHorizontalBlock"] {flex-wrap:nowrap !important; gap:0.3rem !important;}
    div[data-testid="stColumn"], div[data-testid="column"] {min-width:0 !important;}
    .stButton button, .stDownloadButton button {
        padding:0.1rem 0.3rem; min-height:2rem;
        border:1.5px solid #37474F; font-weight:700; color:#102027;
    }
    .stButton button p {white-space:pre-line; line-height:1.15; margin:0;}
    /* 상품 타일: 아이콘 아래에 이름과 가격 */
    .st-key-grid .stButton button {height:4.6rem; width:100%; background:#FFFFFF;}
    .st-key-grid .stButton button:active {background:#FFD54F;}
    .st-key-grid .stButton button p {font-size:0.7rem; text-align:center;}
    .st-key-grid .stButton button p::first-line {font-size:1.8rem; line-height:1.35;}
    .stTabs [data-baseweb="tab"] {padding:0.2rem 0.6rem; height:2.1rem; font-weight:800;}
    label p {font-size:0.75rem !important; font-weight:700;}
    div[data-testid="stRadio"] label {padding-right:0.2rem;}
    h3 {font-size:1.15rem !important; padding:0 !important; margin:0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 상품 목록 (아이콘 / 이름 / 대략적인 2025~2026년 국내 마트 시세, 원)
# 가격은 앱에서 '💲가격' 모드로 언제든 바꿀 수 있어요.
# =====================================================================
RAW = {
    ("🥬", "야채"): """
        🥬 상추 2500
        🥦 브로콜리 3000
        🥕 당근 3000
        🧅 양파 3500
        🧄 마늘 6000
        🥔 감자 4500
        🍠 고구마 5000
        🥒 오이 2000
        🍅 방울토마토 6500
        🌿 대파 3000
        🫑 파프리카 3500
        🍄 버섯 2500
    """,
    ("🍎", "과일"): """
        🍎 사과 8000
        🍐 배 9000
        🍊 귤 6000
        🍌 바나나 3500
        🍇 포도 9000
        🍓 딸기 9000
        🍉 수박 20000
        🍑 복숭아 10000
        🥝 키위 6000
        🍋 레몬 3000
        🍍 파인애플 6000
        🫐 블루베리 7000
    """,
    ("🥩", "육류"): """
        🥩 소고기 25000
        🐖 삼겹살 17000
        🍖 목살 15000
        🍗 닭가슴살 6000
        🍗 닭다리 7000
        🐔 통닭 7500
        🥓 베이컨 5500
        🌭 소시지 6000
        🥩 불고기감 12000
        🍖 갈비 25000
        🥩 다짐육 8000
        🍖 햄 7000
    """,
    ("🐟", "수산물"): """
        🐟 고등어 5500
        🦑 오징어 6500
        🦐 새우 12000
        🐟 연어 15000
        🦀 꽃게 18000
        🐙 낙지 8000
        🐟 갈치 12000
        🦪 굴 7000
        🍥 어묵 4000
        🟫 김 4000
        🐟 멸치 8000
        🐠 명태 5000
    """,
    ("🥛", "유제품·계란"): """
        🥚 계란 30구 7500
        🥚 계란 10구 3500
        🥛 우유 2900
        🧀 슬라이스치즈 5500
        🧈 버터 6500
        🥛 요거트 4500
        🧀 모짜렐라 8000
        🍦 아이스크림 5000
        🥛 두유 4000
        🥚 메추리알 3500
        🍶 생크림 4500
        🥛 떠먹는요거트 3500
    """,
    ("🍞", "빵·간식"): """
        🍞 식빵 3500
        🥐 크루아상 5000
        🥯 베이글 4500
        🍪 쿠키 3500
        🍫 초콜릿 3000
        🍿 팝콘 2500
        🥨 과자 2000
        🍬 사탕 2500
        🍰 케이크 15000
        🍩 도넛 4000
        🍙 삼각김밥 1500
        🥜 견과류 8000
    """,
    ("🥤", "음료"): """
        🥤 콜라 2500
        🥤 사이다 2500
        🧃 오렌지주스 4500
        🧃 사과주스 3500
        ☕ 커피믹스 8000
        ☕ 캔커피 1500
        🍵 녹차 5000
        💧 생수 6000
        🫧 탄산수 6000
        ⚡ 이온음료 2000
        🧋 아이스티 3000
        🍼 보리차 3000
    """,
    ("🍚", "쌀·양념·가공"): """
        🍚 쌀 10kg 35000
        🍚 즉석밥 3000
        🍜 라면 4500
        🍝 파스타면 3000
        🧂 소금 2000
        🫙 간장 5500
        🌶️ 고추장 6500
        🫒 식용유 6500
        🍯 꿀 12000
        🥫 참치캔 4500
        🧈 두부 2500
        🥟 만두 7000
    """,
    ("🍳", "주방용품"): """
        🍳 프라이팬 15000
        🥘 냄비 20000
        🔪 칼 12000
        🥄 수저세트 8000
        🍽️ 접시세트 10000
        🥤 컵 3000
        🍱 밀폐용기 8000
        🧽 수세미 2000
        🧤 고무장갑 2500
        🥢 젓가락 3000
        🫖 주전자 15000
        🪵 도마 6000
    """,
    ("🧴", "생활용품"): """
        🧻 휴지 15000
        🧴 샴푸 8000
        🧼 비누 3000
        🪥 칫솔 3000
        🧴 주방세제 4000
        🧺 세탁세제 9000
        🌸 섬유유연제 8000
        🗑️ 쓰레기봉투 4000
        🔋 건전지 5000
        💡 전구 4000
        😷 마스크 5000
        🧴 핸드워시 3500
    """,
    ("🧸", "완구"): """
        🧸 곰인형 15000
        🧩 퍼즐 12000
        🚗 장난감자동차 8000
        🧱 블록 25000
        🎲 보드게임 20000
        ⚽ 축구공 15000
        🎨 색칠놀이 6000
        🤖 로봇 22000
        🎈 풍선 2000
        🪀 요요 3000
        🪁 연 4000
        🛴 킥보드 45000
    """,
    ("✏️", "문구·학용품"): """
        ✏️ 연필 3000
        🖊️ 볼펜 2500
        📓 공책 2000
        📐 자 1500
        🖍️ 색연필 5000
        ✂️ 가위 3000
        📎 클립 1500
        🗂️ 파일 2500
        🧴 풀 1500
        🖌️ 형광펜 3500
        🎒 필통 6000
        📅 다이어리 8000
    """,
    ("🐶", "반려동물"): """
        🐶 강아지사료 25000
        🐱 고양이사료 22000
        🦴 개껌 5000
        🥫 반려동물캔 2500
        🧻 배변패드 12000
        🏖️ 고양이모래 12000
        🎾 장난감 4000
        🐾 간식 5000
        🦮 목줄 8000
        🥣 밥그릇 6000
    """,
    ("💊", "건강·뷰티"): """
        💊 비타민 15000
        🩹 밴드 3000
        🌡️ 체온계 12000
        🧴 로션 9000
        ☀️ 선크림 12000
        💄 립밤 4000
        🧴 핸드크림 5000
        🪒 면도기 7000
        🧻 물티슈 3000
        🧴 손소독제 3000
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
CATS = list(CATALOG.keys())

MODE_MEMO, MODE_CART, MODE_PRICE = "📝 메모", "🛒 카트", "💲 가격"
IMP_BADGE = {1: "🟢", 2: "🟠", 3: "🔴"}
IMP_NAME = {1: "가격 봐서", 2: "보통", 3: "꼭 사기"}

# =====================================================================
# 상태
# =====================================================================
S = st.session_state
S.setdefault("memo_items", [])  # id, cat, emoji, name, imp, limit, status, price, qty
S.setdefault("budget", 0)
S.setdefault("prices", {})  # "카테고리|이름" -> 바꾼 가격
S.setdefault("history", {})  # 이름 -> 지난번 구매 가격
S.setdefault("favs", [])  # 즐겨찾기
S.setdefault("cat_idx", 0)
S.setdefault("mode", MODE_MEMO)
S.setdefault("imp_pick", 2)


def won(n):
    return f"{int(n):,}원"


def price_of(cat, name, base):
    return S.prices.get(f"{cat}|{name}", base)


def find(item_id):
    return next((i for i in S.memo_items if i["id"] == item_id), None)


def todos():
    return sorted([i for i in S.memo_items if i["status"] == "todo"], key=lambda x: -x["imp"])


def carts():
    return [i for i in S.memo_items if i["status"] == "cart"]


def cart_total():
    return sum(i["price"] * i["qty"] for i in carts())


def new_item(cat, emoji, name, imp, limit, status="todo", price=0, qty=0):
    return {
        "id": uuid.uuid4().hex,
        "cat": cat,
        "emoji": emoji,
        "name": name,
        "imp": imp,
        "limit": int(limit),
        "status": status,
        "price": int(price),
        "qty": int(qty),
    }


def budget_warn(extra):
    b = S.budget
    if b > 0 and cart_total() + extra > b:
        st.toast(f"⚠️ 예산을 {won(cart_total() + extra - b)} 넘었어요!", icon="🚨")


def add_cart(cat, emoji, name, price, qty=1):
    for i in carts():
        if i["name"] == name and i["price"] == price:
            i["qty"] += qty
            break
    else:
        S.memo_items.append(new_item(cat, emoji, name, 2, price, "cart", price, qty))
    S.history[name] = int(price)
    budget_warn(0)


# ---------------- 콜백 ----------------
def tile_click(cat, emoji, name, base):
    mode = S.mode
    p = price_of(cat, name, base)
    if mode == MODE_PRICE:
        S.pending = ("price", cat, emoji, name, base)
    elif mode == MODE_MEMO:
        if any(i["name"] == name and i["status"] == "todo" for i in S.memo_items):
            st.toast(f"{name}은(는) 이미 메모에 있어요", icon="📝")
        else:
            S.memo_items.append(new_item(cat, emoji, name, S.imp_pick, p))
            st.toast(f"{emoji} {name} 메모 추가 ({IMP_BADGE[S.imp_pick]}중요 {S.imp_pick})")
    else:  # 카트
        match = next((i for i in S.memo_items if i["name"] == name and i["status"] == "todo"), None)
        if match:  # 메모에 있는 물건이면 가격·수량 확인 창
            S.pending = ("buy", match["id"])
        else:
            add_cart(cat, emoji, name, p)
            st.toast(f"{emoji} {name} 카트 담기 ({won(p)})")


def open_buy(item_id):
    S.pending = ("buy", item_id)


def delete_item(item_id):
    S.memo_items = [i for i in S.memo_items if i["id"] != item_id]


def change_qty(item_id, d):
    it = find(item_id)
    if it:
        it["qty"] = max(1, it["qty"] + d)
        budget_warn(0)


def toggle_fav(item_id):
    it = find(item_id)
    if not it:
        return
    exist = [f for f in S.favs if f["name"] == it["name"]]
    if exist:
        S.favs = [f for f in S.favs if f["name"] != it["name"]]
    else:
        S.favs.append(
            {"cat": it["cat"], "emoji": it["emoji"], "name": it["name"], "imp": it["imp"],
             "limit": it["limit"] or S.history.get(it["name"], 0)}
        )


def fav_to_memo(idx):
    f = S.favs[idx]
    if any(i["name"] == f["name"] and i["status"] == "todo" for i in S.memo_items):
        st.toast("이미 메모에 있어요", icon="📝")
        return
    limit = S.history.get(f["name"], f["limit"])
    S.memo_items.append(new_item(f["cat"], f["emoji"], f["name"], f["imp"], limit))
    st.toast(f"⭐ {f['name']} 메모 추가")


def fav_remove(idx):
    S.favs.pop(idx)


def move_cat(d):
    S.cat_idx = (S.cat_idx + d) % len(CATS)


def set_cat(i):
    S.cat_idx = i


def custom_add():
    name = S.get("cu_name", "").strip()
    price = int(S.get("cu_price", 0))
    cat = CATS[S.cat_idx]
    icon = CATALOG[cat]["icon"]
    if not name:
        st.toast("상품명을 적어 주세요", icon="⚠️")
        return
    if S.mode == MODE_CART:
        add_cart(cat, icon, name, price)
        st.toast(f"{icon} {name} 카트 담기")
    else:
        S.memo_items.append(new_item(cat, icon, name, S.imp_pick, price or S.history.get(name, 0)))
        st.toast(f"{icon} {name} 메모 추가")
    S.cu_name = ""
    S.cu_price = 0


# =====================================================================
# 팝업창
# =====================================================================
@st.dialog("🛒 가격·수량 확인")
def buy_dialog(item_id):
    it = find(item_id)
    if it is None:
        st.rerun()
    editing = it["status"] == "cart"
    hist = S.history.get(it["name"])
    default_price = it["price"] if editing else (hist or it["limit"] or 0)
    st.markdown(f"### {it['emoji']} {it['name']}")
    st.caption(f"{it['cat']} · {IMP_BADGE[it['imp']]} 중요도 {it['imp']} ({IMP_NAME[it['imp']]})")
    if hist:
        st.caption(f"💡 지난번 구매 가격: {won(hist)}")

    c1, c2 = st.columns(2)
    price = c1.number_input("1개 가격(원)", min_value=0, step=100, value=int(default_price))
    qty = c2.number_input("수량", min_value=1, step=1, value=int(it["qty"] or 1))

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

    line = price * qty
    st.markdown(f"**합계 {won(line)}**")
    if S.budget > 0:
        base_total = cart_total() - (it["price"] * it["qty"] if editing else 0)
        left = S.budget - base_total - line
        if left < 0:
            st.error(f"🚨 예산을 {won(-left)} 넘어요.")
        else:
            st.info(f"담고 나면 예산 {won(left)} 남아요.")

    b1, b2 = st.columns(2)
    if b1.button("✅ 저장" if editing else "✅ 카트에 담기", type="primary", use_container_width=True):
        it["status"] = "cart"
        it["price"] = int(price)
        it["qty"] = int(qty)
        S.history[it["name"]] = int(price)
        st.rerun()
    if not editing and it["imp"] < 3:
        if b2.button("🚫 패스(안 사요)" if too_expensive else "패스", use_container_width=True):
            delete_item(item_id)
            st.rerun()
    elif editing:
        if b2.button("↩ 메모로 되돌리기", use_container_width=True):
            it["status"] = "todo"
            st.rerun()


@st.dialog("💲 가격 수정")
def price_dialog(cat, emoji, name, base):
    cur = price_of(cat, name, base)
    st.markdown(f"### {emoji} {name}")
    st.caption(f"기본 시세 {won(base)}")
    new = st.number_input("내 가격(원)", min_value=0, step=100, value=int(cur))
    c1, c2 = st.columns(2)
    if c1.button("💾 저장", type="primary", use_container_width=True):
        S.prices[f"{cat}|{name}"] = int(new)
        st.rerun()
    if c2.button("기본값으로", use_container_width=True):
        S.prices.pop(f"{cat}|{name}", None)
        st.rerun()


def qr_png(url):
    import qrcode

    buf = BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    return buf.getvalue()


# =====================================================================
# 상단: 제목 + 즐겨찾기 / 예산 / 저장 / QR
# =====================================================================
h = st.columns([2.6, 1, 1, 1, 1])
h[0].markdown("### 🛒 장보기 메모")

with h[1].popover("⭐", use_container_width=True):
    st.markdown("**⭐ 즐겨찾기** (눌러서 메모에 추가)")
    if not S.favs:
        st.caption("메모 목록에서 ⭐를 누르면 여기에 저장돼요.")
    for idx, f in enumerate(S.favs):
        a, b = st.columns([5, 1])
        a.button(f"{f['emoji']} {f['name']} ➕", key=f"fav_{idx}", on_click=fav_to_memo,
                 args=(idx,), use_container_width=True)
        b.button("✕", key=f"favdel_{idx}", on_click=fav_remove, args=(idx,))

with h[2].popover("💰", use_container_width=True):
    nb = st.number_input("오늘 예산(원)", min_value=0, step=5000, value=int(S.budget))
    if nb != S.budget:
        S.budget = int(nb)
        st.rerun()
    st.caption("0원이면 예산 기능을 쓰지 않아요.")

with h[3].popover("💾", use_container_width=True):
    st.caption("메모·가격·즐겨찾기를 파일로 저장했다가 다시 불러올 수 있어요.")
    data = {k: S[k] for k in ("memo_items", "budget", "prices", "history", "favs")}
    st.download_button("⬇ 저장하기", json.dumps(data, ensure_ascii=False),
                       "shopping_memo.json", "application/json", use_container_width=True)
    up = st.file_uploader("불러오기", type="json")
    if up is not None:
        sig = f"{up.name}-{up.size}"
        if S.get("loaded_sig") != sig:
            try:
                d = json.loads(up.getvalue().decode("utf-8"))
                S.memo_items = d.get("memo_items", [])
                S.budget = int(d.get("budget", 0))
                S.prices = d.get("prices", {})
                S.history = d.get("history", {})
                S.favs = d.get("favs", [])
                S.loaded_sig = sig
                st.rerun()
            except Exception:
                st.error("파일을 읽지 못했어요.")

with h[4].popover("📱", use_container_width=True):
    st.caption("배포된 앱 주소를 넣으면 QR이 만들어져요.")
    url = st.text_input("앱 주소", placeholder="https://내앱.streamlit.app")
    if url:
        try:
            st.image(qr_png(url), width=200)
        except Exception:
            st.error("QR 생성 실패: requirements.txt에 qrcode[pil]이 있는지 확인해 주세요.")

# =====================================================================
# 예산 게이지 (담을수록 채워져요)
# =====================================================================
total = cart_total()
n_cart = sum(i["qty"] for i in carts())
td = todos()
est = sum(i["limit"] for i in td)

if S.budget <= 0:
    st.markdown(
        f"<div style='border:2px solid #263238;border-radius:10px;padding:5px 8px;"
        f"font-weight:800'>🧾 카트 {won(total)} · {n_cart}개 &nbsp; "
        f"<span style='color:#C62828'>💰 예산을 먼저 정해 주세요 (위 💰 버튼)</span></div>",
        unsafe_allow_html=True,
    )
else:
    pct = total / S.budget * 100
    color = "#2E7D32" if pct < 80 else ("#EF6C00" if pct <= 100 else "#C62828")
    left = S.budget - total
    left_txt = f"남음 {won(left)}" if left >= 0 else f"🚨 {won(-left)} 초과"
    st.markdown(
        f"""
        <div style="border:2px solid #263238;border-radius:10px;padding:5px 8px;background:#fff">
          <div style="display:flex;justify-content:space-between;font-weight:800;font-size:0.95rem">
            <span>🧾 {won(total)}</span><span style="color:{color}">{left_txt}</span></div>
          <div style="background:#CFD8DC;border-radius:6px;height:14px;overflow:hidden;margin:3px 0">
            <div style="width:{min(pct,100):.0f}%;background:{color};height:100%"></div></div>
          <div style="display:flex;justify-content:space-between;font-size:0.7rem;font-weight:700;color:#37474F">
            <span>카트 {n_cart}개 · 메모 {len(td)}개(예상 {won(est)})</span>
            <span>예산 {won(S.budget)} · {pct:.0f}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =====================================================================
# 탭: 담기 / 메모 / 카트
# =====================================================================
tab_shop, tab_memo, tab_cart = st.tabs(["🛍 담기", "📝 메모", "🧾 카트"])

# ---------------- 담기 탭 ----------------
with tab_shop:
    m1, m2 = st.columns([5, 3])
    m1.radio("모드", [MODE_MEMO, MODE_CART, MODE_PRICE], key="mode", horizontal=True,
             label_visibility="collapsed")
    m2.radio("중요도", [1, 2, 3], key="imp_pick", horizontal=True, label_visibility="collapsed",
             format_func=lambda x: f"{IMP_BADGE[x]}{x}", disabled=(S.mode != MODE_MEMO))

    cat = CATS[S.cat_idx]
    p = st.columns([1, 4, 1, 1])
    p[0].button("◀", key="prev", on_click=move_cat, args=(-1,), use_container_width=True)
    p[1].markdown(
        f"<div style='text-align:center;font-weight:900;font-size:1.05rem;line-height:2rem;"
        f"background:#0D47A1;color:#fff;border-radius:8px'>"
        f"{CATALOG[cat]['icon']} {cat} <span style='font-size:0.7rem'>({S.cat_idx + 1}/{len(CATS)})</span></div>",
        unsafe_allow_html=True,
    )
    p[2].button("▶", key="next", on_click=move_cat, args=(1,), use_container_width=True)
    with p[3].popover("📂", use_container_width=True):
        for i, c in enumerate(CATS):
            st.button(f"{CATALOG[c]['icon']} {c}", key=f"jump_{i}", on_click=set_cat, args=(i,),
                      use_container_width=True)

    with st.container(key="grid", height=268):
        items = CATALOG[cat]["items"]
        for r in range(0, len(items), 4):
            cols = st.columns(4)
            for col, (emo, name, base) in zip(cols, items[r:r + 4]):
                price = price_of(cat, name, base)
                col.button(f"{emo}\n{name}\n{price:,}원", key=f"t_{cat}_{name}",
                           on_click=tile_click, args=(cat, emo, name, base),
                           use_container_width=True)

    with st.form("custom", border=False):
        f1, f2, f3 = st.columns([3, 2, 1.2])
        f1.text_input("직접 입력", key="cu_name", placeholder="없는 상품은 직접 입력",
                      label_visibility="collapsed")
        f2.number_input("가격", key="cu_price", min_value=0, step=100, value=0,
                        label_visibility="collapsed")
        f3.form_submit_button("➕", on_click=custom_add, use_container_width=True)

# ---------------- 메모 탭 ----------------
with tab_memo:
    st.markdown(f"**남은 메모 {len(td)}개 · 예상 {won(est)}**")
    with st.container(height=330, border=True):
        if not td:
            st.caption("남은 메모가 없어요. 🎉" if carts() else "담기 탭에서 살 물건을 추가해 보세요.")
        faved = {f["name"] for f in S.favs}
        for it in td:
            a, b, c, d = st.columns([6, 1, 1, 1])
            lim = f" · 기준 {won(it['limit'])}" if it["limit"] else ""
            a.markdown(
                f"{IMP_BADGE[it['imp']]} **{it['emoji']} {it['name']}**<br>"
                f"<span style='color:#455A64;font-size:0.72rem'>{it['cat']} · {IMP_NAME[it['imp']]}{lim}</span>",
                unsafe_allow_html=True,
            )
            b.button("🛒", key=f"buy_{it['id']}", on_click=open_buy, args=(it["id"],), help="카트에 담기")
            c.button("★" if it["name"] in faved else "☆", key=f"fav_t_{it['id']}",
                     on_click=toggle_fav, args=(it["id"],), help="즐겨찾기")
            d.button("🗑", key=f"del_{it['id']}", on_click=delete_item, args=(it["id"],), help="삭제")

# ---------------- 카트 탭 ----------------
with tab_cart:
    st.markdown(f"**카트 {n_cart}개 · {won(total)}**")
    with st.container(height=330, border=True):
        cl = carts()
        if not cl:
            st.caption("아직 담은 물건이 없어요.")
        for it in cl:
            a, b, c, d, e = st.columns([5, 1, 1, 1, 1])
            a.markdown(
                f"**{it['emoji']} {it['name']}** ×{it['qty']}<br>"
                f"<span style='color:#455A64;font-size:0.72rem'>{won(it['price'])} → "
                f"<b>{won(it['price'] * it['qty'])}</b></span>",
                unsafe_allow_html=True,
            )
            b.button("➖", key=f"m_{it['id']}", on_click=change_qty, args=(it["id"], -1),
                     disabled=it["qty"] <= 1)
            c.button("➕", key=f"p_{it['id']}", on_click=change_qty, args=(it["id"], 1))
            d.button("✏", key=f"e_{it['id']}", on_click=open_buy, args=(it["id"],), help="가격·수량 수정")
            e.button("🗑", key=f"x_{it['id']}", on_click=delete_item, args=(it["id"],), help="카트에서 빼기")

# =====================================================================
# 팝업 열기 (콜백에서 예약한 것)
# =====================================================================
pend = S.pop("pending", None)
if pend:
    if pend[0] == "buy":
        buy_dialog(pend[1])
    elif pend[0] == "price":
        price_dialog(*pend[1:])
