"""Global CSS/HTML design system — palette, fonts, page headers, KPI cards, sidebar/navbar chrome.

Streamlit doesn't execute <script> tags injected via st.markdown, so a Tailwind CDN JIT
compiler can't run reliably here. Instead this module ships a static CSS "design system"
using AZIL Insurance's actual brand tokens (colors + fonts), copied from AZIL-FRONTEND's
Tailwind v4 theme at src/styles/global.css, so this dashboard looks like it belongs to
the same product family.
"""
from __future__ import annotations

import streamlit as st

# --- Brand palette (from AZIL-FRONTEND src/styles/global.css @theme block) ---
BRAND_900 = "#0A0F2C"
BRAND_800 = "#0D1535"
BRAND_700 = "#101C42"
BRAND_600 = "#0D2E5C"
BRAND_500 = "#084887"
BRAND_400 = "#2F8F9D"
BRAND_300 = "#59AEB8"
BRAND_200 = "#8CC8CF"
BRAND_100 = "#D6EEF1"

ACCENT = "#C48A3A"
ACCENT_HOVER = "#D4983F"
ACCENT_GLOW = "#E8C078"
ACCENT_MUTED = "#F5E6CC"
ACCENT_RED = "#C23B3B"
ACCENT_RED_HOVER = "#A83030"

TEAL_500 = "#2F8F9D"
TEAL_400 = "#59AEB8"
TEAL_300 = "#8CC8CF"

NEUTRAL_100 = "#F7F5FB"
NEUTRAL_200 = "#EDEBF5"
NEUTRAL_300 = "#D8D6E3"
NEUTRAL_400 = "#B0ADBE"
NEUTRAL_500 = "#7C7A8A"
NEUTRAL_700 = "#3A3847"
NEUTRAL_900 = "#121212"

SUCCESS = "#2E9E6F"
WARNING = "#D48C2F"
ERROR = "#C23B3B"

# Semantic aliases used elsewhere in the app
PRIMARY = BRAND_900
HEADING_COLOR = BRAND_900
KPI_VALUE_COLOR = BRAND_600

