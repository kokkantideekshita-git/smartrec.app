"""
SMARTREC - "Your shopping, made smarter."
=========================================
ui.py
-----
This file contains everything that makes SMARTREC look beautiful.

It holds:
  *   the two colour themes (light + dark)
  *   one big block of CSS that styles the whole app
  *   small HTML helpers (animated background, product covers, hero, ...)

Rule of thumb for this file: it only changes how SMARTREC LOOKS.
No machine learning happens here.
"""

import base64
import os
import streamlit as st

# Where the bundled real product photos live (served at app/static/products/).
PRODUCT_IMAGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static", "products"
)

# ---------------------------------------------------------------------------
# 1. THE TWO COLOUR THEMES
# ---------------------------------------------------------------------------
# LIGHT THEME  - the official SMARTREC palette (Indigo + Violet)
# DARK THEME   - deep navy with indigo / violet glow
# ---------------------------------------------------------------------------

LIGHT_THEME = {
    "bg": "#F7F7FC",
    "bg_alt": "#EEF0FB",
    "card": "#FFFFFF",
    "card_alt": "#FBFBFF",
    "primary": "#4F46E5",
    "primary_dark": "#4338CA",
    "accent": "#7C3AED",
    "soft": "#EDE9FE",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "text": "#171717",
    "input_text": "#000000",
    "muted": "#64748B",
    "border": "#E2E2F0",
    "shadow": "0 10px 30px rgba(79, 70, 229, 0.10)",
    "shadow_soft": "0 4px 14px rgba(15, 23, 42, 0.06)",
    "nav_bg": "rgba(255, 255, 255, 0.82)",
}

DARK_THEME = {
    "bg": "#080B18",
    "bg_alt": "#0C1124",
    "card": "#121933",
    "card_alt": "#161E3C",
    "primary": "#8B8CF8",
    "primary_dark": "#6366F1",
    "accent": "#C084FC",
    "soft": "#1E2547",
    "success": "#34D399",
    "warning": "#FBBF24",
    "danger": "#F87171",
    "text": "#EAECFF",
    "input_text": "#FFFFFF",
    "muted": "#96A0C4",
    "border": "#26305A",
    "shadow": "0 12px 36px rgba(99, 102, 241, 0.22)",
    "shadow_soft": "0 4px 16px rgba(0, 0, 0, 0.35)",
    "nav_bg": "rgba(18, 25, 51, 0.82)",
}


def theme_variables(theme_name):
    """
    Turn the palette into CSS variables.

    Streamlit keeps some of its own colours in CSS variables as well
    (for example --background-color), so we simply overwrite those too.
    That is how the dark mode toggle works without reloading the app.
    """
    palette = DARK_THEME if theme_name == "dark" else LIGHT_THEME

    lines = [":root {"]
    for name, value in palette.items():
        lines.append(f"    --{name}: {value};")
    # Streamlit's own variables
    lines.append(f"    --background-color: {palette['bg']};")
    lines.append(f"    --secondary-background-color: {palette['card']};")
    lines.append(f"    --text-color: {palette['text']};")
    lines.append(f"    --primary-color: {palette['primary']};")
    lines.append(f"    --border-color: {palette['border']};")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 2. THE MAIN STYLESHEET
# ---------------------------------------------------------------------------
# Everything below is plain CSS. It makes rounded cards, soft shadows,
# hover effects, smooth transitions and the animated background.
# ---------------------------------------------------------------------------

