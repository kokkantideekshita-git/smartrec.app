"""
SMARTREC - "Your shopping, made smarter."
=========================================
app.py
------
This is the Streamlit user interface of SMARTREC.

Pages:
    🏠 Home             - landing page
    👤 New Customer     - registration form + unique SMR-XXXX id
    🔑 Existing Customer- sign in with a SMARTREC id
    🛍️ Recommendations  - the personalised Top 5
    📊 AI Insights      - the machine learning dashboard
    🧠 How It Works     - how SMARTREC thinks
    ℹ️ About            - project information

Run it with:   streamlit run app.py
"""

import time

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import data
import model
import ui

st.set_page_config(
    page_title="SMARTREC · Your shopping, made smarter.",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===========================================================================
# SMALL HELPERS
# ===========================================================================

NAV_ITEMS = [
    ("🏠", "Home", "home"),
    ("🛍️", "Recommendations", "recommendations"),
    ("📊", "AI Insights", "insights"),
    ("🧠", "How It Works", "how"),
    ("ℹ️", "About", "about"),
]

# This item only appears once the customer has signed in with their SMR-XXXX ID.
CART_NAV_ITEM = ("🛒", "Cart", "cart")

# how many catalogue rows the admin table draws before asking them to search
TABLE_LIMIT = 40


def visible_nav_items():
    """The navigation bar items for the current visitor."""
    if st.session_state.get("customer_id"):
        items = []
        for item in NAV_ITEMS:
            items.append(item)
            if item[2] == "recommendations":
                items.append(CART_NAV_ITEM)
        return items
    return list(NAV_ITEMS)


def start_session():
    """Create the session variables the first time the app runs."""
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = None
    if "showed_loader" not in st.session_state:
        st.session_state.showed_loader = False
    if "data_version" not in st.session_state:
        st.session_state.data_version = 0
    if "product_id" not in st.session_state:
        st.session_state.product_id = None
    # the admin is a completely separate login from the customer one
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_edit_id" not in st.session_state:
        st.session_state.admin_edit_id = None


def go_to(page):
    """Switch page and redraw so the new page is painted immediately."""
    st.session_state.page = page
    st.rerun()


def current_customer():
    """Always read the customer fresh from customers.csv (never from memory)."""
    customer_id = st.session_state.get("customer_id")
    if not customer_id:
        return None
    return data.find_customer(customer_id)


def open_product(product_id):
    """Open the full product page (the card's "View details" button)."""
    st.session_state.product_id = product_id
    go_to("product")


def require_login(message):
    """
    Return the logged-in customer, or show a friendly gate and stop the page.
    Used by the pages that only make sense for a signed-in customer.
    """
    customer = current_customer()
    if customer:
        return customer

    st.markdown(ui.hero_html(), unsafe_allow_html=True)
    st.warning(message)
    left, right = st.columns(2)
    if left.button("👤  Existing Customer", key="gate_login", type="primary", width="stretch"):
        go_to("login")
    if right.button("🆕  New Customer", key="gate_register", type="primary", width="stretch"):
        go_to("register")
    return None


def copy_id_component(customer_id):
    """A small copy-to-clipboard button (works inside Streamlit)."""
    html = f"""
    <div style="display:flex; gap:10px; align-items:center; justify-content:center;
                font-family:'Segoe UI',sans-serif; margin-top:6px;">
      <textarea id="smr_id" readonly
        style="position:absolute;left:-9999px;opacity:0;">{customer_id}</textarea>
      <button id="smr_copy" onclick="smrCopy()"
        style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;border:none;
               padding:9px 20px;border-radius:12px;font-weight:700;font-size:0.9rem;
               cursor:pointer;box-shadow:0 8px 20px rgba(79,70,229,.32);">
        📋 Copy Customer ID
      </button>
      <span id="smr_msg" style="color:#059669;font-weight:700;font-size:0.88rem;"></span>
    </div>
    <script>
      function smrCopy() {{
        var box = document.getElementById("smr_id");
        var msg = document.getElementById("smr_msg");
        var done = function() {{ msg.innerHTML = "✓ Copied!"; }};
        var fallback = function() {{
          box.style.position = "static"; box.style.opacity = "1";
          box.select(); document.execCommand("copy");
          box.style.position = "absolute"; box.style.opacity = "0";
          done();
        }};
        try {{
          if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(box.value).then(done, fallback);
          }} else {{ fallback(); }}
        }} catch (err) {{ fallback(); }}
      }}
    </script>
    """
    st.iframe(html, height=70)


def loading_sequence():
    """
    A short, polished loading moment while SMARTREC thinks.

    We never make the user wait longer than about one second.
    """
    messages = [
        "Understanding your preferences…",
        "Analysing shopping behaviour…",
        "Finding your best matches…",
    ]
    placeholder = st.empty()
    for index, message in enumerate(messages):
        with placeholder.container():
            st.markdown(
                f'<div class="sr-loader"><span class="ring"></span>'
                f'<span class="txt">{message}</span></div>',
                unsafe_allow_html=True,
            )
        time.sleep(0.22)
    with placeholder.container():
        st.markdown(
            '<div class="sr-loader"><span>✨</span>'
            '<span class="txt"><b>Recommendations ready!</b></span></div>',
            unsafe_allow_html=True,
        )
    time.sleep(0.18)
    placeholder.empty()


def money(value):
    """Format a number the Indian way: 2499 -> Rs 2,499."""
    return f"₹{float(value):,.0f}"


def price_text(value):
    """
    Show a stored price in the edit box without quietly rounding it.

    1499 comes back as "1499" and 1234.5 comes back as "1234.50", so saving a
    product twice never changes the price behind the admin's back.
    """
    number = float(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.2f}"


def chart_layout(figure, height=330):
    """Make every Plotly chart match the SMARTREC style."""
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=12),
        margin=dict(l=10, r=10, t=34, b=10),
        height=height,
        showlegend=False,
    )
    figure.update_xaxes(gridcolor="rgba(148,163,184,0.16)", zeroline=False)
    figure.update_yaxes(gridcolor="rgba(148,163,184,0.16)", zeroline=False)
    return figure


# ===========================================================================
# THE TRAINED MODEL  (trained once, then reused)
# ===========================================================================


@st.cache_resource(show_spinner=False)
def get_model_bundle():
    """Train (or reuse) the SMARTREC model. Cached for the whole session."""
    return model.train_smartrec_model()


def customer_rankings(bundle, customer):
    """
    Real ML scoring for the logged-in customer.
    Returns the ranked DataFrame (probability for every product).
    """
    interactions = data.get_customer_interactions(customer["Customer_ID"])
    return model.score_products(bundle, customer, interactions), interactions


# ===========================================================================
# NAVIGATION BAR
# ===========================================================================


def render_navbar():
    with st.container(key="navbar"):
        left, middle, right = st.columns([1.35, 6.4, 0.75])

        with left:
            st.markdown(ui.logo_html(), unsafe_allow_html=True)

        with middle:
            items = visible_nav_items()
            buttons = st.columns(len(items))
            customer_id = st.session_state.get("customer_id")
            for column, (icon, label, page) in zip(buttons, items):
                with column:
                    active = st.session_state.page == page
                    # the cart button shows how many units are really in cart.csv
                    caption = f"{icon} {label}"
                    if page == "cart" and customer_id:
                        units = data.cart_count(customer_id)
                        caption = f"{icon} {label} ({units})" if units else f"{icon} {label}"
                    if st.button(
                        caption,
                        key=f"nav_{page}",
                        type="primary" if active else "secondary",
                        width="stretch",
                        help=f"Go to {label}",
                    ):
                        go_to(page)

        with right:
            is_dark = st.session_state.theme == "dark"
            if st.button(
                "☀️" if is_dark else "🌙",
                key="nav_theme",
                help="Switch theme",
                width="stretch",
            ):
                st.session_state.theme = "light" if is_dark else "dark"
                st.rerun()