_GOOGLE_FONTS_LINK = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400..700&family=Chivo+Mono:wght@400;600&display=swap" rel="stylesheet">
"""

_CSS = f"""
<style>
    html, body, [class*="css"] {{ font-family: 'Instrument Sans', sans-serif; }}
    code, pre {{ font-family: 'Chivo Mono', ui-monospace, monospace; }}

    [data-testid="stMetricValue"] {{ color: {KPI_VALUE_COLOR}; }}
    h1, h2, h3 {{ color: {HEADING_COLOR}; }}

    /* ---- Sidebar: styled after AZIL-FRONTEND's admin SideNav (bg-brand-700) ---- */
    [data-testid="stSidebar"] {{
        background-color: {BRAND_700};
    }}
    [data-testid="stSidebar"] * {{ color: rgba(255, 255, 255, 0.85); }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{ color: #ffffff; }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(255, 255, 255, 0.12); }}

    /* Custom nav rows — built via st.page_link() + st.container(key=...) since the
       automatic st.navigation() widget can't be reordered relative to our own sidebar
       content. Active/inactive state is decided in Python (nav.py), not guessed in CSS. */
    [class*="st-key-azmnavitem"] {{ border-radius: 0.75rem; margin: 0.1rem 0; transition: background-color 0.15s ease; }}
    [class*="st-key-azmnavitem"]:hover {{ background-color: rgba(255, 255, 255, 0.1); }}
    [class*="st-key-azmnavitem"] [data-testid="stPageLink"] p {{ color: rgba(255, 255, 255, 0.75); font-size: 0.92rem; }}
    [class*="st-key-azmnavitem"]:hover [data-testid="stPageLink"] p {{ color: #ffffff; }}

    [class*="st-key-azmnavactive"] {{
        border-radius: 0.75rem;
        margin: 0.1rem 0;
        background: linear-gradient(to right, {BRAND_600}, {BRAND_500});
        box-shadow: 0 4px 10px rgba(10, 15, 44, 0.25);
    }}
    [class*="st-key-azmnavactive"] [data-testid="stPageLink"] p {{ color: #ffffff; font-weight: 600; font-size: 0.92rem; }}

    /* Logged-in identity card + logout row */
    .azm-sidebar-user-card {{
        border-radius: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(255, 255, 255, 0.06);
        padding: 0.75rem 0.9rem;
        margin: 0.5rem 0;
    }}
    .azm-sidebar-user-card .azm-user-card-label {{
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 0.5rem;
    }}
    .azm-sidebar-user-card .azm-user-row {{ display: flex; align-items: center; gap: 0.6rem; }}
    .azm-sidebar-user-card .azm-user-avatar-wrap {{ position: relative; display: inline-flex; flex-shrink: 0; }}
    .azm-sidebar-user-card .azm-user-avatar {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 9999px;
        background: {BRAND_100};
        color: {BRAND_700};
        font-weight: 700;
        font-size: 0.85rem;
    }}
    .azm-sidebar-user-card .azm-user-status-dot {{
        position: absolute;
        bottom: 0;
        right: 0;
        width: 8px;
        height: 8px;
        border-radius: 9999px;
        background: {SUCCESS};
        border: 2px solid {BRAND_700};
    }}
    .azm-sidebar-user-card .azm-user-name {{ color: #ffffff; font-weight: 600; font-size: 0.9rem; line-height: 1.2; }}
    .azm-sidebar-user-card .azm-user-email {{ color: rgba(255, 255, 255, 0.55); font-size: 0.75rem; }}

    [class*="st-key-azm_logout"] button {{
        background: transparent !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.75) !important;
        justify-content: flex-start !important;
        padding-left: 0 !important;
    }}
    [class*="st-key-azm_logout"] button p {{ color: inherit !important; }}
    [class*="st-key-azm_logout"] button:hover,
    [class*="st-key-azm_logout"] button:focus {{
        background: rgba(255, 255, 255, 0.14) !important;
        color: #ffffff !important;
    }}
    [class*="st-key-azm_logout"] button:hover p,
    [class*="st-key-azm_logout"] button:focus p {{ color: #ffffff !important; }}

    /* Date-range inputs: force a light, legible input surface — Streamlit's own hover/focus
       states can otherwise turn the field white while our blanket sidebar text stays white too. */
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {{
        background-color: #ffffff !important;
        color: {BRAND_900} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stDateInput"] label p {{
        color: rgba(255, 255, 255, 0.75) !important;
    }}

    .azm-sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.25rem 0 1rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 0.75rem;
    }}
    .azm-sidebar-brand .azm-logo-mark {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        background: linear-gradient(135deg, {BRAND_500}, {TEAL_400}, {ACCENT});
        font-size: 1.3rem;
    }}
    .azm-sidebar-brand .azm-wordmark {{
        font-family: 'Instrument Sans', sans-serif;
        font-size: 19px;
        font-weight: 600;
        color: {TEAL_400};
        line-height: 1.1;
    }}
    .azm-sidebar-brand .azm-wordmark b {{ color: #ffffff; font-weight: 700; }}
    .azm-sidebar-brand .azm-tagline {{
        margin-top: 2px;
        font-size: 9px;
        font-weight: 500;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.6);
    }}

    /* ---- Top navbar: styled after AZIL-FRONTEND's admin Header ---- */
    .azm-navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid {NEUTRAL_300};
        padding: 0.3rem 0.1rem;
        margin-bottom: 0.5rem;
    }}
    .azm-navbar .azm-welcome {{
        font-size: 0.85rem;
        font-weight: 500;
        color: {BRAND_700};
    }}
    .azm-navbar .azm-welcome b {{ color: {BRAND_900}; font-weight: 600; }}
    .azm-navbar .azm-profile {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .azm-navbar .azm-avatar-wrap {{ position: relative; display: inline-flex; }}
    .azm-navbar .azm-avatar {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 9999px;
        background: {BRAND_100};
        color: {BRAND_700};
        font-weight: 700;
        font-size: 0.7rem;
    }}
    .azm-navbar .azm-profile-name {{ font-weight: 500; color: {BRAND_900}; font-size: 0.8rem; }}
    .azm-navbar .azm-status-dot {{
        position: absolute;
        bottom: 0;
        right: 0;
        width: 7px;
        height: 7px;
        border-radius: 9999px;
        background: {SUCCESS};
        border: 2px solid #ffffff;
    }}

    /* Page header */
    .azm-page-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }}
    .azm-page-header .azm-icon {{ font-size: 1.9rem; line-height: 1; }}
    .azm-page-title {{ font-size: 1.9rem; font-weight: 700; color: {HEADING_COLOR}; margin: 0; line-height: 1.2; }}
    .azm-page-subtitle {{ color: {NEUTRAL_500}; font-size: 0.9rem; margin-top: 0.15rem; }}

    /* KPI cards */
    .azm-kpi-card {{
        border-radius: 0.75rem;
        border: 1px solid {NEUTRAL_200};
        padding: 1.1rem 1.25rem;
        box-shadow: 0 1px 2px rgba(10, 15, 44, 0.05);
        background: linear-gradient(to bottom right, var(--azm-grad-from, {NEUTRAL_100}), #ffffff);
        height: 100%;
    }}
    .azm-kpi-label {{
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {NEUTRAL_500};
        margin-bottom: 0.4rem;
    }}
    .azm-kpi-value {{ font-size: 1.75rem; font-weight: 700; color: {KPI_VALUE_COLOR}; }}
    .azm-kpi-sub {{ font-size: 0.75rem; color: {NEUTRAL_500}; margin-top: 0.3rem; }}

    /* Badges */
    .azm-badge {{
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 600;
    }}
    .azm-badge-success {{ background: rgba(46, 158, 111, 0.14); color: {SUCCESS}; }}
    .azm-badge-warning {{ background: rgba(212, 140, 47, 0.14); color: {WARNING}; }}
    .azm-badge-danger {{ background: rgba(194, 59, 59, 0.12); color: {ERROR}; }}
    .azm-badge-neutral {{ background: {NEUTRAL_200}; color: {NEUTRAL_700}; }}

    /* ---- Login page: modeled on AZIL-FRONTEND's real client login
       (src/modules/client/dashboard/login/index.tsx) — a split navy/gradient hero
       banner with a floating white card overlapping both halves, rather than a
       boxed two-column card. ---- */
    .azm-login-hero {{
        display: flex;
        min-height: 320px;
        border-radius: 1.25rem;
        overflow: hidden;
    }}
    .azm-login-hero-left {{
        flex: 1;
        background: {BRAND_900};
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 3rem 3rem;
    }}
    .azm-login-hero-eyebrow {{
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.32em;
        color: rgba(255, 255, 255, 0.7);
    }}
    .azm-login-hero-title {{
        margin-top: 1rem;
        font-size: 2.75rem;
        font-weight: 700;
        line-height: 1.15;
        color: #ffffff;
    }}
    .azm-login-hero-desc {{
        margin-top: 1.25rem;
        font-size: 1rem;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.78);
        max-width: 26rem;
    }}
    .azm-login-hero-right {{
        flex: 1;
        position: relative;
        background: linear-gradient(135deg, {BRAND_700}, {BRAND_500});
    }}
    .azm-login-hero-dots {{
        position: absolute;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 0.5rem;
    }}
    .azm-login-hero-dot {{ width: 8px; height: 8px; border-radius: 9999px; background: rgba(255, 255, 255, 0.45); }}
    .azm-login-hero-dot.active {{ width: 28px; background: #ffffff; }}

    [class*="st-key-azm_login_card_wrap"] {{
        margin-top: -230px;
        position: relative;
        z-index: 2;
        display: flex;
        justify-content: center;
        padding: 0 1rem;
    }}
    [class*="st-key-azm_login_card"] {{
        width: 100%;
        max-width: 46rem;
        min-height: 460px;
        margin: 0 auto;
        border-radius: 2rem;
        border: 1px solid {NEUTRAL_300};
        background: #ffffff;
        box-shadow: 0 20px 60px rgba(10, 15, 44, 0.15);
        padding: 2.5rem 3.5rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .azm-login-brand {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        margin-bottom: 1.5rem;
    }}
    .azm-login-brand .azm-logo-mark {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, {BRAND_500}, {TEAL_400}, {ACCENT});
        font-size: 1.3rem;
    }}
    .azm-login-brand .azm-wordmark {{
        font-family: 'Instrument Sans', sans-serif;
        font-size: 19px;
        font-weight: 600;
        color: {BRAND_600};
        line-height: 1.1;
        text-align: left;
    }}
    .azm-login-brand .azm-wordmark b {{ color: {BRAND_900}; font-weight: 700; }}
    .azm-login-brand .azm-tagline {{
        margin-top: 2px;
        font-size: 9px;
        font-weight: 500;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: {NEUTRAL_500};
    }}

    .azm-login-eyebrow {{
        text-align: center;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3em;
        color: {ACCENT};
    }}
    .azm-login-heading2 {{ margin-top: 0.6rem; text-align: center; font-size: 1.7rem; font-weight: 700; color: {BRAND_900}; }}
    .azm-login-subtext2 {{ margin-top: 0.5rem; text-align: center; font-size: 0.9rem; color: {NEUTRAL_700}; }}

    [class*="st-key-azm_login_card"] label p {{
        text-transform: uppercase;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        color: {NEUTRAL_500} !important;
    }}
    [class*="st-key-azm_login_card"] input:focus {{ border-color: {BRAND_500} !important; }}
    [class*="st-key-azm_login_card"] button[kind="primary"] {{
        background-color: {BRAND_500} !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
    }}
    [class*="st-key-azm_login_card"] button[kind="primary"]:hover {{ background-color: {BRAND_600} !important; }}
</style>
"""


_LOGIN_MODE_CSS = f"""
<style>
    [data-testid="collapsedControl"] {{ display: none; }}
    .stApp {{ background-color: {NEUTRAL_200}; }}
    .stMainBlockContainer {{ padding-top: 2rem; }}
</style>
"""


def inject_global_css(login_mode: bool = False) -> None:
    """login_mode hides the (otherwise empty) sidebar toggle arrow and swaps the page
    background to the light neutral tone AZIL-FRONTEND's client login page uses."""
    _render_html(_GOOGLE_FONTS_LINK)
    _render_html(_CSS)
    if login_mode:
        _render_html(_LOGIN_MODE_CSS)


def _render_html(html: str) -> None:
    """st.markdown(unsafe_allow_html=True) parses its input as Markdown first. A blank
    line in the middle of an indented multi-line HTML snippet (e.g. when an optional
    fragment like a subtitle is empty) ends CommonMark's raw-HTML-block handling early,
    and the remaining indented lines get reinterpreted as an indented code block —
    leaking a literal "</div>" as visible text instead of being parsed as HTML. Collapsing
    to a single line with no blank lines sidesteps that ambiguity entirely."""
    collapsed = " ".join(line.strip() for line in html.strip().splitlines() if line.strip())
    st.markdown(collapsed, unsafe_allow_html=True)


def sidebar_brand(tagline: str = "Analytics") -> None:
    """Logo/wordmark header shown above the page-nav links, matching AZIL's SideNav.astro."""
    _render_html(
        f"""
        <div class="azm-sidebar-brand">
            <div class="azm-logo-mark">📊</div>
            <div>
                <div class="azm-wordmark">azil <b>Insurance</b></div>
                <div class="azm-tagline">{tagline}</div>
            </div>
        </div>
        """
    )


def sidebar_user_card(name: str | None, email: str | None = None) -> None:
    """'Logged In' identity card shown in the sidebar below the nav links."""
    initial = (name or email or "A")[:1].upper()
    email_html = f'<div class="azm-user-email">{email}</div>' if email else ""
    _render_html(
        f"""
        <div class="azm-sidebar-user-card">
            <div class="azm-user-card-label">Logged In</div>
            <div class="azm-user-row">
                <div class="azm-user-avatar-wrap">
                    <div class="azm-user-avatar">{initial}</div>
                    <span class="azm-user-status-dot"></span>
                </div>
                <div>
                    <div class="azm-user-name">{name or "Admin User"}</div>
                    {email_html}
                </div>
            </div>
        </div>
        """
    )


def topbar(welcome_name: str | None = None) -> None:
    """Top navbar matching AZIL's admin Header.tsx — welcome text + profile chip."""
    welcome = f"Welcome, <b>{welcome_name}</b>" if welcome_name else "Azil Insurance Analytics"
    initial = (welcome_name or "A")[:1].upper()
    _render_html(
        f"""
        <div class="azm-navbar">
            <div class="azm-welcome">{welcome}</div>
            <div class="azm-profile">
                <span class="azm-profile-name">{welcome_name or ""}</span>
                <div class="azm-avatar-wrap">
                    <div class="azm-avatar">{initial}</div>
                    <span class="azm-status-dot"></span>
                </div>
            </div>
        </div>
        """
    )


def page_header(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    """Custom HTML/CSS page header used at the top of every page instead of st.title."""
    icon_html = f'<span class="azm-icon">{icon}</span>' if icon else ""
    subtitle_html = f'<div class="azm-page-subtitle">{subtitle}</div>' if subtitle else ""
    _render_html(
        f"""
        <div class="azm-page-header">
            {icon_html}
            <div>
                <div class="azm-page-title">{title}</div>
                {subtitle_html}
            </div>
        </div>
        """
    )


def login_hero() -> None:
    """Split navy/gradient hero banner above the login form, modeled on AZIL-FRONTEND's
    real client login (src/modules/client/dashboard/login/index.tsx): a brand panel on
    the left and a decorative panel on the right (a static gradient here in place of
    their rotating lifestyle-photo carousel, since we don't have those image assets)."""
    _render_html(
        """
        <div class="azm-login-hero">
            <div class="azm-login-hero-left">
                <div class="azm-login-hero-eyebrow">Analytics Portal</div>
                <div class="azm-login-hero-title">Azil<br>Insurance</div>
                <p class="azm-login-hero-desc">
                    Secure access to real-time policy, payment, and performance analytics.
                </p>
            </div>
            <div class="azm-login-hero-right">
                <div class="azm-login-hero-dots">
                    <span class="azm-login-hero-dot active"></span>
                    <span class="azm-login-hero-dot"></span>
                    <span class="azm-login-hero-dot"></span>
                    <span class="azm-login-hero-dot"></span>
                </div>
            </div>
        </div>
        """
    )


def login_form_header() -> None:
    """Wordmark (matching the sidebar's) + "Sign In" kicker + heading shown at the
    top of the login form card."""
    _render_html(
        """
        <div class="azm-login-brand">
            <div class="azm-logo-mark">📊</div>
            <div>
                <div class="azm-wordmark">azil <b>Insurance</b></div>
                <div class="azm-tagline">Analytics</div>
            </div>
        </div>
        <div class="azm-login-eyebrow">Sign In</div>
        <div class="azm-login-heading2">Let's get you in.</div>
        <div class="azm-login-subtext2">It only takes a moment to continue to your analytics dashboard.</div>
        """
    )


_BADGE_CLASS = {
    "success": "azm-badge-success",
    "warning": "azm-badge-warning",
    "danger": "azm-badge-danger",
    "neutral": "azm-badge-neutral",
}


def badge(text: str, tone: str = "neutral") -> str:
    """Return an inline HTML badge/chip. Embed the result in another st.markdown call."""
    css_class = _BADGE_CLASS.get(tone, _BADGE_CLASS["neutral"])
    return f'<span class="azm-badge {css_class}">{text}</span>'