BASE_CSS = """
/* ---------- page basics ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
}
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
.stApp { background: var(--bg) !important; }
[data-testid="stMain"] { position: relative; z-index: 2; }
[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stMainBlockContainer"] {
    padding-top: 1.1rem;
    padding-bottom: 5rem;
    max-width: 1240px;
}
.block-container { max-width: 1240px; }
p, span, div, label, h1, h2, h3, h4, li { color: var(--text); }
[data-testid="stCaptionContainer"] p,
[data-testid="stMarkdownContainer"] p { color: var(--muted); }
hr { border-color: var(--border); }

/* ---------- animated background ---------- */
.sr-background {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
    background:
        radial-gradient(1100px 620px at 12% -8%, rgba(124, 58, 237, 0.13), transparent 60%),
        radial-gradient(900px 520px at 92% 4%, rgba(79, 70, 229, 0.13), transparent 62%),
        radial-gradient(760px 620px at 50% 112%, rgba(99, 102, 241, 0.11), transparent 60%);
}
.sr-blob {
    position: absolute;
    border-radius: 50%;
    filter: blur(64px);
    opacity: 0.42;
    animation: sr-drift 26s ease-in-out infinite alternate;
}
.sr-blob.b1 { width: 420px; height: 420px; top: -110px; left: -80px;
    background: radial-gradient(circle, rgba(124,58,237,.55), rgba(124,58,237,0)); }
.sr-blob.b2 { width: 380px; height: 380px; top: 24%; right: -110px;
    background: radial-gradient(circle, rgba(79,70,229,.5), rgba(79,70,229,0));
    animation-duration: 32s; animation-delay: -6s; }
.sr-blob.b3 { width: 340px; height: 340px; bottom: -120px; left: 32%;
    background: radial-gradient(circle, rgba(147,51,234,.4), rgba(147,51,234,0));
    animation-duration: 38s; animation-delay: -12s; }
@keyframes sr-drift {
    0%   { transform: translate3d(0, 0, 0) scale(1); }
    50%  { transform: translate3d(46px, -34px, 0) scale(1.09); }
    100% { transform: translate3d(-38px, 42px, 0) scale(0.95); }
}
.sr-particle {
    position: absolute;
    width: 4px; height: 4px;
    border-radius: 50%;
    background: var(--primary);
    opacity: 0.32;
    animation: sr-float 17s linear infinite;
}
@keyframes sr-float {
    0%   { transform: translateY(0) translateX(0); opacity: 0; }
    12%  { opacity: 0.35; }
    88%  { opacity: 0.28; }
    100% { transform: translateY(-118vh) translateX(46px); opacity: 0; }
}

/* ---------- navigation bar ---------- */
.st-key-navbar {
    background: var(--nav_bg);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 10px 16px;
    box-shadow: var(--shadow_soft);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    margin-bottom: 20px;
    position: sticky;
    top: 8px;
    z-index: 40;
}
.sr-logo { display: flex; align-items: center; gap: 9px; font-size: 22px; font-weight: 800;
    letter-spacing: -0.4px; color: var(--text); white-space: nowrap; }
.sr-logo .mark {
    width: 34px; height: 34px; border-radius: 11px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff; font-size: 18px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
}
.sr-logo span.brand { background: linear-gradient(90deg, var(--primary), var(--accent));
    -webkit-background-clip: text; background-clip: text; color: transparent; }
.st-key-navbar button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: 12px !important;
    padding: 0.32rem 0.55rem !important;
    transition: all 0.18s ease !important;
}
.st-key-navbar button:hover {
    color: var(--primary) !important;
    background: var(--soft) !important;
    transform: translateY(-1px);
}
.st-key-navbar button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
    color: #fff !important;
    box-shadow: 0 6px 18px rgba(79, 70, 229, 0.3);
}
.st-key-navbar button p { color: inherit !important; font-weight: 600 !important; }
.st-key-navbar button:hover p { color: inherit !important; }

/* ---------- generic buttons ---------- */
.stButton > button, .stDownloadButton > button {
    border-radius: 13px !important;
    border: 1px solid var(--border) !important;
    background: var(--card) !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease,
                background 0.18s ease !important;
    box-shadow: var(--shadow_soft) !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    border-color: var(--primary) !important;
    box-shadow: 0 10px 22px rgba(79, 70, 229, 0.16) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
    color: #fff !important;
    border-color: transparent !important;
    box-shadow: 0 8px 22px rgba(79, 70, 229, 0.28) !important;
}
.stButton > button p { color: inherit !important; }
.stButton > button:disabled { opacity: 0.5 !important; transform: none !important; }

/* ---------- hero ---------- */
.sr-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--soft); color: var(--primary_dark);
    border: 1px solid rgba(124, 58, 237, 0.22);
    padding: 6px 15px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 800; letter-spacing: 1.3px;
}
.sr-hero-title {
    font-size: clamp(2.1rem, 5.2vw, 3.65rem);
    font-weight: 850; line-height: 1.06; letter-spacing: -1.6px;
    margin: 14px 0 6px 0;
}
.sr-hero-title span {
    background: linear-gradient(100deg, var(--primary) 8%, var(--accent) 92%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.sr-hero-sub { font-size: 1.06rem; line-height: 1.65; max-width: 640px; }
.sr-tagline { font-size: 1.02rem; font-weight: 650; color: var(--muted); letter-spacing: -0.2px; }

/* ---------- glass cards ---------- */
.sr-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 22px 24px;
    box-shadow: var(--shadow_soft);
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}
.sr-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); border-color: rgba(124,58,237,.3); }
.sr-card-title { font-size: 1.02rem; font-weight: 750; letter-spacing: -0.3px; margin-bottom: 6px; }
.sr-card-text { font-size: 0.92rem; line-height: 1.62; color: var(--muted); }

/* ---------- big choice cards on the home page ---------- */
.st-key-choice_existing, .st-key-choice_new {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 26px 22px !important;
    box-shadow: var(--shadow_soft) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
}
.st-key-choice_existing:hover, .st-key-choice_new:hover {
    transform: translateY(-6px) !important;
    box-shadow: var(--shadow) !important;
    border-color: var(--primary) !important;
}
.sr-choice-icon {
    width: 58px; height: 58px; border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 12px;
    background: linear-gradient(135deg, var(--soft), rgba(124,58,237,.18));
    border: 1px solid rgba(124, 58, 237, 0.2);
}
.sr-choice-title { font-size: 1.15rem; font-weight: 780; letter-spacing: -0.3px; }
.sr-choice-text { font-size: 0.88rem; color: var(--muted); line-height: 1.6; margin-top: 6px; }

/* ---------- product detail page ---------- */
.st-key-product_gallery {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 18px !important;
    box-shadow: var(--shadow_soft) !important;
}
.st-key-product_gallery .sr-cover { border-radius: 20px; overflow: hidden; }
.st-key-product_gallery .sr-cover img { height: 250px; }
.sr-crumb { font-size: 0.82rem; color: var(--muted); font-weight: 600; margin-bottom: 6px; }
.sr-crumb b { color: var(--primary); }
.sr-pd-title { font-size: 1.5rem; font-weight: 820; letter-spacing: -0.6px; line-height: 1.22; color: var(--text); }
.sr-pd-brand { font-size: 0.83rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }
.sr-pd-price { display: flex; align-items: baseline; gap: 11px; flex-wrap: wrap; margin: 12px 0 4px 0; }
.sr-pd-price .now { font-size: 2rem; font-weight: 850; color: var(--text); letter-spacing: -1px; }
.sr-pd-price .was { font-size: 1rem; color: var(--muted); text-decoration: line-through; font-weight: 650; }
.sr-pd-price .off { font-size: 0.86rem; font-weight: 800; color: var(--success); background: rgba(5,150,105,.12);
                    border: 1px solid rgba(5,150,105,.28); border-radius: 999px; padding: 4px 11px; }
.sr-pd-rating { display: inline-flex; align-items: center; gap: 8px; font-size: 0.87rem; font-weight: 700; }
.sr-pd-rating .stars { color: #F59E0B; letter-spacing: 1px; font-size: 0.95rem; }
.sr-pd-rating .score { background: var(--success); color: #fff; border-radius: 7px; padding: 2px 9px; font-weight: 800; }
.sr-pd-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.sr-opt-label { font-size: 0.78rem; font-weight: 800; color: var(--text); text-transform: uppercase; letter-spacing: 0.5px; margin: 16px 0 4px 0; }
.sr-highlight {
    display: flex; gap: 10px; align-items: flex-start; font-size: 0.88rem;
    color: var(--muted); line-height: 1.55; padding: 9px 0;
    border-bottom: 1px dashed var(--border);
}
.sr-highlight:last-child { border-bottom: none; }
.sr-highlight .tick { color: var(--success); font-weight: 900; }
.sr-offer {
    display: flex; gap: 11px; align-items: center; font-size: 0.86rem;
    background: var(--soft); border: 1px solid var(--border);
    border-left: 4px solid var(--primary); border-radius: 13px;
    padding: 11px 14px; margin-top: 9px; color: var(--text);
}
.sr-trust { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 9px; margin-top: 6px; }
.sr-trust .t { background: var(--card_alt); border: 1px solid var(--border); border-radius: 13px; padding: 10px 12px; }
.sr-trust .t .h { font-size: 0.8rem; font-weight: 800; color: var(--text); }
.sr-trust .t .d { font-size: 0.76rem; color: var(--muted); margin-top: 3px; }

/* ---------- cart page ---------- */
[class*="st-key-cart_line"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 14px 16px !important;
    margin-bottom: 10px !important;
    box-shadow: var(--shadow_soft) !important;
}
[class*="st-key-cart_line"] .sr-cover { border-radius: 15px; overflow: hidden; }
[class*="st-key-cart_line"] .sr-cover img { height: 92px; }
.st-key-cart_summary {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    padding: 22px !important;
    box-shadow: var(--shadow_soft) !important;
    position: sticky; top: 96px;
}
.sr-cart-name { font-size: 0.98rem; font-weight: 750; color: var(--text); letter-spacing: -0.2px; }
.sr-cart-meta { font-size: 0.76rem; color: var(--muted); font-weight: 600; margin-top: 3px; }
.sr-cart-line-total { font-size: 1.16rem; font-weight: 820; color: var(--text); letter-spacing: -0.3px; }
.sr-summary-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.9rem; color: var(--muted); padding: 8px 0;
}
.sr-summary-row.grand {
    border-top: 1.5px solid var(--border); margin-top: 8px; padding-top: 13px;
    font-size: 1.06rem; font-weight: 820; color: var(--text);
}
.sr-summary-row .save { color: var(--success); font-weight: 750; }
.sr-empty {
    text-align: center; padding: 46px 20px;
}
.sr-empty .icon { font-size: 54px; }
.sr-empty .h { font-size: 1.16rem; font-weight: 800; color: var(--text); margin-top: 12px; }
.sr-empty .d { font-size: 0.9rem; color: var(--muted); margin-top: 6px; }

/* ---------- admin panel ---------- */
.st-key-admin_gate, .st-key-admin_hero {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 26px 24px !important;
    box-shadow: var(--shadow_soft) !important;
}
.st-key-admin_summary {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 16px 18px !important;
    margin-bottom: 10px !important;
    box-shadow: var(--shadow_soft) !important;
}
.sr-admin-badge {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 5px 13px; border-radius: 999px;
    background: rgba(124, 92, 255, 0.14);
    border: 1px solid rgba(124, 92, 255, 0.34);
    font-size: 0.7rem; font-weight: 800; letter-spacing: 1.2px;
    color: var(--accent); text-transform: uppercase;
}
.sr-admin-title {
    font-size: 1.7rem; font-weight: 850; letter-spacing: -0.7px;
    color: var(--text); margin: 12px 0 6px;
}
.sr-admin-sub { font-size: 0.92rem; color: var(--muted); font-weight: 550; }
.sr-admin-stat {
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    padding: 15px 10px; border-radius: 18px;
    background: var(--card_alt); border: 1px solid var(--border);
}
.sr-admin-stat .v {
    font-size: 1.5rem; font-weight: 850; color: var(--accent); letter-spacing: -0.5px;
}
.sr-admin-stat .l {
    font-size: 0.68rem; font-weight: 750; color: var(--muted);
    letter-spacing: 0.9px; text-transform: uppercase;
}
.sr-admin-id {
    display: inline-block; padding: 3px 9px; border-radius: 8px;
    background: rgba(124, 92, 255, 0.13); color: var(--accent);
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 0.74rem; font-weight: 700;
}
.sr-admin-new {
    display: inline-block; padding: 2px 8px; border-radius: 999px;
    background: rgba(52, 199, 143, 0.16); color: var(--success);
    font-size: 0.66rem; font-weight: 800; letter-spacing: 0.5px;
}
.sr-admin-foot {
    text-align: center; font-size: 0.76rem; color: var(--muted);
    margin-top: 16px; line-height: 1.6;
}
.sr-admin-head {
    display: grid;
    grid-template-columns: 108px minmax(0,1fr) 108px 96px 78px;
    gap: 12px; align-items: center;
    padding: 0 14px 10px; margin-bottom: 4px;
    font-size: 0.66rem; font-weight: 800; letter-spacing: 1px;
    color: var(--muted); text-transform: uppercase;
}
/* every catalogue line is a real Streamlit row, so the Edit button sits
   inside the row instead of underneath it */
[class*="st-key-admin_row_"] {
    padding: 10px 14px; border-radius: 16px; margin-bottom: 8px;
    background: var(--card); border: 1px solid var(--border);
    box-shadow: var(--shadow_soft);
    transition: border-color 0.15s ease;
}
[class*="st-key-admin_row_"]:hover { border-color: rgba(124, 92, 255, 0.5); }
[class*="st-key-admin_row_now_"] {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent) inset, var(--shadow_soft);
}
/* one marketplace listing row in the admin panel */
[class*="st-key-admin_mp_row_"] {
    padding: 9px 14px; border-radius: 14px; margin-bottom: 6px;
    background: var(--card); border: 1px solid var(--border);
}
.sr-admin-name {
    font-size: 0.88rem; font-weight: 700; color: var(--text);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.sr-admin-cat { font-size: 0.78rem; color: var(--muted); font-weight: 650; }
.sr-admin-price { font-size: 0.88rem; font-weight: 800; color: var(--text); }
.sr-admin-empty {
    padding: 26px 16px; text-align: center; border-radius: 16px;
    background: var(--card_alt); border: 1px dashed var(--border);
    font-size: 0.86rem; color: var(--muted); font-weight: 600;
}
.sr-admin-result {
    padding: 12px 16px; border-radius: 15px; margin: 4px 0 12px;
    font-size: 0.86rem; font-weight: 700;
}
.sr-admin-result.ok {
    background: rgba(52, 199, 143, 0.14);
    border: 1px solid rgba(52, 199, 143, 0.36);
    color: var(--success);
}
.sr-admin-result.bad {
    background: rgba(255, 107, 129, 0.14);
    border: 1px solid rgba(255, 107, 129, 0.36);
    color: var(--danger);
}
@media (max-width: 780px) {
    /* Streamlit stacks the row columns on a narrow screen by itself, so the
       fixed header would no longer line up with anything - hide it */
    .sr-admin-head { display: none; }
    .sr-admin-name { white-space: normal; }
    [class*="st-key-admin_row_"] { padding: 10px 12px; }
}

/* ---------- "Where to Buy" marketplace box (product page) ---------- */
.sr-mp-box {
    display: flex; flex-direction: column; gap: 10px;
    margin: 6px 0 10px;
}
.sr-mp-row {
    display: grid; grid-template-columns: 44px 1fr auto 128px;
    gap: 14px; align-items: center;
    padding: 13px 16px; border-radius: 16px;
    background: var(--card); border: 1px solid var(--border);
    box-shadow: var(--shadow_soft);
}
.sr-mp-row.best {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent) inset, var(--shadow_soft);
    background: linear-gradient(180deg, rgba(124, 92, 255, 0.12), var(--card) 60%);
}
.sr-mp-rank {
    width: 42px; height: 42px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    background: var(--card_alt); border: 1px solid var(--border);
    font-size: 1.15rem; font-weight: 800;
}
.sr-mp-store { display: flex; flex-direction: column; gap: 6px; }
.sr-mp-name {
    font-size: 1.02rem; font-weight: 800; color: var(--text);
    letter-spacing: -0.2px;
}
.sr-mp-best-tag {
    display: inline-block; width: fit-content;
    padding: 3px 10px; border-radius: 999px;
    background: rgba(52, 199, 143, 0.16); color: var(--success);
    font-size: 0.64rem; font-weight: 800; letter-spacing: 0.6px;
}
.sr-mp-price {
    font-size: 1.05rem; font-weight: 850; color: var(--text);
    white-space: nowrap;
}
.sr-mp-buy {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 10px 18px; border-radius: 12px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: #fff; font-size: 0.78rem; font-weight: 800; letter-spacing: 0.4px;
    text-decoration: none; cursor: pointer; white-space: nowrap;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
a.sr-mp-buy:hover { transform: translateY(-1px); box-shadow: 0 12px 26px rgba(79, 70, 229, 0.4); }
.sr-mp-checked {
    text-align: center; font-size: 0.72rem; color: var(--muted);
    margin-top: 2px; line-height: 1.6;
}
.sr-mp-plain {
    padding: 26px 20px; text-align: center; border-radius: 18px;
    background: var(--card); border: 1px dashed var(--border);
    box-shadow: var(--shadow_soft);
}
.sr-mp-plain-title {
    font-size: 1rem; font-weight: 800; color: var(--text); margin-bottom: 6px;
}
.sr-mp-plain-text { font-size: 0.9rem; color: var(--text); font-weight: 650; }
.sr-mp-plain-note { font-size: 0.74rem; color: var(--muted); margin-top: 8px; line-height: 1.6; }
@media (max-width: 760px) {
    .sr-mp-row { grid-template-columns: 40px 1fr auto; }
    .sr-mp-buy { grid-column: 2 / -1; width: 100%; }
    .sr-mp-price { justify-self: end; }
}

/* ---------- team member card (About page) ---------- */
.sr-member {
    display: flex; align-items: center; gap: 22px; flex-wrap: wrap;
}
.sr-avatar {
    width: 86px; height: 86px; min-width: 86px; border-radius: 26px;
    display: flex; align-items: center; justify-content: center;
    font-size: 30px; font-weight: 800; color: #fff; letter-spacing: -1px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    box-shadow: 0 12px 30px rgba(79, 70, 229, 0.32);
}
.sr-member-body { flex: 1 1 320px; min-width: 260px; }
.sr-member-name { font-size: 1.34rem; font-weight: 800; letter-spacing: -0.5px; color: var(--text); }
.sr-member-role { font-size: 0.86rem; color: var(--primary); font-weight: 700; letter-spacing: 0.3px; text-transform: uppercase; margin-top: 3px; }
.sr-member-about { font-size: 0.9rem; color: var(--muted); line-height: 1.6; margin-top: 8px; }
.sr-member-tasks { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.sr-task {
    font-size: 0.79rem; font-weight: 650; color: var(--text);
    background: var(--soft); border: 1px solid var(--border);
    border-radius: 999px; padding: 6px 13px;
}

/* ---------- product cards (the Top 5) ---------- */
.st-key-rec_card_1, .st-key-rec_card_2, .st-key-rec_card_3,
.st-key-rec_card_4, .st-key-rec_card_5 {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 16px 16px 14px 16px !important;
    box-shadow: var(--shadow_soft) !important;
    height: 100%;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
}
.st-key-rec_card_1:hover, .st-key-rec_card_2:hover, .st-key-rec_card_3:hover,
.st-key-rec_card_4:hover, .st-key-rec_card_5:hover {
    transform: translateY(-8px) !important;
    box-shadow: var(--shadow) !important;
    border-color: rgba(124, 58, 237, 0.45) !important;
}
.st-key-rec_card_1 {
    border: 1.5px solid var(--primary) !important;
    box-shadow: 0 14px 34px rgba(79, 70, 229, 0.22) !important;
    background: linear-gradient(180deg, var(--soft) 0%, var(--card) 42%) !important;
}
.st-key-rec_card_1:hover { transform: translateY(-10px) scale(1.012) !important; }
.st-key-rec_card_2, .st-key-rec_card_3 { border-color: rgba(124, 58, 237, 0.26) !important; }
[class*="st-key-shop_card"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 14px !important;
    box-shadow: var(--shadow_soft) !important;
    height: 100%;
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease !important;
}
[class*="st-key-shop_card"]:hover {
    transform: translateY(-6px) !important;
    box-shadow: var(--shadow) !important;
    border-color: rgba(124, 58, 237, 0.35) !important;
}
.sr-cover { border-radius: 16px; overflow: hidden; display: block; line-height: 0; }
.sr-cover img {
    width: 100%; height: 152px; object-fit: cover; display: block;
    transition: transform 0.55s cubic-bezier(.2,.7,.3,1);
}
.st-key-rec_card_1:hover .sr-cover img,
[class*="st-key-shop_card"]:hover .sr-cover img,
.st-key-rec_card_2:hover .sr-cover img,
.st-key-rec_card_3:hover .sr-cover img,
.st-key-rec_card_4:hover .sr-cover img,
.st-key-rec_card_5:hover .sr-cover img { transform: scale(1.08); }

.sr-rank {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 30px; height: 26px; padding: 0 8px;
    border-radius: 9px; font-size: 0.76rem; font-weight: 850;
    background: var(--soft); color: var(--primary_dark);
    border: 1px solid rgba(124, 58, 237, 0.25);
}
.sr-rank.top { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff;
    border-color: transparent; box-shadow: 0 5px 14px rgba(79, 70, 229, 0.35); }
.sr-label {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.68rem; font-weight: 850; letter-spacing: 0.9px;
    padding: 4px 9px; border-radius: 8px;
    background: var(--soft); color: var(--primary_dark);
    border: 1px solid rgba(124, 58, 237, 0.22);
}
.sr-label.l1 { background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; border-color: transparent; }
.sr-label.l2 { background: rgba(5, 150, 105, 0.12); color: var(--success); border-color: rgba(5,150,105,.25); }
.sr-label.l3 { background: rgba(217, 119, 6, 0.12); color: var(--warning); border-color: rgba(217,119,6,.25); }
.sr-product-name { font-size: 0.98rem; font-weight: 750; line-height: 1.32; letter-spacing: -0.2px;
    margin: 9px 0 3px 0; }
.sr-product-meta { font-size: 0.76rem; color: var(--muted); font-weight: 600; letter-spacing: 0.2px; }
.sr-price { font-size: 1.22rem; font-weight: 850; letter-spacing: -0.5px; margin-top: 8px; }
.sr-price s { font-size: 0.78rem; color: var(--muted); font-weight: 600; margin-left: 6px; }
.sr-seen { font-size: 0.72rem; color: var(--muted); margin-top: 6px; }

/* card buttons */
.st-key-rec_card_1 button, .st-key-rec_card_2 button, .st-key-rec_card_3 button,
.st-key-rec_card_4 button, .st-key-rec_card_5 button,
[class*="st-key-shop_card"] button {
    border-radius: 11px !important; font-size: 0.78rem !important; font-weight: 650 !important;
    padding: 0.34rem 0.3rem !important; width: 100%;
}
.st-key-rec_card_1 .stButton > button, .st-key-rec_card_2 .stButton > button,
.st-key-rec_card_3 .stButton > button, .st-key-rec_card_4 .stButton > button,
.st-key-rec_card_5 .stButton > button {
    background: var(--card_alt) !important; color: var(--text) !important;
}
[class*="st-key-shop_card"] .stButton > button { background: var(--card_alt) !important; }

/* ---------- reasons / why this product ---------- */
.sr-reason {
    font-size: 0.87rem; line-height: 1.55; color: var(--muted);
    padding: 7px 0; border-bottom: 1px dashed var(--border);
}
.sr-reason:last-child { border-bottom: none; }
.sr-reason b { color: var(--text); font-weight: 700; }
details[data-testid="stExpander"] {
    border: 1px solid var(--border) !important; border-radius: 15px !important;
    background: var(--card-alt) !important; box-shadow: none !important;
}
details[data-testid="stExpander"] summary { font-size: 0.84rem !important; font-weight: 650 !important; }

/* ---------- stat + metric cards ---------- */
.sr-stat {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 18px; padding: 16px 18px; box-shadow: var(--shadow_soft);
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.sr-stat:hover { transform: translateY(-4px); box-shadow: var(--shadow); }
.sr-stat .k { font-size: 0.72rem; font-weight: 750; letter-spacing: 0.9px;
    text-transform: uppercase; color: var(--muted); }
.sr-stat .v { font-size: 1.7rem; font-weight: 850; letter-spacing: -1px; margin-top: 5px;
    background: linear-gradient(100deg, var(--primary), var(--accent));
    -webkit-background-clip: text; background-clip: text; color: transparent; }
.sr-stat .s { font-size: 0.78rem; color: var(--muted); }
.sr-stat .v.plain { background: none; -webkit-text-fill-color: var(--text); color: var(--text); }

/* ---------- customer id hero ---------- */
.sr-id-box {
    text-align: center; padding: 30px 22px;
    background: linear-gradient(140deg, var(--primary), var(--accent));
    border-radius: 26px; color: #fff;
    box-shadow: 0 20px 48px rgba(79, 70, 229, 0.32);
    position: relative; overflow: hidden;
}
.sr-id-box::after {
    content: ""; position: absolute; inset: -40% -10% auto -10%; height: 180%;
    background: radial-gradient(circle at 30% 20%, rgba(255,255,255,.22), transparent 55%);
    animation: sr-drift 20s ease-in-out infinite alternate;
}
.sr-id-box .k { font-size: 0.76rem; letter-spacing: 1.4px; font-weight: 750; opacity: 0.9; }
.sr-id-box .v {
    font-size: clamp(2.4rem, 7vw, 3.4rem); font-weight: 900; letter-spacing: 3px;
    margin: 8px 0 6px 0; text-shadow: 0 6px 22px rgba(0,0,0,.18);
}
.sr-id-box .s { font-size: 0.9rem; opacity: 0.94; }

/* ---------- pipeline (How it works) ---------- */
.sr-step {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 20px; padding: 18px 20px; box-shadow: var(--shadow_soft);
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color .22s ease;
}
.sr-step:hover { transform: translateY(-5px); box-shadow: var(--shadow); border-color: rgba(124,58,237,.35); }
.sr-step .ic {
    width: 46px; height: 46px; border-radius: 14px; font-size: 21px;
    display: flex; align-items: center; justify-content: center; margin-bottom: 11px;
    background: linear-gradient(135deg, var(--soft), rgba(124,58,237,.16));
    border: 1px solid rgba(124, 58, 237, 0.2);
}
.sr-step .t { font-weight: 760; font-size: 0.97rem; letter-spacing: -0.2px; }
.sr-step .d { font-size: 0.85rem; color: var(--muted); line-height: 1.55; margin-top: 5px; }
.sr-step .num {
    float: right; font-size: 0.72rem; font-weight: 800; color: var(--primary);
    background: var(--soft); border-radius: 8px; padding: 3px 8px;
}
.sr-arrow {
    display: flex; align-items: center; justify-content: center;
    color: var(--primary); font-size: 1.3rem; font-weight: 800; padding: 2px 0;
    animation: sr-bob 2.4s ease-in-out infinite;
}
@keyframes sr-bob { 0%,100% { transform: translateY(0); opacity:.75 } 50% { transform: translateY(5px); opacity:1 } }

/* ---------- loading animation ---------- */
.sr-loader { display: flex; align-items: center; gap: 11px; padding: 5px 0; }
.sr-loader .ring {
    width: 19px; height: 19px; border-radius: 50%;
    border: 2.5px solid var(--border); border-top-color: var(--primary);
    animation: sr-spin 0.85s linear infinite; flex: 0 0 auto;
}
@keyframes sr-spin { to { transform: rotate(360deg); } }
.sr-loader .txt { font-size: 0.92rem; font-weight: 600; color: var(--muted); }
.sr-progress {
    height: 5px; border-radius: 99px; background: var(--border); overflow: hidden; margin-top: 9px;
}
.sr-progress > span {
    display: block; height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    animation: sr-fill 1.6s cubic-bezier(.4,0,.2,1) forwards;
}
@keyframes sr-fill { from { width: 0 } to { width: 100% } }

/* ---------- sections / chips ---------- */
.sr-section-title { font-size: 1.32rem; font-weight: 820; letter-spacing: -0.6px; }
.sr-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 999px; padding: 5px 13px; font-size: 0.79rem;
    font-weight: 650; color: var(--muted); box-shadow: var(--shadow_soft);
}
.sr-divider { height: 1px; background: var(--border); margin: 22px 0; border: none; }

/* ---------- plotly charts ---------- */
[data-testid="stPlotlyChart"] {
    border: 1px solid var(--border); border-radius: 20px;
    overflow: hidden; background: var(--card); box-shadow: var(--shadow_soft);
}

/* ---------- inputs ---------- */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-radius: 13px !important; color: var(--input_text) !important;
    -webkit-text-fill-color: var(--input_text) !important; caret-color: var(--primary);
    font-weight: 600 !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: var(--input_text) !important; -webkit-text-fill-color: var(--input_text) !important;
    opacity: 1;
}
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {
    border-color: var(--primary) !important; box-shadow: 0 0 0 3px rgba(124,58,237,.14) !important;
}
[data-baseweb="select"] > div, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: var(--card) !important; border-radius: 13px !important;
}
[data-testid="stSidebar"] { background: var(--card); }
[data-testid="stMetric"] {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 18px; padding: 14px 16px; box-shadow: var(--shadow_soft);
}
[data-testid="stMetricValue"] { font-weight: 850 !important; letter-spacing: -1px; }

/* ---------- toast / alerts ---------- */
[data-testid="stToast"] { border-radius: 14px !important; }
.stAlert { border-radius: 16px !important; }

/* ---------- footer ---------- */
.sr-footer {
    text-align: center; color: var(--muted); font-size: 0.82rem;
    padding: 26px 0 6px 0; border-top: 1px solid var(--border); margin-top: 34px;
}
.sr-footer b { color: var(--primary); }

/* ---------- entrance animation ---------- */
.sr-fade-up { animation: sr-up 0.55s cubic-bezier(.22,.9,.3,1) both; }
@keyframes sr-up { from { opacity: 0; transform: translateY(16px) } to { opacity: 1; transform: none } }

/* ---------- small screens ---------- */
@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] { padding-left: 0.9rem; padding-right: 0.9rem; }
    .st-key-navbar { border-radius: 18px; padding: 8px 10px; }
    .sr-hero-title { letter-spacing: -1px; }
}
"""