def render_customer_chip(bundle):
    """A small bar showing who is logged in (visible on every inner page)."""
    customer = current_customer()
    if not customer:
        return None

    summary = model.behaviour_summary(customer)
    left, middle, right = st.columns([2.4, 3.2, 1.4])

    with left:
        st.markdown(
            f"""
            <div class="sr-chip" style="padding:8px 14px;">
                <span style="font-size:1.05rem;">👤</span>
                <b style="color:var(--text);">{customer['Name']}</b>
                <span style="color:var(--primary);font-weight:800;">{customer['Customer_ID']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with middle:
        st.markdown(
            f"""
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <span class="sr-chip">👁️ {summary['views']} views</span>
              <span class="sr-chip">🛒 {summary['cart_adds']} cart adds</span>
              <span class="sr-chip">💳 {summary['purchases']} purchases</span>
              <span class="sr-chip">💰 {money(summary['total_spend'])}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        if st.button("🚪 Sign out", key="sign_out", width="stretch"):
            st.session_state.customer_id = None
            st.session_state.product_id = None
            st.session_state.showed_loader = False
            st.toast("You have been signed out. See you soon! 👋")
            go_to("home")
    return customer


# ===========================================================================
# PAGE 1 · HOME
# ===========================================================================


def page_home():
    hero_left, hero_right = st.columns([1.15, 1])

    with hero_left:
        st.markdown(ui.hero_html(), unsafe_allow_html=True)
        st.markdown("")
        st.markdown(
            '<span class="sr-tagline">✦ SMARTREC — Your shopping, made smarter.</span>',
            unsafe_allow_html=True,
        )

    with hero_right:
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">🧠 What happens when you log in?</div>
              <div class="sr-card-text">
                SMARTREC joins your profile with the product catalogue, builds
                the right features and asks a trained Logistic Regression model
                <b>how likely you are to buy each product</b>. The five best
                matches are shown to you — and every click is remembered.
              </div>
            </div>
            <div style="height:14px"></div>
            <div class="sr-card">
              <div class="sr-card-title">📦 Your data stays yours</div>
              <div class="sr-card-text">
                Every profile lives in <b>customers.csv</b> on this computer.
                Restart the app and SMARTREC still knows you by your
                <b>SMR-XXXX</b> Customer ID.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown(
        "<h3 style='margin:8px 0 2px 0; letter-spacing:-0.5px;'>Choose how you want to continue</h3>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        with st.container(key="choice_existing"):
            st.markdown(
                """
                <div class="sr-choice-icon">👤</div>
                <div class="sr-choice-title">Existing Customer</div>
                <div class="sr-choice-text">Already have a SMARTREC ID?
                Enter it and we reload your profile, your previous purchases and
                your latest behaviour.</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "👤  Existing Customer",
                key="home_existing",
                type="primary",
                width="stretch",
            ):
                go_to("login")

    with right:
        with st.container(key="choice_new"):
            st.markdown(
                """
                <div class="sr-choice-icon">🆕</div>
                <div class="sr-choice-title">New Customer</div>
                <div class="sr-choice-text">First time here? Tell us what you
                like and your budget. We create a permanent SMARTREC Customer
                ID for you in seconds.</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "🆕  New Customer",
                key="home_new",
                type="primary",
                width="stretch",
            ):
                go_to("register")

    # live numbers taken from the real model + real data
    bundle = get_model_bundle()
    report = bundle["cleaning_report"]
    metrics = bundle["metrics"]

    st.markdown("")
    st.markdown(ui.section_title("SMARTREC right now", "live numbers from the trained model"), unsafe_allow_html=True)
    cards = st.columns(4)
    stats = [
        ("PRODUCTS IN CATALOGUE", f"{len(data.load_products())}", "items SMARTREC can recommend"),
        ("CUSTOMERS RECOGNISED", f"{len(data.load_customers())}", "stored permanently in customers.csv"),
        ("MODEL ACCURACY", f"{metrics['accuracy'] * 100:.1f}%", f"on {report['rows_after']:,} cleaned rows"),
        ("MODEL ROC-AUC", f"{metrics['roc_auc']:.3f}", "how well the model separates buyers"),
    ]
    for column, (title, value, subtitle) in zip(cards, stats):
        with column:
            st.markdown(ui.stat_card(title, value, subtitle), unsafe_allow_html=True)

    # The admin login link. It sits at the very bottom of the Home page only,
    # so a customer browsing the recommendations never sees it. It leads to a
    # login form - no password, no product controls, are shown here.
    st.markdown("")
    admin_hint, _ = st.columns([1, 3])
    with admin_hint:
        if st.button("⚙️  Admin", key="home_admin_link", width="content"):
            go_to("admin_login")


# ===========================================================================
# PAGE 2 · NEW CUSTOMER REGISTRATION
# ===========================================================================


def page_register():
    st.markdown(
        """
        <span class="sr-eyebrow">🆕 NEW CUSTOMER</span>
        <div class="sr-hero-title" style="font-size:2.3rem;">Create your SMARTREC profile</div>
        <p class="sr-hero-sub">Tell us what you like and SMARTREC creates your own
        permanent Customer ID. No password needed — the ID <i>is</i> your identity.</p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    left, right = st.columns([1.25, 1])

    with left:
        with st.container(key="register_card"):
            name = st.text_input(
                "👤 Full name",
                placeholder="Rahul Kumar",
                max_chars=60,
                key="reg_name",
            )
            contact = st.text_input(
                "📧 Email or phone number",
                placeholder="rahul@gmail.com",
                max_chars=80,
                key="reg_contact",
            )

            st.markdown(
                '<p style="font-size:0.88rem;font-weight:650;margin:6px 0 2px 0;">'
                "🎯 Interested categories</p>",
                unsafe_allow_html=True,
            )
            categories = st.pills(
                "Interested categories",
                data.PRODUCT_CATEGORIES,
                selection_mode="multi",
                default=["Electronics"],
                label_visibility="collapsed",
            )

            st.markdown("")
            st.markdown(
                '<p style="font-size:0.88rem;font-weight:650;margin:6px 0 2px 0;">'
                "💰 Preferred budget</p>",
                unsafe_allow_html=True,
            )
            budget = st.slider(
                "Preferred budget",
                min_value=500,
                max_value=30000,
                value=(1000, 10000),
                step=500,
                label_visibility="collapsed",
            )
            st.markdown(
                f'<p style="font-size:0.84rem;color:var(--muted);">'
                f"Your range: <b style='color:var(--primary);'>{money(budget[0])} — "
                f"{money(budget[1])}</b></p>",
                unsafe_allow_html=True,
            )
            st.markdown("")

            if st.button("✨  Create My Profile", key="create_profile", type="primary", width="stretch"):
                # ---------- simple validation ----------
                problems = []
                if name.strip() == "":
                    problems.append("please enter your name")
                if contact.strip() == "":
                    problems.append("please enter an email or phone number")
                if not categories:
                    problems.append("please choose at least one category")
                if budget[0] >= budget[1]:
                    problems.append("your minimum budget must be lower than your maximum")

                if problems:
                    st.error("Almost there — " + ", ".join(problems) + ".")
                else:
                    # ---- create the permanent profile ----
                    new_customer = data.save_new_customer(
                        name=name.strip(),
                        contact=contact.strip(),
                        categories=categories,
                        min_budget=budget[0],
                        max_budget=budget[1],
                    )
                    st.session_state.customer_id = new_customer["Customer_ID"]
                    st.session_state.showed_loader = False
                    st.session_state.data_version += 1
                    st.toast(
                        f"Profile created · {new_customer['Customer_ID']}",
                        icon="🎉",
                    )
                    go_to("welcome")

    with right:
        with st.container(key="register_info"):
            st.markdown(
                """
                <div class="sr-card-title">🎁 What you get with your ID</div>
                <div class="sr-card-text">
                  Your <b>SMR-XXXX Customer ID</b> is your key to SMARTREC.
                </div>
                <div class="sr-reason">✓ A permanent profile saved in <b>customers.csv</b></div>
                <div class="sr-reason">✓ Returning customers are recognised instantly</div>
                <div class="sr-reason">✓ Your views, cart adds and purchases are remembered</div>
                <div class="sr-reason">✓ Recommendations get better after every click</div>
                <div class="sr-reason">✓ Products you already bought are never shown again</div>
                <div style="height:10px"></div>
                <div class="sr-card-title">🔒 No passwords</div>
                <div class="sr-card-text">
                  For this academic project the Customer ID is enough to identify you.
                  It starts at <b>SMR-1001</b> and is never reused.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")
    if st.button("←  Back to Home", key="register_back"):
        go_to("home")


# ===========================================================================
# PAGE 3 · WELCOME (a new customer sees their brand new ID)
# ===========================================================================


def page_welcome():
    customer = current_customer()
    if not customer:
        go_to("home")
        return

    st.markdown(
        f"""
        <div style="text-align:center;">
          <span class="sr-eyebrow">🎉 WELCOME TO SMARTREC</span>
          <div class="sr-hero-title" style="font-size:2.5rem;">Welcome, {customer['Name']}!</div>
          <p class="sr-hero-sub" style="margin:0 auto;">
            Your SMARTREC Customer ID is ready. Save it — you will use it every
            time you return to SMARTREC.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown(
            ui.customer_id_box_html(customer["Customer_ID"], customer["Name"]),
            unsafe_allow_html=True,
        )
        copy_id_component(customer["Customer_ID"])
    with right:
        st.markdown(
            f"""
            <div class="sr-card">
              <div class="sr-card-title">🧠 How your first recommendations work</div>
              <div class="sr-card-text">
                You are new, so SMARTREC has no views or purchases for you yet.
                It uses the three things it already knows:
                <div class="sr-reason">✓ Your favourite categories —
                  <b>{customer['Categories'].replace('|', ', ')}</b></div>
                <div class="sr-reason">✓ Your budget — <b>{money(customer['Min_Budget'])} to
                  {money(customer['Max_Budget'])}</b></div>
                <div class="sr-reason">✓ What thousands of past customers did with
                  the same products</div>
                As soon as you view, save or buy something, this profile starts
                growing and your recommendations get more personal.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    columns = st.columns([1, 1, 1.2])
    with columns[0]:
        if st.button("🏠  Home", key="welcome_home", width="stretch"):
            go_to("home")
    with columns[1]:
        if st.button("📊  AI Insights", key="welcome_insights", width="stretch"):
            go_to("insights")
    with columns[2]:
        if st.button("✨  Get My Recommendations", key="welcome_go", type="primary", width="stretch"):
            go_to("recommendations")


# ===========================================================================
# PAGE 4 · EXISTING CUSTOMER SIGN IN
# ===========================================================================


def page_login():
    st.markdown(
        """
        <span class="sr-eyebrow">👋 WELCOME BACK</span>
        <div class="sr-hero-title" style="font-size:2.3rem;">Enter your SMARTREC Customer ID</div>
        <p class="sr-hero-sub">We will reload your profile, your previous purchases
        and your latest behaviour — no new account is created.</p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    left, right = st.columns([1.05, 1])

    with left:
        with st.container(key="login_card"):
            entered = st.text_input(
                "SMARTREC Customer ID",
                placeholder="SMR-1001",
                max_chars=20,
                key="login_id",
            )
            st.markdown(
                '<p style="font-size:0.8rem;color:var(--muted);margin-top:-8px;">'
                "IDs look like <b>SMR-1001</b>. You only need this one thing.</p>",
                unsafe_allow_html=True,
            )
            if st.button("✨  Continue", key="login_go", type="primary", width="stretch"):
                cleaned = entered.strip().upper()
                found = data.find_customer(cleaned) if cleaned else None
                if found is None:
                    st.error(
                        f"We could not find **{cleaned or 'an empty ID'}**. "
                        "Please check the ID, or register as a new customer."
                    )
                else:
                    st.session_state.customer_id = found["Customer_ID"]
                    st.session_state.showed_loader = False
                    st.session_state.data_version += 1
                    st.toast(f"Welcome back, {found['Name']}! 👋", icon="✅")
                    go_to("returning")

    with right:
        customers = data.load_customers()
        if len(customers) > 0:
            recent = customers.tail(4).iloc[::-1]
            rows = "".join(
                f'<div class="sr-reason">🔑 <b>{row["Customer_ID"]}</b> — {row["Name"]}</div>'
                for _, row in recent.iterrows()
            )
            st.markdown(
                f"""
                <div class="sr-card">
                  <div class="sr-card-title">🗂️ Customers on this computer</div>
                  <div class="sr-card-text">
                    SMARTREC has {len(customers)} registered customer(s).
                    Use any ID below to test the returning-customer flow.
                  </div>
                  <div style="height:8px"></div>
                  {rows}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="sr-card">
                  <div class="sr-card-title">🆕 No customers yet?</div>
                  <div class="sr-card-text">Register as a new customer first —
                  SMARTREC will create your SMR-1001 ID and save it permanently.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")
    if st.button("←  Back to Home", key="login_back"):
        go_to("home")


# ===========================================================================
# PAGE 5 · RETURNING CUSTOMER GREETING
# ===========================================================================


def page_returning():
    customer = current_customer()
    if not customer:
        go_to("home")
        return

    summary = model.behaviour_summary(customer)
    st.markdown(
        f"""
        <div class="sr-fade-up">
          <span class="sr-eyebrow">👋 WELCOME BACK</span>
          <div class="sr-hero-title" style="font-size:2.4rem;">
            Welcome back, {customer['Name']}! 👋</div>
          <p class="sr-hero-sub">We've updated your recommendations based on your
          latest shopping activity.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    cards = st.columns(5)
    stats = [
        ("CUSTOMER ID", customer["Customer_ID"], f"since {customer['Created_On']}"),
        ("PRODUCTS VIEWED", summary["views"], "lifetime views"),
        ("CART ADDITIONS", summary["cart_adds"], "lifetime cart adds"),
        ("PURCHASES", summary["purchases"], "previous purchases"),
        ("TOTAL SPEND", money(summary["total_spend"]), f"cart conversion {summary['cart_conversion']}%"),
    ]
    for column, (title, value, subtitle) in zip(cards, stats):
        with column:
            plain = " plain" if title in ("CUSTOMER ID", "TOTAL SPEND") else ""
            st.markdown(
                f'<div class="sr-stat"><div class="k">{title}</div>'
                f'<div class="v{plain}">{value}</div><div class="s">{subtitle}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    left, right, middle = st.columns([1, 1, 1.4])
    with left:
        if st.button("🛍️  Show My Recommendations", key="ret_go", type="primary", width="stretch"):
            go_to("recommendations")
    with middle:
        if st.button("📊  AI Insights", key="ret_insights", width="stretch"):
            go_to("insights")
    with right:
        if st.button("🏠  Home", key="ret_home", width="stretch"):
            go_to("home")


# ===========================================================================
# PAGE 6 · RECOMMENDATIONS  (the heart of SMARTREC)
# ===========================================================================


def handle_interaction(customer, product_row, action, button_key, quantity=1,
                       colour="", size="", open_details_after_view=False):
    """
    Record a click permanently and let the user know.

    A "cart" action does two things: it saves the behaviour event the model
    learns from AND puts the product into the customer's real cart (cart.csv).
    A "purchase" also clears that product out of the cart.
    """
    customer_id = customer["Customer_ID"]
    product_id = product_row["Product_ID"]

    updated = data.record_interaction(
        customer_id,
        product_id,
        action,
        product_row["Product_Price"],
        quantity=quantity,
    )
    st.session_state.data_version += 1
    st.session_state.showed_loader = False

    if action == "cart":
        data.add_to_cart(customer_id, product_id, quantity, colour, size)
    elif action == "purchase":
        data.remove_from_cart(customer_id, product_id)

    messages = {
        "view": ("👁️", "You viewed"),
        "cart": ("🛒", "Added to your cart"),
        "purchase": ("💳", "You bought"),
    }
    icon, text = messages[action]

    if action == "cart":
        units = data.cart_count(customer_id)
        st.toast(
            f"{text} {product_row['Product_Name']} · {units} unit(s) in your cart"
            f" · {customer_id}",
            icon=icon,
        )
    else:
        st.toast(
            f"{text} {product_row['Product_Name']} · saved to {customer_id}",
            icon=icon,
        )
    if open_details_after_view:
        st.session_state.product_id = product_id
        st.session_state.page = "product"
    st.rerun()


def render_top_five(bundle, customer, ranked, interactions):
    """The five personalised recommendation cards."""
    top_five = model.top_recommendations(ranked, 5)

    header_left, header_right = st.columns([3, 1.4])
    with header_left:
        st.markdown(ui.section_title("Your personalised Top 5"), unsafe_allow_html=True)
    with header_right:
        st.markdown(
            '<div class="sr-chip" style="float:right;">🧠 Ranked by AI purchase probability</div>',
            unsafe_allow_html=True,
        )

    if len(top_five) == 0:
        st.info(
            "You have bought every product in the catalogue — SMARTREC has nothing "
            "left to recommend. Come back after the next product drop! 🎉"
        )
        return

    def draw_card(column, product_row):
        rank = int(product_row["Rank"])
        button_key = "top"
        with column:
            with st.container(key=f"rec_card_{rank}"):
                st.markdown(
                    ui.product_card_html(product_row, rank, interactions),
                    unsafe_allow_html=True,
                )

                columns = st.columns(3)
                product_id = product_row["Product_ID"]

                if columns[0].button(
                    "🔎 View details", key=f"view_{button_key}_{product_id}",
                    help="Mark this product as viewed and open its full details",
                    width="stretch",
                ):
                    handle_interaction(
                        customer, product_row, "view", button_key,
                        open_details_after_view=True,
                    )
                if columns[1].button(
                    "🛒 Cart", key=f"cart_{button_key}_{product_id}",
                    help="Add this product to your cart",
                    width="stretch",
                ):
                    handle_interaction(customer, product_row, "cart", button_key)
                if columns[2].button(
                    "💳 Buy", key=f"buy_{button_key}_{product_id}",
                    help="Mark this product as purchased",
                    width="stretch",
                ):
                    handle_interaction(customer, product_row, "purchase", button_key)

                with st.expander("Why this product?"):
                    reasons = model.build_reasons(product_row, customer, interactions, bundle)
                    st.markdown(ui.reason_html(reasons), unsafe_allow_html=True)

    row_one = st.columns(3)
    for column, (_, product_row) in zip(row_one, list(top_five.iterrows())[:3]):
        draw_card(column, product_row)

    row_two = st.columns(3)
    remaining = list(top_five.iterrows())[3:]
    for column, (_, product_row) in zip(row_two, remaining):
        draw_card(column, product_row)

    # the third slot of the last row explains how the model is working
    if len(remaining) < 3:
        with row_two[len(remaining)]:
            with st.container(key="rec_card_info"):
                st.markdown(ui.stat_card(
                    "TOP 5 REFRESHED FROM",
                    "Real ML",
                    "Every card above is ranked by predict_proba() — no manual picks.",
                    plain=True,
                ), unsafe_allow_html=True)
                st.markdown("")
                st.markdown(
                    f"""
                    <div class="sr-card-text" style="font-size:0.83rem;">
                      <b>Your behaviour score</b><br>
                      👁️ {int(customer.get('Views', 0))} views ·
                      🛒 {int(customer.get('Cart_Adds', 0))} cart adds ·
                      💳 {int(customer.get('Purchases', 0))} purchases<br><br>
                      The more you shop, the more the model knows about you and
                      the sharper these five cards become.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_browse_section(bundle, customer, ranked, interactions):
    """Search, filters and the full product grid."""
    st.markdown('<hr class="sr-divider"/>', unsafe_allow_html=True)
    st.markdown(ui.section_title("Browse all products", "search · filter · sort"), unsafe_allow_html=True)

    products = data.load_products().merge(
        ranked[["Product_ID", "Rank", "Purchase_Probability"]],
        on="Product_ID",
        how="left",
    )

    # -------- filter bar --------
    filter_1, filter_2, filter_3, filter_4 = st.columns([2.1, 2.2, 2.2, 1.6])

    with filter_1:
        search_text = st.text_input(
            "🔍 Search products",
            placeholder="headphones, keyboard, books…",
            key="filter_search",
            label_visibility="collapsed",
        )
    with filter_2:
        chosen_categories = st.multiselect(
            "Category filter",
            data.PRODUCT_CATEGORIES,
            default=data.PRODUCT_CATEGORIES,
            key="filter_category",
            label_visibility="collapsed",
        )
    with filter_3:
        price_limits = st.slider(
            "Price range",
            min_value=int(products["Product_Price"].min()),
            max_value=int(products["Product_Price"].max()),
            value=(
                int(products["Product_Price"].min()),
                int(products["Product_Price"].max()),
            ),
            step=100,
            key="filter_price",
            label_visibility="collapsed",
        )
    with filter_4:
        sort_choice = st.selectbox(
            "Sorting",
            ["✨ Recommended", "💰 Price: Low → High", "💎 Price: High → Low", "🏷️ Category"],
            key="filter_sort",
            label_visibility="collapsed",
        )

    # -------- apply the filters ----------
    filtered = products.copy()
    if search_text.strip():
        needle = search_text.strip().lower()
        filtered = filtered[
            filtered["Product_Name"].str.lower().str.contains(needle, na=False)
            | filtered["Product_Category"].str.lower().str.contains(needle, na=False)
        ]
    if chosen_categories:
        filtered = filtered[filtered["Product_Category"].isin(chosen_categories)]
    filtered = filtered[
        (filtered["Product_Price"] >= price_limits[0])
        & (filtered["Product_Price"] <= price_limits[1])
    ]

    # -------- sorting ----------
    if sort_choice == "✨ Recommended":
        # the AI ranking decides the order
        filtered = filtered.sort_values(
            by=["Purchase_Probability", "Rank"], ascending=[False, True], na_position="last"
        )
    elif sort_choice == "💰 Price: Low → High":
        filtered = filtered.sort_values("Product_Price")
    elif sort_choice == "💎 Price: High → Low":
        filtered = filtered.sort_values("Product_Price", ascending=False)
    else:
        filtered = filtered.sort_values(by=["Product_Category", "Product_Name"])

    # -------- show a limited number of cards, then "show more" ----------
    limit_key = "browse_limit"
    if st.session_state.get(f"{limit_key}_for") != search_text + sort_choice:
        st.session_state[limit_key] = 12
        st.session_state[f"{limit_key}_for"] = search_text + sort_choice

    shown = filtered.head(st.session_state[limit_key])
    st.markdown(
        f'<p style="font-size:0.86rem;color:var(--muted);margin:2px 0 12px 0;">'
        f"Showing <b>{len(shown)}</b> of <b>{len(filtered)}</b> products"
        + (" · sorted by AI recommendation" if sort_choice == "✨ Recommended" else f" · {sort_choice}")
        + "</p>",
        unsafe_allow_html=True,
    )

    columns_per_row = 4
    for start in range(0, len(shown), columns_per_row):
        columns = st.columns(columns_per_row)
        for column, (_, product_row) in zip(columns, list(shown.iterrows())[start:start + columns_per_row]):
            with column:
                with st.container(key=f"shop_card_{product_row['Product_ID']}"):
                    rank = product_row["Rank"]
                    rank_badge = ""
                    if pd.notna(rank):
                        rank_badge = (
                            f'<span class="sr-rank top">#{int(rank)}</span>'
                            if int(rank) == 1
                            else f'<span class="sr-rank">#{int(rank)}</span>'
                        )
                    st.markdown(
                        f"""
                        <div class="sr-cover">
                          <img src="{ui.product_image_source(product_row)}"
                               alt="{product_row['Product_Name']}" />
                        </div>
                        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px;">
                          {rank_badge}
                          <span class="sr-product-meta">{product_row['Product_Category']}</span>
                        </div>
                        <div class="sr-product-name" style="font-size:0.9rem;">{product_row['Product_Name']}</div>
                        <div class="sr-price" style="font-size:1.08rem;">{money(product_row['Product_Price'])}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    button_1, button_2 = st.columns(2)
                    if button_1.button(
                        "🔎 View details",
                        key=f"b_view_{product_row['Product_ID']}",
                        help="Mark this product as viewed and open its full details",
                        width="stretch",
                    ):
                        handle_interaction(
                            customer, product_row, "view", "browse",
                            open_details_after_view=True,
                        )
                    if button_2.button(
                        "🛒 Cart", key=f"b_cart_{product_row['Product_ID']}", width="stretch"
                    ):
                        handle_interaction(customer, product_row, "cart", "browse")

    if len(filtered) > st.session_state[limit_key]:
        if st.button(
            f"➕  Show {min(12, len(filtered) - st.session_state[limit_key])} more products",
            key="show_more",
        ):
            st.session_state[limit_key] += 12
            st.rerun()

    if len(filtered) == 0:
        st.info("No product matches these filters. Try widening the price range or clearing the search.")


def page_recommendations():
    customer = require_login(
        "Please choose 👤 Existing Customer or 🆕 New Customer to see your Top 5."
    )
    if not customer:
        return

    render_customer_chip(get_model_bundle())
    st.markdown("")

    bundle = get_model_bundle()

    # ---- the model runs on every visit, so behaviour changes show up at once
    ranked, interactions = customer_rankings(bundle, customer)

    if not st.session_state.showed_loader:
        loading_sequence()
        st.session_state.showed_loader = True

    refresh_left, refresh_right = st.columns([4, 1.3])
    with refresh_left:
        st.markdown(
            f"""
            <div class="sr-chip">
              🧠 Recommendations generated from
              <b style="color:var(--primary);">{len(ranked)}</b> products ·
              customer <b style="color:var(--primary);">{customer['Customer_ID']}</b> ·
              {len(interactions)} tracked interaction(s)
            </div>
            """,
            unsafe_allow_html=True,
        )
    with refresh_right:
        if st.button("🔄  Refresh", key="refresh_recs", width="stretch"):
            st.session_state.showed_loader = False
            st.rerun()

    st.markdown("")
    render_top_five(bundle, customer, ranked, interactions)
    render_browse_section(bundle, customer, ranked, interactions)


# ===========================================================================
# PAGE 8 · PRODUCT DETAILS  (the page every product card opens)
# ===========================================================================


def page_product():
    """The full product page: picture, price, offers, options and actions."""
    customer = require_login("Sign in to open product details and buy.")
    if not customer:
        return

    product_id = st.session_state.get("product_id")
    product = data.find_product(product_id) if product_id else None

    if product is None:
        st.markdown(ui.hero_html(), unsafe_allow_html=True)
        st.error("We could not find that product. It may have been removed from the catalogue.")
        if st.button("🛍️  Back to recommendations", key="bad_product_back", type="primary"):
            go_to("recommendations")
        return

    render_customer_chip(get_model_bundle())
    st.markdown("")

    # the model knows this product too, so we can show the real reasons here
    bundle = get_model_bundle()
    interactions = data.get_customer_interactions(customer["Customer_ID"])
    ranked, _ = customer_rankings(bundle, customer)
    product_row = ranked[ranked["Product_ID"] == product_id]
    product_row = product_row.iloc[0] if len(product_row) else None

    colours = data.split_options(product.get("Colours")) or ["Standard"]
    sizes = data.split_options(product.get("Sizes")) or ["Standard"]

    # remember the chosen options per product
    option_key = f"opt_{product_id}"
    if option_key not in st.session_state:
        st.session_state[option_key] = {"colour": colours[0], "size": sizes[0], "quantity": 1}
    chosen = st.session_state[option_key]

    gallery, information = st.columns([1, 1.5], gap="large")

    # ---------------- left: the picture ----------------
    with gallery:
        with st.container(key="product_gallery"):
            st.markdown(ui.product_gallery_html(product), unsafe_allow_html=True)

    # ---------------- right: everything else ----------------
    with information:
        st.markdown(ui.product_headline_html(product), unsafe_allow_html=True)

        st.markdown(
            f'<div class="sr-card-text" style="margin-top:12px;">{product["Description"]}</div>',
            unsafe_allow_html=True,
        )

        with st.container(key="product_options"):
            st.markdown('<div class="sr-opt-label">🎨 Colour</div>', unsafe_allow_html=True)
            for start in range(0, len(colours), 4):
                option_columns = st.columns(min(4, len(colours) - start))
                for offset, column in enumerate(option_columns):
                    colour = colours[start + offset]
                    with column:
                        if st.button(
                            f"● {colour}",
                            key=f"{option_key}_colour_{start + offset}",
                            type="primary" if colour == chosen["colour"] else "secondary",
                            help=f"Choose {colour}",
                            width="stretch",
                        ):
                            chosen["colour"] = colour
                            st.rerun()

            st.markdown(
                '<div class="sr-opt-label">🧩 Available variants</div>',
                unsafe_allow_html=True,
            )
            for start in range(0, len(sizes), 4):
                option_columns = st.columns(min(4, len(sizes) - start))
                for offset, column in enumerate(option_columns):
                    size = sizes[start + offset]
                    with column:
                        if st.button(
                            size,
                            key=f"{option_key}_size_{start + offset}",
                            type="primary" if size == chosen["size"] else "secondary",
                            help=f"Choose {size}",
                            width="stretch",
                        ):
                            chosen["size"] = size
                            st.rerun()

            new_quantity = st.number_input(
                "🔢 Quantity",
                min_value=1,
                max_value=10,
                value=int(chosen["quantity"]),
                step=1,
                key=f"{option_key}_quantity",
            )
            chosen["quantity"] = int(new_quantity)

        st.markdown("")
        buy_row = st.columns([2, 1, 1])
        if buy_row[0].button(
            "🛒  Add to cart", key="product_add_cart", type="primary", width="stretch"
        ):
            handle_interaction(
                customer, product_row if product_row is not None else product,
                "cart", "product", quantity=int(chosen["quantity"]),
                colour=chosen["colour"], size=chosen["size"],
            )
        if buy_row[1].button("💳  Buy now", key="product_buy_now", width="stretch"):
            handle_interaction(
                customer, product_row if product_row is not None else product,
                "purchase", "product", quantity=int(chosen["quantity"]),
            )
        if buy_row[2].button("❤️  View", key="product_view", width="stretch"):
            handle_interaction(
                customer, product_row if product_row is not None else product, "view", "product"
            )

        cart_units = data.cart_count(customer["Customer_ID"])
        st.markdown("")
        left, middle, right = st.columns(3)
        if left.button("🛍️  My recommendations", key="product_back_recs", width="stretch"):
            go_to("recommendations")
        if middle.button("🛒  Go to cart", key="product_go_cart", width="stretch"):
            go_to("cart")
        if right.button("🏠  Home", key="product_back_home", width="stretch"):
            go_to("home")
        st.markdown(
            f'<div class="sr-card-text" style="font-size:0.82rem;text-align:center;'
            f'margin-top:10px;">Your cart currently holds <b style="color:var(--primary);">'
            f"{cart_units}</b> unit(s) · every click on this page is saved to "
            f"<b>{customer['Customer_ID']}</b></div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # -------- 🛍️ WHERE TO BUY --------
    st.markdown(
        ui.section_title("🛍️ Where to buy", f"{product_id} · compare prices"),
        unsafe_allow_html=True,
    )
    marketplace = data.marketplace_for(product_id)
    if len(marketplace) == 0:
        st.markdown(ui.marketplace_unavailable_html(), unsafe_allow_html=True)
    else:
        st.markdown(ui.marketplace_html(marketplace, money), unsafe_allow_html=True)

    st.markdown("")

    # ---------------- lower panels ----------------
    lower_left, lower_right = st.columns([1, 1], gap="large")

    with lower_left:
        with st.container(key="product_details_left"):
            st.markdown(ui.section_title("Product highlights"), unsafe_allow_html=True)
            with st.container(key="product_highlights"):
                st.markdown(ui.product_highlights_html(product), unsafe_allow_html=True)
            st.markdown("")
            st.markdown(ui.section_title("Offers for you"), unsafe_allow_html=True)
            st.markdown(ui.product_offers_html(product), unsafe_allow_html=True)

    with lower_right:
        with st.container(key="product_details_right"):
            st.markdown(ui.section_title("Warranty, returns & payment"), unsafe_allow_html=True)
            st.markdown(ui.product_trust_html(product), unsafe_allow_html=True)

            if product_row is not None:
                st.markdown("")
                st.markdown(ui.section_title("Why SMARTREC picked this"), unsafe_allow_html=True)
                reasons = model.build_reasons(product_row, customer, interactions, bundle)
                st.markdown(ui.reason_html(reasons), unsafe_allow_html=True)

            # real numbers about this product, taken from the training data
            history = bundle["history"]
            product_history = history[history["Product_ID"] == product_id]
            st.markdown("")
            st.markdown(ui.section_title("What the history says"), unsafe_allow_html=True)
            stat_row = st.columns(3)
            if len(product_history) > 0:
                stats = [
                    ("HISTORICAL VIEWS", f"{len(product_history):,}"),
                    ("HISTORICAL CARTS", f"{int(product_history['Cart_Adds'].sum()):,}"),
                    ("PURCHASE RATE", f"{product_history['Purchased'].mean() * 100:.0f}%"),
                ]
            else:
                stats = [("HISTORICAL VIEWS", "0"), ("HISTORICAL CARTS", "0"), ("PURCHASE RATE", "0%")]
            for column, (title, value) in zip(stat_row, stats):
                with column:
                    st.markdown(ui.stat_card(title, value, plain=True), unsafe_allow_html=True)


# ===========================================================================
# PAGE 9 · MY CART
# ===========================================================================


def page_cart():
    """The customer's shopping cart, read live from cart.csv."""
    customer = require_login("Sign in with your SMR-XXXX ID to open your cart.")
    if not customer:
        return

    render_customer_chip(get_model_bundle())
    st.markdown("")

    lines = data.cart_details(customer["Customer_ID"])
    totals = data.cart_totals(customer["Customer_ID"])

    st.markdown(
        ui.section_title(
            "My cart",
            f"{totals['items']} product(s) · {totals['units']} unit(s)",
        ),
        unsafe_allow_html=True,
    )

    if len(lines) == 0:
        st.markdown(
            ui.empty_cart_html(
                "Your cart is empty",
                "Open any product and press 🛒 Add to cart — everything you add is "
                "saved to cart.csv and stays here after a restart.",
            ),
            unsafe_allow_html=True,
        )
        st.markdown("")
        left, right = st.columns(2)
        if left.button("🛍️  See my recommendations", key="cart_empty_recs", type="primary",
                       width="stretch"):
            go_to("recommendations")
        if right.button("🏠  Home", key="cart_empty_home", width="stretch"):
            go_to("home")
        return

    items_left, summary_right = st.columns([1.65, 1], gap="large")

    # ---------------- cart lines ----------------
    with items_left:
        for _, line in lines.iterrows():
            product = data.find_product(line["Product_ID"])
            if product is None:
                continue
            product_id = line["Product_ID"]
            with st.container(key=f"cart_line_{product_id}"):
                st.markdown(
                    ui.cart_line_html(line, product, money(line["Line_Total"])),
                    unsafe_allow_html=True,
                )

                controls = st.columns([1, 1, 1, 1.4])
                with controls[0]:
                    new_quantity = st.number_input(
                        "Qty",
                        min_value=0,
                        max_value=10,
                        value=int(line["Quantity"]),
                        step=1,
                        key=f"cart_qty_{product_id}",
                        label_visibility="collapsed",
                    )
                with controls[1]:
                    if st.button(
                        "💾 Update", key=f"cart_update_{product_id}", width="stretch"
                    ):
                        if new_quantity <= 0:
                            data.remove_from_cart(customer["Customer_ID"], product_id)
                            st.toast(f"Removed {product['Product_Name']}", icon="🗑️")
                        else:
                            data.update_cart_quantity(
                                customer["Customer_ID"], product_id, new_quantity
                            )
                            st.toast(
                                f"Updated {product['Product_Name']} · "
                                f"{new_quantity} unit(s)",
                                icon="💾",
                            )
                        st.rerun()
                with controls[2]:
                    if st.button(
                        "🗑️ Remove", key=f"cart_remove_{product_id}", width="stretch"
                    ):
                        data.remove_from_cart(customer["Customer_ID"], product_id)
                        st.toast(f"Removed {product['Product_Name']} from cart", icon="🗑️")
                        st.rerun()
                with controls[3]:
                    if st.button(
                        "🔎 View", key=f"cart_view_{product_id}", width="stretch"
                    ):
                        open_product(product_id)

        st.markdown("")
        small_left, small_right = st.columns(2)
        if small_left.button("🛍️  Continue shopping", key="cart_continue", width="stretch"):
            go_to("recommendations")
        if small_right.button(
            "🧹  Empty cart", key="cart_clear", width="stretch"
        ):
            data.clear_cart(customer["Customer_ID"])
            st.toast("Your cart is now empty", icon="🧹")
            st.rerun()

    # ---------------- order summary ----------------
    with summary_right:
        with st.container(key="cart_summary"):
            st.markdown(ui.stat_card(
                "ORDER SUMMARY",
                f"{totals['units']} unit(s)",
                f"{totals['items']} different product(s)",
                plain=True,
            ), unsafe_allow_html=True)
            st.markdown("")
            st.markdown(ui.cart_summary_html(totals, money), unsafe_allow_html=True)

            st.markdown("")
            if st.button(
                "💳  Place order",
                key="cart_checkout",
                type="primary",
                width="stretch",
                help="Records a real purchase for every item in your cart",
            ):
                place_order(customer, lines)

            st.markdown(
                '<div class="sr-card-text" style="font-size:0.79rem;margin-top:10px;">'
                "💡 Placing the order records a real purchase for every item, "
                "updates your total spend and removes those products from your "
                "future recommendations.</div>",
                unsafe_allow_html=True,
            )


def place_order(customer, lines):
    """Turn every cart line into a real recorded purchase."""
    customer_id = customer["Customer_ID"]
    spent = 0.0
    bought = 0
    for _, line in lines.iterrows():
        units = int(line["Quantity"])
        data.record_interaction(
            customer_id,
            line["Product_ID"],
            "purchase",
            float(line["Unit_Price"]),
            quantity=units,
        )
        spent += float(line["Line_Total"])
        bought += units

    data.clear_cart(customer_id)
    st.session_state.data_version += 1
    st.session_state.showed_loader = False
    st.toast(
        f"Order placed · {bought} unit(s) · {money(spent)} · saved to {customer_id}",
        icon="🎉",
    )
    go_to("recommendations")


# ===========================================================================
# PAGE 7 · AI INSIGHTS  (the evaluation dashboard)
# ===========================================================================


def page_insights():
    customer = current_customer()
    render_customer_chip(get_model_bundle())
    st.markdown("")

    bundle = get_model_bundle()
    metrics = bundle["metrics"]
    report = bundle["cleaning_report"]

    st.markdown(
        """
        <div class="sr-fade-up">
          <span class="sr-eyebrow">📊 AI INSIGHTS</span>
          <div class="sr-hero-title" style="font-size:2.3rem;">Inside the SMARTREC model</div>
          <p class="sr-hero-sub">This page is for the project demonstration. Every
          number below is calculated by the trained model — nothing is typed in by hand.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ---------------- model performance ----------------
    st.markdown(ui.section_title("Model performance", "measured on unseen test data"), unsafe_allow_html=True)
    cards = st.columns(5)
    metric_cards = [
        ("MODEL ACCURACY", f"{metrics['accuracy'] * 100:.1f}%", "correct predictions"),
        ("PRECISION", f"{metrics['precision'] * 100:.1f}%", "predicted buyers that were real"),
        ("RECALL", f"{metrics['recall'] * 100:.1f}%", "real buyers the model caught"),
        ("F1 SCORE", f"{metrics['f1'] * 100:.1f}%", "balance of precision and recall"),
        ("ROC-AUC", f"{metrics['roc_auc']:.3f}", "overall ranking quality"),
    ]
    for column, (title, value, subtitle) in zip(cards, metric_cards):
        with column:
            st.markdown(ui.stat_card(title, value, subtitle), unsafe_allow_html=True)

    st.markdown("")
    info_1, info_2, info_3 = st.columns(3)
    with info_1:
        st.markdown(
            f'<div class="sr-chip">🧪 Training rows: <b>{metrics["train_rows"]:,}</b></div>',
            unsafe_allow_html=True,
        )
    with info_2:
        st.markdown(
            f'<div class="sr-chip">🧪 Test rows: <b>{metrics["test_rows"]:,}</b></div>',
            unsafe_allow_html=True,
        )
    with info_3:
        st.markdown(
            f'<div class="sr-chip">⏱️ Trained: <b>{bundle["trained_on"]}</b></div>',
            unsafe_allow_html=True,
        )

    # ---------------- confusion matrix + roc ----------------
    st.markdown("")
    matrix_column, roc_column = st.columns(2)

    with matrix_column:
        st.markdown(ui.section_title("Confusion matrix", "test set"), unsafe_allow_html=True)
        matrix = bundle["confusion_matrix"]
        heatmap = go.Figure(
            data=go.Heatmap(
                z=matrix,
                x=["Predicted: No", "Predicted: Yes"],
                y=["Actual: No", "Actual: Yes"],
                text=[[str(matrix[0][0]), str(matrix[0][1])], [str(matrix[1][0]), str(matrix[1][1])]],
                texttemplate="%{text}",
                textfont=dict(size=20),
                colorscale=[
                    [0, "#EDE9FE"],
                    [0.5, "#A78BFA"],
                    [1, "#4F46E5"],
                ],
                hovertemplate="%{y} / %{x}: <b>%{text}</b><extra></extra>",
            )
        )
        heatmap.update_layout(title=None)
        chart_layout(heatmap, height=300)
        st.plotly_chart(heatmap, width="stretch", config={"displayModeBar": False})

        st.markdown(
            f"""
            <div class="sr-card-text" style="font-size:0.84rem;">
              ✅ <b>{matrix[1][1]:,}</b> buyers correctly found ·
              ❌ <b>{matrix[1][0]:,}</b> buyers missed ·
              ⚠️ <b>{matrix[0][1]:,}</b> non-buyers flagged ·
              ✔️ <b>{matrix[0][0]:,}</b> non-buyers correctly ignored
            </div>
            """,
            unsafe_allow_html=True,
        )

    with roc_column:
        st.markdown(ui.section_title("ROC curve", "how well the model separates buyers"), unsafe_allow_html=True)
        false_positive_rate, true_positive_rate = bundle["roc_curve"]
        roc_figure = go.Figure()
        roc_figure.add_trace(go.Scatter(
            x=false_positive_rate, y=true_positive_rate, mode="lines",
            line=dict(color="#4F46E5", width=3),
            fill="tozeroy", fillcolor="rgba(124, 58, 237, 0.14)",
            name="SMARTREC model",
        ))
        roc_figure.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines",
            line=dict(color="#94A3B8", width=2, dash="dash"),
            name="Random guess",
        ))
        roc_figure.update_layout(
            title=None,
            xaxis_title="False positive rate",
            yaxis_title="True positive rate",
        )
        chart_layout(roc_figure, height=300)
        st.plotly_chart(roc_figure, width="stretch", config={"displayModeBar": False})

    # ---------------- feature importance ----------------
    st.markdown("")
    st.markdown(
        ui.section_title(
            "Feature importance",
            "logistic regression coefficients (higher = stronger influence)",
        ),
        unsafe_allow_html=True,
    )
    importance = bundle["feature_importance"].head(14).iloc[::-1]
    importance_figure = go.Figure(
        go.Bar(
            x=importance["Coefficient"],
            y=importance["Feature"],
            orientation="h",
            marker=dict(
                color=[
                    "#4F46E5" if value >= 0 else "#94A3B8" for value in importance["Coefficient"]
                ],
                line=dict(width=0),
            ),
            text=[f"{value:+.2f}" for value in importance["Coefficient"]],
            textposition="outside",
        )
    )
    importance_figure.update_layout(xaxis_title="Coefficient (scaled features)")
    chart_layout(importance_figure, height=430)
    st.plotly_chart(importance_figure, width="stretch", config={"displayModeBar": False})
    st.markdown(
        """
        <div class="sr-card-text" style="font-size:0.85rem;">
          A <b>positive</b> bar means "more of this feature → more likely to buy".
          These are the model's own weights — computed during training, not written by hand.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- purchase probabilities ----------------
    st.markdown('<hr class="sr-divider"/>', unsafe_allow_html=True)
    st.markdown(
        ui.section_title("Purchase probability", "the numbers the customer never sees on the cards"),
        unsafe_allow_html=True,
    )

    if customer:
        ranked, _ = customer_rankings(bundle, customer)
        top_five = model.top_recommendations(ranked, 5)

        probability_table = pd.DataFrame({
            "Rank": top_five["Rank"].astype(int),
            "Product": top_five["Product_Name"],
            "Category": top_five["Product_Category"],
            "Price": top_five["Product_Price"].map(money),
            "Purchase probability": (top_five["Purchase_Probability"] * 100).round(1),
        })

        probability_figure = go.Figure(
            go.Bar(
                x=probability_table["Purchase probability"],
                y=["#" + str(value) for value in probability_table["Rank"]],
                orientation="h",
                marker=dict(
                    color=["#4F46E5", "#6366F1", "#7C3AED", "#8B5CF6", "#A78BFA"][:len(top_five)],
                    line=dict(width=0),
                ),
                text=[f"{value:.1f}%" for value in probability_table["Purchase probability"]],
                textposition="outside",
                customdata=probability_table["Product"],
                hovertemplate="%{customdata}<br>Purchase probability <b>%{x:.1f}%</b><extra></extra>",
            )
        )
        probability_figure.update_layout(
            xaxis_title="Purchase probability (%)",
            yaxis_title="Rank",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        chart_layout(probability_figure, height=300)
        probability_figure.update_layout(showlegend=False)

        probability_column, note_column = st.columns([1.35, 1])
        with probability_column:
            st.plotly_chart(probability_figure, width="stretch", config={"displayModeBar": False})
        with note_column:
            st.dataframe(
                probability_table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Purchase probability": st.column_config.ProgressColumn(
                        "Purchase probability",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%",
                    ),
                },
            )
            st.markdown(
                f"""
                <div class="sr-card-text" style="font-size:0.84rem;">
                  These are the real <b>model.predict_proba()</b> outputs for
                  <b>{customer['Customer_ID']}</b>. They are hidden on the
                  recommendation cards so the shopping screen stays clean — but
                  they are the reason these five products are in this exact order.
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "Log in with a SMARTREC Customer ID to see the live purchase probabilities "
            "that were calculated for your own Top 5."
        )

    # ---------------- dataset + cleaning ----------------
    st.markdown('<hr class="sr-divider"/>', unsafe_allow_html=True)
    st.markdown(ui.section_title("Dataset & preprocessing", "the data the model learned from"), unsafe_allow_html=True)

    dataset_cards = st.columns(4)
    dataset_stats = [
        ("ROWS LOADED", f"{report['rows_loaded']:,}", "from history.csv"),
        ("DUPLICATES REMOVED", f"{report['duplicate_rows_removed']:,}", "same customer + product merged"),
        ("MISSING VALUES FIXED", f"{report['missing_before']:,}", f"→ {report['missing_after']} left"),
        ("CLEAN ROWS USED", f"{report['rows_after']:,}", f"{report['customers']:,} historical customers"),
    ]
    for column, (title, value, subtitle) in zip(dataset_cards, dataset_stats):
        with column:
            st.markdown(ui.stat_card(title, value, subtitle, plain=True), unsafe_allow_html=True)

    st.markdown("")
    category_column, class_column = st.columns([1.3, 1])

    with category_column:
        history = bundle["history"]
        category_chart = (
            history.groupby("Product_Category")
            .agg(Views=("Views", "sum"), Purchases=("Purchased", "sum"))
            .reset_index()
            .melt(id_vars="Product_Category", var_name="Metric", value_name="Total")
        )
        bar_figure = px.bar(
            category_chart,
            x="Product_Category",
            y="Total",
            color="Metric",
            barmode="group",
            color_discrete_map={"Views": "#A78BFA", "Purchases": "#4F46E5"},
        )
        bar_figure.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        chart_layout(bar_figure, height=320)
        st.plotly_chart(bar_figure, width="stretch", config={"displayModeBar": False})

    with class_column:
        history = bundle["history"]
        bought = int(history["Purchased"].sum())
        not_bought = int(len(history) - bought)
        pie_figure = go.Figure(
            go.Pie(
                labels=["Purchased (1)", "Not purchased (0)"],
                values=[bought, not_bought],
                hole=0.62,
                marker=dict(colors=["#4F46E5", "#C7D2FE"], line=dict(color="#FFFFFF", width=3)),
                textinfo="percent",
            )
        )
        pie_figure.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.06))
        chart_layout(pie_figure, height=320)
        pie_figure.update_layout(showlegend=True)
        st.plotly_chart(pie_figure, width="stretch", config={"displayModeBar": False})
        st.markdown(
            f'<div class="sr-chip">Target <b>Purchased</b> · {bought:,} positive vs '
            f"{not_bought:,} negative rows</div>",
            unsafe_allow_html=True,
        )

    # ---------------- features used ----------------
    with st.expander(
        f"🧠 The {len(model.ALL_FEATURES)} features SMARTREC computes "
        f"({len(model.NUMERIC_FEATURES)} numeric + 1 categorical) for every customer-product pair"
    ):
        st.markdown(
            f"""
            <div class="sr-card-text">
              Each product is described by these numbers before it reaches the model:
            </div>
            """,
            unsafe_allow_html=True,
        )
        feature_table = pd.DataFrame({
            "Feature": model.ALL_FEATURES,
            "Type": ["number" if name in model.NUMERIC_FEATURES else "category"
                     for name in model.ALL_FEATURES],
        })
        st.dataframe(feature_table, width="stretch", hide_index=True, height=430)
        st.markdown(
            """
            <div class="sr-card-text" style="font-size:0.85rem;">
              <b>Why this matters:</b> the same feature builder is used for training
              and for real customers, so the model always receives columns in the
              same format. That is what keeps the predictions trustworthy.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ===========================================================================
# PAGE 8 · HOW IT WORKS
# ===========================================================================


def page_how():
    st.markdown(
        """
        <div class="sr-fade-up">
          <span class="sr-eyebrow">🧠 HOW IT WORKS</span>
          <div class="sr-hero-title" style="font-size:2.4rem;">From a click to a Top 5</div>
          <p class="sr-hero-sub">SMARTREC follows one clear path. Here is every step,
          explained in plain language.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    for index, (icon, title, description) in enumerate(ui.PIPELINE_STEPS, start=1):
        st.markdown(
            ui.pipeline_step_html(index, icon, title, description),
            unsafe_allow_html=True,
        )
        if index < len(ui.PIPELINE_STEPS):
            st.markdown('<div class="sr-arrow">↓</div>', unsafe_allow_html=True)

    st.markdown('<hr class="sr-divider"/>', unsafe_allow_html=True)
    st.markdown(ui.section_title("Why Logistic Regression?"), unsafe_allow_html=True)

    reasons = st.columns(2)
    with reasons[0]:
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">📈 It outputs a real probability</div>
              <div class="sr-card-text">
                <code>purchase_proba()</code> returns a number between 0 and 1.
                That is exactly what we need to rank products — 0.82 means
                "an 82% chance this customer buys it".
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">🪟 It is easy to explain</div>
              <div class="sr-card-text">
                Every feature gets one weight. The Feature Importance chart on the
                AI Insights page shows those weights — perfect for a viva.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with reasons[1]:
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">⚡ It is fast and light</div>
              <div class="sr-card-text">
                The whole model trains in about a second on a normal laptop —
                no GPU and no paid service required.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">🌱 It learns over time</div>
              <div class="sr-card-text">
                Each view, cart add and purchase is written to
                <b>interactions.csv</b>. The next visit builds new features from
                that history, so the same model gives sharper results.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    bundle = get_model_bundle()
    metrics = bundle["metrics"]
    st.markdown(
        f"""
        <div class="sr-card">
          <div class="sr-card-title">📉 The short version</div>
          <div class="sr-card-text">
            The model was trained on <b>{metrics['train_rows']:,}</b> historical
            customer-product rows and tested on <b>{metrics['test_rows']:,}</b> rows it
            had never seen. It reached an accuracy of
            <b>{metrics['accuracy'] * 100:.1f}%</b> and an ROC-AUC of
            <b>{metrics['roc_auc']:.3f}</b>. Open 📊 AI Insights to see the full report.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    if st.button("📊  See the real model numbers", key="how_insights", type="primary"):
        go_to("insights")


# ===========================================================================
# PAGE 9 · ABOUT
# ===========================================================================


def page_about():
    st.markdown(
        """
        <div style="text-align:center;">
          <div class="sr-logo" style="justify-content:center;font-size:2.1rem;">
            <span class="mark">✦</span><span class="brand">SMARTREC</span>
          </div>
          <div class="sr-hero-title" style="font-size:2.1rem;">AI-Powered Product
          Recommendation System</div>
          <p class="sr-hero-sub" style="margin:0 auto;">Your shopping, made smarter.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">💡 What is SMARTREC?</div>
              <div class="sr-card-text">
                SMARTREC is an AI-powered recommendation engine for an online
                shopping platform. It studies historical customer behaviour, learns
                from it with a machine learning model, and then predicts how likely
                each customer is to buy each product.
              </div>
              <div class="sr-reason">✓ Real trained ML model — not hardcoded results</div>
              <div class="sr-reason">✓ Permanent customer profiles with unique SMR-XXXX IDs</div>
              <div class="sr-reason">✓ Behaviour tracking: views, cart adds, purchases</div>
              <div class="sr-reason">✓ Personalised Top 5 that improves with every visit</div>
              <div class="sr-reason">✓ CSV storage — easy to open and understand</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="sr-card">
              <div class="sr-card-title">🛠️ Technologies used</div>
              <div class="sr-card-text">Everything runs locally. No paid API.</div>
              <div style="height:8px"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tech = st.columns(2)
        technologies = [
            ("🐍", "Python", "Core language"),
            ("📊", "Pandas", "Data handling"),
            ("🧠", "Scikit-learn", "ML model"),
            ("🎨", "Streamlit", "Web interface"),
            ("📈", "Plotly", "Charts"),
            ("🔢", "NumPy", "Numbers"),
        ]
        for column, (icon, name, role) in zip(tech, technologies[:4]):
            with column:
                st.markdown(
                    f'<div class="sr-chip" style="width:100%;justify-content:center;">'
                    f"{icon} <b>{name}</b></div>",
                    unsafe_allow_html=True,
                )
        tech_two = st.columns(2)
        for column, (icon, name, role) in zip(tech_two, technologies[4:]):
            with column:
                st.markdown(
                    f'<div class="sr-chip" style="width:100%;justify-content:center;">'
                    f"{icon} <b>{name}</b></div>",
                    unsafe_allow_html=True,
                )

    st.markdown("")
    st.markdown(ui.section_title("Team member"), unsafe_allow_html=True)
    st.markdown(
        ui.team_card_html(
            name="Deekshita Kokkanti",
            role="Solo Developer · SMARTREC",
            initials="DK",
            about=(
                "Designed, built and documented SMARTREC end to end — the product "
                "catalogue and dataset generation, the Logistic Regression model, "
                "the customer ID and interaction storage, and every screen of the "
                "web interface."
            ),
            tasks=[
                "🎯 Data &amp; dataset generation",
                "🧠 Feature engineering &amp; ML model",
                "🗄️ CSV storage &amp; customer IDs",
                "🎨 Streamlit UI &amp; design",
                "🧪 Testing &amp; documentation",
            ],
        ),
        unsafe_allow_html=True,
    )

    st.markdown("")
    details = st.columns(2)
    placeholders = [
        ("🏫 COLLEGE", "VIT-CHENNAI"),
        ("🎓 DEPARTMENT", "Computer Science Core"),
    ]
    for column, (title, value) in zip(details, placeholders):
        with column:
            st.markdown(
                f'<div class="sr-stat"><div class="k">{title}</div>'
                f'<div class="v plain" style="font-size:1.02rem;">{value}</div></div>',
                unsafe_allow_html=True,
            )


# ===========================================================================
# PAGE 8 · ADMIN LOGIN  (separate from the customer login)
# ===========================================================================


def page_admin_login():
    """A completely separate login screen, only for the SMARTREC admin."""
    left, right = st.columns([1, 1.15])

    with left:
        with st.container(key="admin_gate"):
            st.markdown(ui.admin_login_html(), unsafe_allow_html=True)
            st.markdown("")

            username = st.text_input(
                "Admin username",
                placeholder="admin",
                max_chars=40,
                key="admin_username",
            )
            password = st.text_input(
                "Admin password",
                type="password",
                max_chars=60,
                key="admin_password",
            )

            if st.button("🔓  Log in as Admin", key="admin_login_go",
                         type="primary", width="stretch"):
                if data.check_admin_login(username, password):
                    st.session_state.admin_logged_in = True
                    st.session_state.showed_loader = False
                    st.session_state.data_version += 1
                    st.toast("Admin logged in ⚙️", icon="✅")
                    go_to("admin")
                else:
                    st.error("Wrong admin username or password. Please try again.")

            st.markdown(
                '<p style="font-size:0.78rem;color:var(--muted);margin-top:6px;">'
                "This screen is only for the SMARTREC admin. Customers do not "
                "need an account here.</p>",
                unsafe_allow_html=True,
            )

    with right:
        with st.container(key="admin_hero"):
            st.markdown(
                """
                <span class="sr-eyebrow">🛠️ WHAT THE ADMIN CAN DO</span>
                <div class="sr-hero-title" style="font-size:1.5rem;">
                    Manage products and customers
                </div>
                <p class="sr-hero-sub">
                  The admin can manage the product catalogue and remove customer
                  accounts. Customers cannot access these controls.
                </p>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("")
            steps = [
                ("➕", "Add a product", "Type the name, category, price, image "
                                        "address and description. SMARTREC creates "
                                        "the Product ID for you."),
                ("✏️", "Edit a product", "Change any product's details. The Product "
                                        "ID stays the same, so no customer history "
                                        "is lost."),
                ("🗑️", "Delete a customer", "Remove a customer profile, cart and "
                                           "interaction history. Deleted customer "
                                           "IDs are never reused."),
                ("💾", "Saved permanently", "Every change is written to "
                                           "products.csv and survives a restart."),
                ("🤖", "Ready for the model", "A new product joins the catalogue "
                                              "straight away, so the recommendation "
                                              "system can score it."),
            ]
            for icon, title, text in steps:
                st.markdown(
                    f'<div class="sr-reason">{icon} <b>{title}</b> — {text}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("")
    if st.button("←  Back to Home", key="admin_login_back"):
        go_to("home")


# ===========================================================================
# PAGE 9 · ADMIN PANEL  (products + customer management)
# ===========================================================================


def require_admin():
    """
    Return True only when the logged-in person really is the admin.

    Every admin page calls this first, so a customer can never reach the
    product controls - not by typing anything, not by clicking a stale button.
    """
    if st.session_state.get("admin_logged_in"):
        return True

    st.warning("Please log in as the admin to open the Admin Panel.")
    if st.button("🔓  Go to Admin Login", key="admin_gate_go"):
        go_to("admin_login")
    return False


def admin_product_table():
    """The searchable product table shown under the Add / Edit forms."""
    products = data.load_products()

    st.markdown("")
    with st.container(key="admin_summary"):
        head_left, head_right = st.columns([2.4, 1])
        with head_left:
            st.markdown(
                '<div class="sr-card-title">📋 Product catalogue</div>',
                unsafe_allow_html=True,
            )
        with head_right:
            admin_added = int(
                products["Product_ID"].astype(str).str.startswith("PRD-").sum()
            )
            st.markdown(
                f'<div style="text-align:right;font-size:0.78rem;color:var(--muted);'
                f'font-weight:700;">Showing {len(products)} product(s) · '
                f"{admin_added} added by admin</div>",
                unsafe_allow_html=True,
            )

        filter_row = st.columns([1.6, 1])
        with filter_row[0]:
            search_text = st.text_input(
                "Search products",
                placeholder="Search by name or Product ID",
                key="admin_search",
            )
        with filter_row[1]:
            filter_choice = st.selectbox(
                "Category",
                ["All categories"] + list(data.PRODUCT_CATEGORIES),
                key="admin_filter",
            )

        st.markdown(ui.admin_table_head_html(), unsafe_allow_html=True)

        # the rows the admin should see after searching / filtering
        shown = products
        if search_text:
            needle = search_text.lower()
            shown = shown[
                shown["Product_Name"].astype(str).str.lower().str.contains(needle)
                | shown["Product_ID"].astype(str).str.lower().str.contains(needle)
            ]
        if filter_choice != "All categories":
            shown = shown[shown["Product_Category"] == filter_choice]

        total = len(shown)
        shown = shown.head(TABLE_LIMIT)
        chosen_id = st.session_state.get("admin_edit_id")

        # one real Streamlit row per product, so each row has its own Edit button
        for _, product in shown.iterrows():
            product_id = str(product["Product_ID"])
            cells = ui.admin_row_cells(product, money)

            row_key = "admin_row_now_" if product_id == chosen_id else "admin_row_"
            with st.container(key=f"{row_key}{product_id}"):
                id_col, name_col, cat_col, price_col, edit_col = st.columns(
                    [1.05, 3.2, 1.05, 1.0, 0.9]
                )
                with id_col:
                    st.markdown(cells[0], unsafe_allow_html=True)
                with name_col:
                    st.markdown(cells[1], unsafe_allow_html=True)
                with cat_col:
                    st.markdown(cells[2], unsafe_allow_html=True)
                with price_col:
                    st.markdown(cells[3], unsafe_allow_html=True)
                with edit_col:
                    if st.button(
                        "✏️  Edit",
                        key=f"admin_edit_{product_id}",
                        width="stretch",
                        help=f"Edit {product_id}",
                    ):
                        st.session_state.admin_edit_id = product_id
                        # a new version makes the edit form follow this row
                        st.session_state.admin_edit_version = (
                            st.session_state.get("admin_edit_version", 0) + 1
                        )
                        # jump to the "Edit Product" tab automatically (the tab
                        # container reads this next run and selects it)
                        st.session_state.admin_wanted_tab = "✏️  Edit Product"
                        # ... and scroll the page up to the form on that run
                        st.session_state.admin_scroll_edit = True
                        st.rerun()

        if total == 0:
            st.markdown(ui.admin_empty_html(), unsafe_allow_html=True)
        elif total > TABLE_LIMIT:
            st.markdown(
                ui.admin_note_html(
                    f"Showing the first {TABLE_LIMIT} of {total} matching products. "
                    "Use the search box to narrow it down."
                ),
                unsafe_allow_html=True,
            )


def admin_add_form():
    """The ➕ Add Product form."""
    # A "version" number is put into every box's key. After a successful save
    # we bump the version, so the next run draws brand new empty boxes. This is
    # the simple Streamlit way of clearing a form without touching any other
    # session data.
    version = st.session_state.get("admin_add_version", 0)

    with st.form(key="admin_add_form", clear_on_submit=False):
        st.markdown(
            '<div class="sr-card-title">➕ Add a new product</div>'
            '<div class="sr-card-text" style="margin-bottom:14px;">'
            "Fill these in and SMARTREC will create the Product ID and save it "
            "to <b>products.csv</b> straight away.</div>",
            unsafe_allow_html=True,
        )

        row_one = st.columns(2)
        with row_one[0]:
            name = st.text_input("Product name", placeholder="Gaming Mouse",
                                 max_chars=80, key=f"admin_add_name_{version}")
        with row_one[1]:
            category = st.selectbox(
                "Category", list(data.PRODUCT_CATEGORIES),
                key=f"admin_add_category_{version}",
            )

        row_two = st.columns(2)
        with row_two[0]:
            price = st.text_input("Price (₹)", placeholder="2499",
                                  max_chars=12, key=f"admin_add_price_{version}")
        with row_two[1]:
            image = st.text_input(
                "Product image URL (optional)",
                placeholder="https://example.com/mouse.jpg",
                max_chars=500,
                key=f"admin_add_image_{version}",
            )
            st.markdown(
                '<p style="font-size:0.75rem;color:var(--muted);margin-top:-10px;">'
                "Leave it empty and SMARTREC draws a picture for you.</p>",
                unsafe_allow_html=True,
            )

        description = st.text_area(
            "Description",
            placeholder="A light and fast gaming mouse with 6 buttons.",
            max_chars=1000,
            height=110,
            key=f"admin_add_description_{version}",
        )

        submitted = st.form_submit_button(
            "➕  Add Product", type="primary", key="admin_add_submit"
        )

    if submitted:
        new_id, error = data.add_product(name, category, price, image, description)
        if error:
            st.markdown(ui.admin_result_html("bad", error), unsafe_allow_html=True)
        else:
            # remember the message, bump the version, then redraw so the boxes
            # come back empty and ready for the next product
            st.session_state.admin_flash = (
                "ok",
                f"Saved! <b>{new_id}</b> is now in the catalogue and the "
                "recommendation system can score it.",
            )
            st.session_state.admin_add_version = version + 1
            st.session_state.data_version += 1
            st.rerun()


def admin_customer_management():
    """Allow an authenticated admin to remove a customer and their stored data."""
    customers = data.load_customers()
    st.markdown(
        '<div class="sr-card-title">👥 Customer accounts</div>'
        '<div class="sr-card-text">Deleting an account permanently removes its '
        'profile, cart and interaction history. The customer ID remains reserved '
        'so it cannot be assigned to someone else.</div>',
        unsafe_allow_html=True,
    )
    if len(customers) == 0:
        st.info("There are no customer accounts to manage.")
        return

    customer_ids = customers["Customer_ID"].astype(str).tolist()
    customer_names = dict(zip(customer_ids, customers["Name"].astype(str)))
    selected_id = st.selectbox(
        "Select a customer",
        customer_ids,
        format_func=lambda value: f"{value} · {customer_names[value]}",
        key="admin_customer_select",
    )

    if st.button(
        "🗑️  Delete customer",
        key="admin_customer_delete_request",
        type="secondary",
    ):
        st.session_state.admin_delete_customer_id = selected_id

    pending_id = st.session_state.get("admin_delete_customer_id")
    if pending_id:
        pending_customer = data.find_customer(pending_id)
        if pending_customer is None:
            st.session_state.pop("admin_delete_customer_id", None)
            st.warning("That customer account no longer exists. Refresh the selection.")
            return

        st.warning(
            f"Delete {pending_customer['Name']} ({pending_id}) and permanently "
            "remove their profile, cart and interaction history?"
        )
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button(
            "Yes, permanently delete",
            key="admin_customer_delete_confirm",
            type="primary",
        ):
            if data.delete_customer(pending_id):
                if str(st.session_state.get("customer_id", "")).strip().upper() == (
                    str(pending_id).strip().upper()
                ):
                    st.session_state.customer_id = None
                st.session_state.data_version += 1
                st.session_state.showed_loader = False
                st.session_state.pop("admin_delete_customer_id", None)
                st.toast(f"Deleted customer {pending_id}", icon="🗑️")
                st.rerun()
            st.error("The customer account could not be found; nothing was deleted.")
        if cancel_col.button("Cancel", key="admin_customer_delete_cancel"):
            st.session_state.pop("admin_delete_customer_id", None)
            st.rerun()


def admin_edit_form():
    """The ✏️ Edit Product form. The Product ID can never be changed."""
    # an invisible target the row-edit auto scroll jumps to; see
    # admin_scroll_to_edit_form() below. It must exist before the form so the
    # scroll lands just above the boxes the admin is about to touch.
    st.markdown('<div id="admin_edit_anchor"></div>', unsafe_allow_html=True)

    products = data.load_products()

    options = list(products["Product_ID"])

    # The version number is part of every key in this form. It is bumped whenever
    # the product changes or a save succeeds, so the boxes are always redrawn
    # from what products.csv really holds right now.
    version = st.session_state.get("admin_edit_version", 0)

    chosen_id = st.session_state.get("admin_edit_id")
    if chosen_id not in options:
        chosen_id = options[0]
        st.session_state.admin_edit_id = chosen_id

    selected_id = st.selectbox(
        "Select a product to edit",
        options,
        index=options.index(chosen_id),
        key=f"admin_edit_select_{version}",
        format_func=lambda value: (
            f"{value} · {products[products['Product_ID'] == value].iloc[0]['Product_Name']}"
        ),
    )

    if selected_id != chosen_id:
        # the admin picked a different product from the drop-down
        st.session_state.admin_edit_id = selected_id
        st.session_state.admin_edit_version = version + 1
        st.rerun()

    chosen_id = selected_id
    current = products[products["Product_ID"] == chosen_id].iloc[0]

    box_key = f"{chosen_id}_{version}"

    st.markdown(
        f'<div class="sr-admin-result ok" style="margin-top:4px;">'
        f"🔒 Product ID <b>{chosen_id}</b> is locked. It is the key the "
        "recommendation system and every customer interaction use, so it can "
        "never be changed.</div>",
        unsafe_allow_html=True,
    )

    with st.form(key="admin_edit_form", clear_on_submit=False):
        edit_row = st.columns([2.2, 1])
        with edit_row[0]:
            name = st.text_input(
                "Product name",
                value=str(current["Product_Name"]),
                max_chars=80,
                key=f"admin_edit_name_{box_key}",
            )
        with edit_row[1]:
            category_options = list(data.PRODUCT_CATEGORIES)
            current_category = str(current["Product_Category"])
            if current_category not in category_options:
                category_options.append(current_category)
            category = st.selectbox(
                "Category",
                category_options,
                index=category_options.index(current_category),
                key=f"admin_edit_category_{box_key}",
            )

        price_row = st.columns(2)
        with price_row[0]:
            price = st.text_input(
                "Price (₹)",
                value=price_text(current["Product_Price"]),
                max_chars=12,
                key=f"admin_edit_price_{box_key}",
            )
        with price_row[1]:
            image_value = str(current["Product_Image"] or "")
            is_url = image_value.lower().startswith(("http://", "https://"))
            image = st.text_input(
                "Product image URL",
                value=image_value if is_url else "",
                placeholder="https://example.com/mouse.jpg",
                max_chars=500,
                key=f"admin_edit_image_{box_key}",
            )

        description = st.text_area(
            "Description",
            value=str(current["Description"] or ""),
            max_chars=1000,
            height=110,
            key=f"admin_edit_description_{box_key}",
        )

        st.markdown(
            '<p style="font-size:0.76rem;color:var(--muted);margin-top:-6px;">'
            "Saving keeps this Product ID, so all customer interaction history "
            "for it stays exactly as it is.</p>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            "💾  Save changes", type="primary", key="admin_edit_submit"
        )

    if submitted:
        ok, message = data.update_product(
            chosen_id, name, category, price, image, description
        )
        if not ok:
            st.markdown(ui.admin_result_html("bad", message), unsafe_allow_html=True)
        else:
            # remember the message, bump the version, then redraw so the boxes
            # show exactly what is now stored in products.csv
            st.session_state.admin_flash = (
                "ok",
                f"Saved! <b>{chosen_id}</b> is updated in products.csv and the "
                "change is permanent.",
            )
            st.session_state.admin_edit_version = version + 1
            st.session_state.data_version += 1
            st.rerun()


def admin_marketplace_form():
    """
    The 🏷️ Marketplace tab: pick a product, delete any of its listings, and
    add or update one platform at a time (price + product URL). The change is
    written permanently to marketplace_prices.csv.
    """
    products = data.load_products()
    options = list(products["Product_ID"])

    version = st.session_state.get("admin_market_version", 0)
    chosen_id = st.session_state.get("admin_market_id")
    if chosen_id not in options:
        chosen_id = options[0]
        st.session_state.admin_market_id = chosen_id

    selected_id = st.selectbox(
        "Product",
        options,
        index=options.index(chosen_id),
        key=f"admin_market_product_{version}",
        format_func=lambda value: (
            f"{value} · {products[products['Product_ID'] == value].iloc[0]['Product_Name']}"
        ),
    )

    if selected_id != chosen_id:
        st.session_state.admin_market_id = selected_id
        st.session_state.admin_market_version = version + 1
        st.rerun()

    chosen_id = selected_id
    listings = data.marketplace_for(chosen_id)

    st.markdown(
        ui.section_title(
            f"Current listings for {chosen_id}",
            f"{len(listings)} platform(s)",
        ),
        unsafe_allow_html=True,
    )

    if len(listings) == 0:
        st.markdown(
            ui.admin_note_html(
                "No marketplace listings yet for this product. Add the first "
                "one below, or it will show as 'currently unavailable'."
            ),
            unsafe_allow_html=True,
        )
    else:
        # one real row per existing listing, with its own Delete button
        for _, listing in listings.iterrows():
            platform = str(listing["Platform"])
            with st.container(key=f"admin_mp_row_{chosen_id}_{platform}"):
                name_col, price_col, url_col, del_col = st.columns([1.2, 1, 2.8, 0.8])
                with name_col:
                    st.markdown(
                        f'<div class="sr-admin-cat" style="font-weight:800;color:var(--text);">'
                        f"{platform}</div>",
                        unsafe_allow_html=True,
                    )
                with price_col:
                    st.markdown(
                        f'<div class="sr-admin-price">{money(float(listing["Price"]))}</div>',
                        unsafe_allow_html=True,
                    )
                with url_col:
                    st.markdown(
                        f'<div style="font-size:0.76rem;color:var(--muted);overflow:hidden;'
                        f'text-overflow:ellipsis;white-space:nowrap;">'
                        f'🔗 <a href="{listing["Product_URL"]}" target="_blank" '
                        f'rel="noopener" style="color:var(--accent);">'
                        f"{listing['Product_URL'][:44]}</a></div>",
                        unsafe_allow_html=True,
                    )
                with del_col:
                    if st.button(
                        "🗑",
                        key=f"admin_mp_del_{chosen_id}_{platform}",
                        width="stretch",
                        help=f"Remove the {platform} listing for {chosen_id}",
                    ):
                        ok, message = data.remove_marketplace(chosen_id, platform)
                        st.session_state.admin_flash = ("ok" if ok else "bad", message)
                        st.session_state.data_version += 1
                        st.rerun()

    st.markdown("")
    st.markdown(
        ui.section_title("Add or update a listing", "one row per product + platform"),
        unsafe_allow_html=True,
    )

    # which platforms already have a listing for this product
    listed = set(listings["Platform"].astype(str))
    status = "     ".join(
        (
            f"<b style='color:var(--success)'>✓ {platform}</b>"
            if platform in listed
            else f"<b style='color:var(--muted)'>✗ {platform}</b>"
        )
        for platform in data.MARKETPLACE_PLATFORMS
    )
    st.markdown(
        f'<div style="font-size:0.78rem;color:var(--muted);margin:2px 0 10px;">{status}</div>',
        unsafe_allow_html=True,
    )

    # if the platform already has a listing, its price and URL are pre-filled
    # so the form is used for editing as well as adding
    platform_pick = st.selectbox(
        "Platform",
        data.MARKETPLACE_PLATFORMS,
        key="admin_market_platform_pick",
    )
    existing = listings[listings["Platform"] == platform_pick]
    default_price = price_text(float(existing.iloc[0]["Price"])) if len(existing) else ""
    default_url = (
        str(existing.iloc[0]["Product_URL"]) if len(existing) else ""
    )

    with st.form(key="admin_market_form", clear_on_submit=False):
        price = st.text_input(
            "Price (₹)",
            value=default_price,
            max_chars=12,
            key=f"admin_market_price_{chosen_id}_{platform_pick}",
        )
        url = st.text_input(
            "Product URL",
            value=default_url,
            placeholder="https://www.amazon.in/dp/...",
            max_chars=500,
            key=f"admin_market_url_{chosen_id}_{platform_pick}",
        )
        submitted = st.form_submit_button(
            "💾  Save listing", type="primary", key="admin_market_submit"
        )

    if submitted:
        ok, message = data.add_marketplace(
            chosen_id, platform_pick, price, url
        )
        st.markdown(
            ui.admin_result_html("ok" if ok else "bad", message),
            unsafe_allow_html=True,
        )
        if ok:
            st.session_state.data_version += 1
            st.rerun()


def admin_scroll_to_edit_form():
    """Scroll the page up to the edit form right after an ✏️ row click.

    The row button sets admin_scroll_edit before its rerun. On that one run we
    draw a zero-height iframe whose tiny script scrolls the parent page to the
    Edit Product tab. The script retries for a few seconds, because the tab
    panel may still be mounting when the iframe runs - the scroll only happens
    once the element is really in the page. The flag is popped, so ordinary tab
    switches and saves never trigger a scroll, and if a browser blocks the
    script the app simply keeps its normal behaviour.
    """
    if not st.session_state.pop("admin_scroll_edit", False):
        return

    st.iframe(
        """
        <script>
          (function () {
            var tries = 0;
            var done = false;
            function pick() {
              try {
                // the tabs bar is always visible (even while the tab panel is
                // still loading), so it is the most reliable thing to land on
                var bar = window.parent.document.getElementById('admin_tabs');
                if (bar) {
                  bar.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  return true;
                }
                var anchor = window.parent.document.getElementById('admin_edit_anchor');
                if (anchor) {
                  anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  return true;
                }
              } catch (err) {
                return true; // parent page blocked - give up silently
              }
              return false;
            }
            var timer = window.setInterval(function () {
              tries += 1;
              if (pick() || tries >= 30) {
                window.clearInterval(timer);
              }
            }, 150);
          })();
        </script>
        """,
        height=1,
    )


def page_admin():
    """The Admin Panel for product and customer management."""
    if not require_admin():
        return

    products = data.load_products()
    admin_added = int(products["Product_ID"].astype(str).str.startswith("PRD-").sum())

    with st.container(key="admin_hero"):
        st.markdown(
            ui.admin_header_html(len(products), admin_added),
            unsafe_allow_html=True,
        )

    # the green "Saved!" strip, shown once after an add or an edit
    flash = st.session_state.pop("admin_flash", None)
    if flash:
        kind, message = flash
        st.markdown(ui.admin_result_html(kind, message), unsafe_allow_html=True)

    st.markdown("")
    # after an ✏️ row click the table asks which tab to open on the next run
    wanted_tab = st.session_state.pop("admin_wanted_tab", None)
    tab_add, tab_edit, tab_market, tab_customers = st.tabs(
        [
            "➕  Add Product",
            "✏️  Edit Product",
            "🏷️  Marketplace prices",
            "👥  Customers",
        ],
        key="admin_tabs",
        default=wanted_tab,
    )
    with tab_add:
        admin_add_form()
    with tab_edit:
        admin_edit_form()
        admin_scroll_to_edit_form()
    with tab_market:
        admin_marketplace_form()
    with tab_customers:
        admin_customer_management()

    admin_product_table()

    st.markdown("")
    action_row = st.columns(2)
    if action_row[0].button("🏠  Back to Home", key="admin_home"):
        st.session_state.admin_logged_in = False
        go_to("home")
    if action_row[1].button("🔓  Log out of Admin", key="admin_logout"):
        st.session_state.admin_logged_in = False
        st.session_state.admin_edit_id = None
        st.toast("Admin logged out", icon="🔒")
        go_to("home")


# ===========================================================================
# MAIN
# ===========================================================================


def main():
    start_session()

    # 1. create the storage files the first time the app runs
    created_files = data.initialise_storage()
    if created_files:
        st.toast(
            "Created " + ", ".join(created_files) + " for the first time.",
            icon="📁",
        )

    # 2. style + animated background
    ui.apply_theme(st.session_state.theme)
    ui.animated_background()

    # 3. navigation
    render_navbar()

    # 4. the requested page
    page = st.session_state.page
    if page == "home":
        page_home()
    elif page == "register":
        page_register()
    elif page == "welcome":
        page_welcome()
    elif page == "login":
        page_login()
    elif page == "returning":
        page_returning()
    elif page == "recommendations":
        page_recommendations()
    elif page == "product":
        page_product()
    elif page == "cart":
        page_cart()
    elif page == "insights":
        page_insights()
    elif page == "how":
        page_how()
    elif page == "about":
        page_about()
    elif page == "admin_login":
        page_admin_login()
    elif page == "admin":
        page_admin()

    st.markdown(ui.footer_html(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()