# ---------------------------------------------------------------------------
# 3. INJECT EVERYTHING INTO THE PAGE
# ---------------------------------------------------------------------------


def apply_theme(theme_name):
    """Load the CSS of the selected theme into the Streamlit page."""
    st.markdown(
        f"<style>{theme_variables(theme_name)}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<style>{BASE_CSS}</style>", unsafe_allow_html=True)


def animated_background():
    """
    The soft moving gradient blobs and floating particles behind the app.

    It is pure HTML + CSS animation, so it never slows SMARTREC down.
    """
    # a few particles with different sizes / speeds
    particles = ""
    sizes = [3, 5, 4, 6, 3, 5, 4, 3, 5, 4, 6, 3]
    for index, size in enumerate(sizes):
        left = 4 + index * 8
        delay = -(index * 1.7) % 17
        duration = 15 + (index % 5) * 2.5
        particles += (
            f'<div class="sr-particle" style="left:{left}%;bottom:-20px;'
            f'width:{size}px;height:{size}px;animation-delay:{delay:.1f}s;'
            f'animation-duration:{duration:.1f}s;"></div>'
        )

    st.markdown(
        f"""
        <div class="sr-background">
            <div class="sr-blob b1"></div>
            <div class="sr-blob b2"></div>
            <div class="sr-blob b3"></div>
            {particles}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 4. PRODUCT COVER IMAGES
# ---------------------------------------------------------------------------
# The product pictures are generated as small SVG drawings, so the app does
# not need any internet connection or extra image files.
# ---------------------------------------------------------------------------


def product_cover(image_emoji, hue, product_name=""):
    """Return a data-URI SVG cover for one product."""
    hue = int(hue) if str(hue).replace(".", "").isdigit() else 258
    second_hue = (hue + 42) % 360
    initial = (product_name or "S")[:1].upper()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="hsl({hue}, 74%, 60%)"/>
          <stop offset="100%" stop-color="hsl({second_hue}, 72%, 42%)"/>
        </linearGradient>
        <radialGradient id="s" cx="28%" cy="18%" r="78%">
          <stop offset="0%" stop-color="rgba(255,255,255,0.38)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
        </radialGradient>
      </defs>
      <rect width="400" height="300" fill="url(#g)"/>
      <rect width="400" height="300" fill="url(#s)"/>
      <circle cx="336" cy="54" r="64" fill="rgba(255,255,255,0.11)"/>
      <circle cx="54" cy="252" r="86" fill="rgba(0,0,0,0.09)"/>
      <circle cx="300" cy="252" r="30" fill="rgba(255,255,255,0.08)"/>
      <text x="200" y="138" font-size="104" text-anchor="middle"
            font-family="Segoe UI Emoji, Noto Color Emoji, Apple Color Emoji, sans-serif">{image_emoji}</text>
      <text x="200" y="238" font-size="26" font-weight="700" text-anchor="middle"
            fill="rgba(255,255,255,0.92)"
            font-family="Segoe UI, Inter, sans-serif">{initial}</text>
    </svg>"""

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


# ---------------------------------------------------------------------------
# 5. SMALL HTML BUILDERS
# ---------------------------------------------------------------------------

# labels used on the Top 5 recommendation cards (no percentages here!)
RECOMMENDATION_LABELS = {
    1: ("#1 BEST MATCH", "sr-label l1"),
    2: ("⭐ RECOMMENDED", "sr-label l2"),
    3: ("✨ GREAT MATCH", "sr-label l3"),
    4: ("💡 YOU MAY LIKE", "sr-label"),
    5: ("⭐ RECOMMENDED", "sr-label l2"),
}


def product_image_source(product):
    """
    Return the <img src> to use for one product.

    Priority:
      1. if the admin typed a real web address in the Admin Panel, use that;
      2. if a bundled photo exists in static/products/, use that;
      3. otherwise fall back to the generated SVG cover, so every product
         always shows a picture.
    """
    image_value = str(product.get("Product_Image", "") or "").strip()
    if image_value.lower().startswith(("http://", "https://")):
        return image_value

    product_id = str(product.get("Product_ID", "") or "").strip()
    if product_id:
        local = os.path.join(PRODUCT_IMAGE_DIR, f"{product_id}.jpg")
        if os.path.exists(local):
            return f"app/static/products/{product_id}.jpg"

    return product_cover(
        image_value or "🛍️",
        product.get("Hue", 258),
        product.get("Product_Name", ""),
    )


def logo_html():
    return (
        '<div class="sr-logo"><span class="mark">✦</span>'
        "<span class='brand'>SMARTREC</span></div>"
    )


def hero_html():
    return """
    <div class="sr-fade-up">
      <span class="sr-eyebrow">✦ AI-POWERED RECOMMENDATIONS</span>
      <div class="sr-hero-title">Your shopping,<br><span>made smarter.</span></div>
      <p class="sr-hero-sub">Discover products selected specifically for your
      interests and shopping behaviour — powered by a real machine learning
      model that learns from every view, cart add and purchase.</p>
    </div>
    """


def stat_card(title, value, subtitle="", plain=False):
    plain_class = " plain" if plain else ""
    return f"""
    <div class="sr-stat">
      <div class="k">{title}</div>
      <div class="v{plain_class}">{value}</div>
      <div class="s">{subtitle}</div>
    </div>
    """


def section_title(title, subtitle=""):
    subtitle_html = f'<div class="sr-chip">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                gap:12px; flex-wrap:wrap; margin-bottom:6px;">
      <div class="sr-section-title">{title}</div>
      {subtitle_html}
    </div>
    """


def team_card_html(name, role, initials, about, tasks):
    """One developer card: avatar with initials, name, role and task chips."""
    chips = "".join(f'<div class="sr-task">{task}</div>' for task in tasks)
    return f"""
    <div class="sr-card">
      <div class="sr-member">
        <div class="sr-avatar">{initials}</div>
        <div class="sr-member-body">
          <div class="sr-member-name">{name}</div>
          <div class="sr-member-role">{role}</div>
          <div class="sr-member-about">{about}</div>
          <div class="sr-member-tasks">{chips}</div>
        </div>
      </div>
    </div>
    """


def product_card_html(product, rank, interaction_history=None, show_reasons=False):
    """
    The visual part of a recommendation card:
    cover image, rank, label, name, category and price.

    NOTE: the purchase probability is NOT printed here on purpose - that is
    only shown on the AI Insights page.
    """
    label_text, label_class = RECOMMENDATION_LABELS.get(rank, (f"#{rank} FOR YOU", "sr-label"))
    cover = product_image_source(product)
    price = float(product.get("Product_Price", 0))
    price_text = f"₹{price:,.0f}"

    seen_text = ""
    if interaction_history is not None:
        own = interaction_history[
            interaction_history["Product_ID"] == product["Product_ID"]
        ]
        if len(own) > 0 and own.iloc[0]["Views"] > 0:
            seen_text = f'<div class="sr-seen">👁️ You viewed this {int(own.iloc[0]["Views"])}×</div>'

    return f"""
    <div class="sr-cover"><img src="{cover}" alt="{product.get("Product_Name", "")}" /></div>
    <div style="display:flex; align-items:center; justify-content:space-between; margin-top:12px;">
      <span class="sr-rank top">#{rank}</span>
      <span class="{label_class}">{label_text}</span>
    </div>
    <div class="sr-product-name">{product.get("Product_Name", "")}</div>
    <div class="sr-product-meta">{product.get("Product_Category", "")}</div>
    <div class="sr-price">{price_text}</div>
    {seen_text}
    """


def reason_html(reasons):
    """Render the honest 'Why this product?' list."""
    return "".join(f'<div class="sr-reason">✓ {reason}</div>' for reason in reasons)


def customer_id_box_html(customer_id, name):
    return f"""
    <div class="sr-id-box">
      <div class="k">YOUR SMARTREC CUSTOMER ID</div>
      <div class="v">{customer_id}</div>
      <div class="s">{name} · save this ID — use it every time you return</div>
    </div>
    """


PIPELINE_STEPS = [
    ("👤", "CUSTOMER", "A person arrives on SMARTREC. New or returning, we identify them with a unique SMR-XXXX Customer ID."),
    ("📋", "CUSTOMER / PRODUCT DATA", "We join their profile (budget, favourite categories) and their behaviour (views, cart adds, purchases) with the product catalogue."),
    ("🧹", "DATA CLEANING", "Missing values are filled, duplicate rows are removed and the numbers are made consistent."),
    ("⚙️", "FEATURE ENGINEERING", "We build useful columns such as view-to-cart rate, previous purchases, budget fit and category preference."),
    ("🧠", "MACHINE LEARNING MODEL", "A Logistic Regression model is trained on 80% of the historical data to predict buying behaviour."),
    ("📈", "PURCHASE PROBABILITY", "For every available product the model returns a real probability using predict_proba()."),
    ("🏆", "PRODUCT RANKING", "Products are sorted from the highest probability to the lowest."),
    ("🛍️", "TOP 5 RECOMMENDATIONS", "You see five products. Every view, cart add and purchase is saved and improves the next visit."),
]


def pipeline_step_html(index, icon, title, description):
    return f"""
    <div class="sr-step">
      <span class="num">{index}</span>
      <div class="ic">{icon}</div>
      <div class="t">{title}</div>
      <div class="d">{description}</div>
    </div>
    """


def footer_html():
    return """
    <div class="sr-footer">
      ✦ <b>SMARTREC</b> · Your shopping, made smarter.<br>
      AI-Powered Product Recommendation System · Built with Python, Pandas,
      Scikit-learn, Streamlit &amp; Plotly
    </div>
    """


# ---------------------------------------------------------------------------
# 7. PRODUCT PAGE + CART PAGE BUILDERS
# ---------------------------------------------------------------------------
# These return plain HTML. All the numbers come from the catalogue, cart.csv
# and the trained model - nothing here is typed in by hand.
# ---------------------------------------------------------------------------


def stars_html(rating):
    """Turn 4.3 into ★★★★☆ with a half-star look."""
    rating = float(rating or 0)
    full = int(round(rating))
    filled = "★" * full
    empty = "☆" * (5 - full)
    return f'<span class="stars">{filled}{empty}</span>'


def product_gallery_html(product):
    """The picture panel of the product page (big cover + thumbnails)."""
    cover = product_image_source(product)
    thumbnails = "".join(
        f'<img src="{cover}" style="height:100%;width:100%;object-fit:cover;" />'
        for _ in range(3)
    )
    return f"""
    <div class="sr-cover"><img src="{cover}" alt="{product['Product_Name']}" /></div>
    <div style="display:grid; grid-template-columns:repeat(3,1fr);gap:9px;margin-top:9px;">
      {thumbnails}
    </div>
    """


def product_headline_html(product):
    """Name, brand, rating and the real price block."""
    price = float(product["Product_Price"])
    mrp = float(product.get("MRP") or 0)
    discount = int(round((1 - price / mrp) * 100)) if mrp > price else 0
    rating = float(product.get("Rating") or 0)
    reviews = int(float(product.get("Reviews") or 0))
    stock = int(float(product.get("Stock") or 0))

    stock_html = (
        '<span style="color:var(--success);font-weight:750;">✅ In stock</span>'
        if stock > 5
        else '<span style="color:var(--warning);font-weight:750;">⚠️ Only a few left</span>'
        if stock > 0
        else '<span style="color:#DC2626;font-weight:750;">❌ Out of stock</span>'
    )

    return f"""
    <div class="sr-crumb">Home / {product['Product_Category']} / <b>{product['Product_Name']}</b></div>
    <div class="sr-pd-brand">{product['Brand']}</div>
    <div class="sr-pd-title">{product['Product_Name']}</div>
    <div class="sr-pd-rating" style="margin-top:10px;">
      {stars_html(rating)}
      <span class="score">{rating:.1f}</span>
      <span style="color:var(--muted);font-weight:600;">{reviews:,} ratings</span>
    </div>
    <div class="sr-pd-price">
      <span class="now">₹{price:,.0f}</span>
      <span class="was">₹{mrp:,.0f}</span>
      <span class="off">{discount}% OFF</span>
    </div>
    <div style="font-size:0.79rem;color:var(--muted);font-weight:650;">
      Inclusive of all taxes · {stock} units left in the warehouse
    </div>
    <div class="sr-pd-meta">
      <span class="sr-chip">{stock_html}</span>
      <span class="sr-chip">🚚 Delivers in {int(float(product.get('Delivery_Days') or 0))} days</span>
      <span class="sr-chip">🛡️ {product['Warranty']}</span>
      <span class="sr-chip">💵 Cash on delivery</span>
    </div>
    """


def product_offers_html(product):
    """Real offer lines built from the catalogue numbers."""
    price = float(product["Product_Price"])
    mrp = float(product.get("MRP") or 0)
    discount = int(round((1 - price / mrp) * 100)) if mrp > price else 0
    days = int(float(product.get("Delivery_Days") or 0))
    return f"""
    <div class="sr-offer">🏷️ <span><b>Bank offer:</b> extra {min(discount, 20)}% off with
      any debit card on orders above ₹999</span></div>
    <div class="sr-offer">🎁 <span><b>Bundle deal:</b> buy this {product['Product_Category'].lower()} product
      and get free delivery plus a 30-day easy return</span></div>
    <div class="sr-offer">⚡ <span><b>Limited deal:</b> {discount}% off today —
      price drops from ₹{mrp:,.0f} to ₹{price:,.0f}</span></div>
    <div class="sr-offer">🚚 <span><b>Express shipping:</b> arrives in about {days} days
      with cash on delivery available</span></div>
    """


def product_highlights_html(product):
    """The bullet list of highlights, straight from products.csv."""
    items = "".join(
        f'<div class="sr-highlight"><span class="tick">✓</span><span>{point}</span></div>'
        for point in (product.get("Highlights") or "").split(" | ")
        if point.strip()
    )
    return items


def product_trust_html(product):
    """Return / replacement / payment / seller blocks."""
    return f"""
    <div class="sr-trust">
      <div class="t"><div class="h">↩️ 7-day easy returns</div>
        <div class="d">Return it if you do not like it</div></div>
      <div class="t"><div class="h">🛡️ {product['Warranty']}</div>
        <div class="d">Covered by the brand</div></div>
      <div class="t"><div class="h">🔒 Secure payment</div>
        <div class="d">UPI, cards and COD</div></div>
      <div class="t"><div class="h">🏪 Sold by SMARTREC</div>
        <div class="d">Genuine products only</div></div>
    </div>
    """


def cart_line_html(line, product, money_text):
    """One row of the cart page: picture, name, options, line total."""
    return f"""
    <div style="display:flex;gap:15px;align-items:center;">
      <div style="width:104px;min-width:104px;">
        <div class="sr-cover">
          <img src="{product_image_source(product)}"
               alt="{product['Product_Name']}" />
        </div>
      </div>
      <div style="flex:1;min-width:0;">
        <div class="sr-cart-name">{product['Product_Name']}</div>
        <div class="sr-cart-meta">
          {product['Product_Category']} · {product['Brand']}
          {f" · {line['Colour']}" if line.get("Colour") else ""}
          {f" · {line['Size']}" if line.get("Size") else ""}
        </div>
        <div class="sr-cart-meta">Added on {line['Added_On']}</div>
      </div>
      <div style="text-align:right;">
        <div class="sr-cart-line-total">{money_text}</div>
        <div class="sr-cart-meta">₹{float(line['Unit_Price']):,.0f} × {int(line['Quantity'])}</div>
      </div>
    </div>
    """


def cart_summary_html(totals, money):
    """The order summary panel with the real totals from cart.csv."""
    delivery_text = "FREE" if totals["delivery"] == 0 else money(totals["delivery"])
    rows = [
        f'<div class="sr-summary-row"><span>Subtotal ({totals["units"]} unit(s))</span>'
        f"<span>{money(totals['subtotal'])}</span></div>",
        f'<div class="sr-summary-row"><span>Delivery</span><span>{delivery_text}</span></div>',
    ]
    if totals["savings"] > 0:
        rows.append(
            f'<div class="sr-summary-row"><span>Discount saved</span>'
            f'<span class="save">− {money(totals["savings"])}</span></div>'
        )
    rows.append(
        f'<div class="sr-summary-row grand"><span>Total payable</span>'
        f"<span>{money(totals['total'])}</span></div>"
    )
    return "".join(rows)


def empty_cart_html(title, description):
    """The empty-state card shown when the cart has nothing in it."""
    return f"""
    <div class="sr-card sr-empty">
      <div class="icon">🛒</div>
      <div class="h">{title}</div>
      <div class="d">{description}</div>
    </div>
    """

# ---------------------------------------------------------------------------
# 8. ADMIN PANEL BUILDERS
# ---------------------------------------------------------------------------


def admin_login_html():
    """The heading of the separate admin login screen."""
    return """
    <div style="text-align:center;">
      <span class="sr-admin-badge">⚙️ Restricted area</span>
      <div class="sr-admin-title">⚙️ Admin Panel</div>
      <div class="sr-admin-sub">Product and customer management for SMARTREC</div>
    </div>
    """


def admin_header_html(total_products, admin_added):
    """The heading shown at the top of the Admin Panel."""
    return f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;
                gap:18px;flex-wrap:wrap;">
      <div style="min-width:0;">
        <span class="sr-admin-badge">⚙️ Admin Panel</span>
        <div class="sr-admin-title">Product &amp; Customer Management</div>
        <div class="sr-admin-sub">
          Manage products and customer accounts. Changes are saved to the local CSV files.
        </div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin-top:20px;">
      <div class="sr-admin-stat"><span class="v">{total_products}</span><span class="l">Products</span></div>
      <div class="sr-admin-stat"><span class="v">{admin_added}</span><span class="l">Added by admin</span></div>
      <div class="sr-admin-stat"><span class="v">live</span><span class="l">Saved to CSV</span></div>
    </div>
    """


def admin_table_head_html():
    """The column titles that sit above the catalogue rows."""
    return (
        '<div class="sr-admin-head">'
        '<span>Product ID</span><span>Product name</span>'
        '<span>Category</span><span>Price</span><span>Edit</span>'
        "</div>"
    )


def admin_row_cells(product, money):
    """
    The four read-only cells of one catalogue row, as HTML strings.

    Streamlit cannot put a real button inside an HTML table, so the row is built
    with normal Streamlit columns and this only draws the text cells. That way
    the Edit button is a real button sitting inside the same row.
    """
    product_id = str(product["Product_ID"])
    new_tag = '<span class="sr-admin-new">NEW</span>' if product_id.startswith("PRD-") else ""
    return [
        f'<span class="sr-admin-id">{product_id}</span>',
        f'<span class="sr-admin-name">{product["Product_Name"]} {new_tag}</span>',
        f'<span class="sr-admin-cat">{product["Product_Category"]}</span>',
        f'<span class="sr-admin-price">{money(product["Product_Price"])}</span>',
    ]


def admin_note_html(message):
    """A short grey line, used for "nothing matched" and "showing 40 of 61"."""
    return f'<div class="sr-admin-foot">{message}</div>'


def admin_empty_html():
    return (
        '<div class="sr-admin-empty">'
        "No products matched that search. Try a different name or category."
        "</div>"
    )


def marketplace_unavailable_html():
    """Shown when a product has no stored marketplace listings at all."""
    return (
        '<div class="sr-mp-plain">'
        "<div class=\"sr-mp-plain-title\">🛍️ Where to buy</div>"
        '<div class="sr-mp-plain-text">Marketplace availability is currently '
        "unavailable.</div>"
        '<div class="sr-mp-plain-note">We only show a store after someone has '
        "added its real price and product link to SMARTREC's data file. Nothing "
        "is invented, and no price is ever claimed to be live.</div>"
        "</div>"
    )


def marketplace_html(entries, money):
    """
    The full "Where to Buy" box: every stored listing for one product, sorted
    from the cheapest to the dearest. The cheapest row is highlighted as the
    BEST PRICE. Each BUY NOW button is a real link that opens that store's
    product page in a new browser tab.
    """
    medals = ["🥇", "🥈", "🥉"]
    cards = ""
    for index, (_, row) in enumerate(entries.iterrows()):
        price_value = float(row["Price"])
        is_best = index == 0
        medal = medals[index] if index < len(medals) else f"<b>{index + 1}</b>"
        best_tag = (
            '<div class="sr-mp-best-tag">🏷️ BEST PRICE</div>' if is_best else ""
        )
        cards += (
            f'<div class="sr-mp-row{" best" if is_best else ""}">'
            f'<div class="sr-mp-rank">{medal}</div>'
            f'<div class="sr-mp-store"><div class="sr-mp-name">{row["Platform"]}</div>'
            f"{best_tag}</div>"
            f'<div class="sr-mp-price">{money(price_value)}</div>'
            f'<a class="sr-mp-buy" href="{row["Product_URL"]}" target="_blank" '
            f'rel="noopener">BUY NOW ↗</a></div>'
        )

    checked = entries["Checked_On"].dropna()
    note = ""
    if len(checked) > 0:
        note = (
            f'<div class="sr-mp-checked">Prices are stored in SMARTREC\'s '
            f"marketplace file, not live. Last checked: <b>{checked.max()}</b>.</div>"
        )

    return f'<div class="sr-mp-box">{cards}{note}</div>'



def admin_result_html(kind, message):
    """A small success or error strip shown after an add or an edit."""
    if kind == "ok":
        return f'<div class="sr-admin-result ok">✅ {message}</div>'
    return f'<div class="sr-admin-result bad">⚠️ {message}</div>'
