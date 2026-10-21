"""Brew & Bites Café — AI-Powered Sales Analytics Dashboard
Project by Chaitanya Jadhav
Run:  streamlit run app.py
"""
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

import cafe_analytics as A

# ================================================================ settings
CAFE = "Brew & Bites Café"
CITY = "Kolhapur"
TAGLINE = "Every cutting chai and vada pav tells a story. This dashboard reads it — sales, menu, customers and what to do next."
AUTHOR = "Chaitanya Jadhav"
LINKEDIN = "https://www.linkedin.com/in/chaitanyatj369344259/"
GITHUB = "https://github.com/chaitanya5711"
EMAIL = "jadhavchaitanya5911@gmail.com"

st.set_page_config(page_title=f"{CAFE} · AI Analytics", page_icon="☕", layout="wide",
                   initial_sidebar_state="expanded")

COFFEE = ["#2c4a3a", "#a87a22", "#6e8b5f", "#c9a35a", "#8fa898", "#5a6860", "#d9c49a", "#3f6b55"]
SCALE = ["#eef1ec", "#c9d4c4", "#8fa898", "#4f6b45", "#2c4a3a"]
px.defaults.color_discrete_sequence = COFFEE

PAGES = {
    "🏠 Home": "Start here",
    "📊 Sales Overview": "Revenue, profit, trends and monthly target",
    "🍽️ Menu Insights": "Best and weak items, menu matrix, item explorer",
    "⏰ Time & Offers": "Peak hours, best days, Tuesday offer, festivals",
    "👥 Orders & Customers": "Dine-in vs apps, payments, ratings, AI segments",
    "🔮 AI Forecast": "Next 60 days of sales and unusual days",
    "🧰 Smart Tools": "Combo ideas and price simulator",
    "💬 AI Chatbot": "Ask questions about the café in plain language",
    "📄 Report & About": "Findings, recommendations and the author",
}

# ================================================================ styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Gloock&family=Hanken+Grotesk:wght@400;500;600;700&family=Tiro+Devanagari+Marathi&display=swap');
:root{--mist:#eef1ec;--paper:#fbfcf9;--ink:#18241e;--hill:#2c4a3a;--moss:#6e8b5f;--brass:#a87a22;
  --brass-soft:#ecdcb6;--chai:#efe4cf;--muted:#5a6860;--line:#d3d9d0;--good:#2f7a45;--bad:#a8402a;
  --display:"Gloock",Georgia,serif;--body:"Hanken Grotesk",system-ui,sans-serif;
  --deva:"Tiro Devanagari Marathi","Kohinoor Devanagari",serif}
html, body, .stApp, [class*="css"], .stMarkdown, p, li, label, button, input {font-family:var(--body);}
#MainMenu, footer, header [data-testid="stToolbar"] {visibility:hidden;}
.stApp{background:var(--mist);color:var(--ink);overflow-x:hidden}
.block-container{padding-top:1.6rem;padding-bottom:0;max-width:1160px}
h1,h2,h3,h4{font-family:var(--display)!important;font-weight:400!important;color:var(--ink);letter-spacing:-.01em}

/* ---------- hero: the one bold moment ---------- */
.hero{padding:18px 0 6px;overflow:hidden;margin-bottom:10px}
.hero-word{position:relative;display:inline-block;font-family:var(--display);color:var(--brass);
  font-size:clamp(3rem,8vw,6.2rem);line-height:1.05;margin-left:-.03em;white-space:nowrap}
.hero-word:after{content:"";position:absolute;left:calc(100% + 14px);top:.55em;width:100vw;height:.055em;
  background:currentColor;border-radius:2px}
.hero h1{font-size:clamp(2.6rem,6vw,4.4rem);line-height:1.05;margin:.1em 0 .25em;color:var(--ink)}
.hero-meaning{font-size:.9rem;color:var(--muted);margin:0 0 14px}
.hero-meaning em{font-family:var(--deva);font-style:normal;color:var(--brass)}
.lede{font-size:1.25rem;line-height:1.5;max-width:46ch;color:#3b4a42;margin:0 0 16px}
.open-now{display:inline-flex;align-items:center;gap:9px;font-weight:600;margin-right:22px}
.open-now:before{content:"";width:9px;height:9px;border-radius:50%;background:var(--good);
  box-shadow:0 0 0 4px rgba(47,122,69,.22)}
.meta{color:var(--muted);font-size:.92rem;margin-right:22px}
.fadein{animation:fade .6s ease both}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* ---------- page header: quiet, left-aligned ---------- */
.page-head{padding:6px 0 14px;margin-bottom:18px;border-bottom:1px solid var(--line)}
.page-head .label{margin-bottom:2px}
.page-head h2{font-size:clamp(2rem,4.2vw,2.8rem);margin:0;line-height:1.08}
.page-head p{margin:4px 0 0;color:var(--muted);font-size:.95rem}
.label{font-size:.875rem;font-weight:600;color:var(--brass);letter-spacing:.01em}

/* ---------- figures: rules instead of boxes ---------- */
.kpi{padding:6px 0 10px 16px;border-left:2px solid var(--line);height:100%;transition:border-color .2s}
.kpi:hover{border-left-color:var(--brass)}
.kpi .lbl{font-size:.875rem;font-weight:600;color:var(--brass)}
.kpi .val{font-family:var(--display);font-size:1.9rem;line-height:1.15;color:var(--ink);
  font-variant-numeric:tabular-nums lining-nums}
.kpi .dl{font-size:.8rem;margin-top:2px}
.up{color:var(--good)}.down{color:var(--bad)}.flat{opacity:.4}

/* ---------- navigation list ---------- */
.nav-card{padding:18px 0 8px;border-top:1px solid var(--line);transition:border-color .2s}
.nav-card:hover{border-top-color:var(--brass)}
.nav-card .ic{font-size:1.4rem}
.nav-card h4{font-size:1.35rem;margin:4px 0 4px}
.nav-card p{margin:0 0 4px;font-size:.9rem;line-height:1.5;color:var(--muted);min-height:3em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

/* ---------- paper objects: cards, slips ---------- */
.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:10px}
.insight{background:var(--chai);border-left:3px solid var(--brass);border-radius:6px;padding:12px 16px;margin:10px 0;
  font-size:.98rem}
.section{font-family:var(--display);font-size:1.7rem;color:var(--ink);margin:26px 0 6px;line-height:1.1}
.author{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:22px}
.author h3{font-size:1.7rem}

/* ---------- footer: ink band ---------- */
.footer{background:var(--ink);color:#c9d0c7;margin:56px -100vw 0;padding:36px 100vw 44px;font-size:.9rem;text-align:left}
.footer .fb{font-family:var(--display);font-size:1.3rem;color:var(--mist)}
.footer .fb span{font-family:var(--deva);color:var(--brass);margin-right:10px}
.footer a{color:var(--mist)!important}

/* ---------- tabs, buttons, inputs ---------- */
.stTabs [data-baseweb="tab-list"]{gap:26px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{background:none;padding:8px 0;color:var(--muted);font-weight:500}
.stTabs [aria-selected="true"]{color:var(--ink)!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--brass)!important;height:2px}
div.stButton > button, div.stDownloadButton > button{border-radius:999px;min-height:44px;padding:0 20px;font-weight:600;
  background:var(--hill);color:#f4f6f1;border:1.5px solid var(--hill);transition:all .15s}
div.stButton > button:hover, div.stDownloadButton > button:hover{background:var(--ink);border-color:var(--ink);color:var(--mist)}
div.stButton > button p{color:inherit}
[data-testid="stAlert"]{border-radius:6px}
.stSlider [role="slider"]{background:var(--brass)!important}

/* ---------- sidebar: tekdi green band ---------- */
section[data-testid="stSidebar"]{background:var(--hill)}
section[data-testid="stSidebar"] *{color:#e9eee7}
section[data-testid="stSidebar"] [role="radiogroup"] label{padding:9px 12px;border-radius:999px;margin:1px 0;width:100%;
  transition:background .15s}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.08)}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--mist)}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) *{color:var(--ink)!important}
section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{display:none}
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="tag"] *{color:var(--ink)}
section[data-testid="stSidebar"] a{color:var(--brass-soft)!important}
section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.15)}
.brand{margin:0;line-height:1.1}
.brand .bm{font-family:var(--deva);font-size:1.55rem;color:#d3a446!important;margin-right:8px}
.brand .bn{font-family:var(--display);font-size:1.35rem;color:#f4f6f1!important}
.brand-sub{font-size:.85rem;color:#b9c7b0!important;margin:2px 0 6px}
/* ---------- force light look even if Streamlit is in dark mode ---------- */
header[data-testid="stHeader"]{background:var(--mist)!important}
[data-testid="stMain"], .main{color:var(--ink)}
[data-testid="stMain"] p, [data-testid="stMain"] li, [data-testid="stMain"] span, [data-testid="stMain"] label,
[data-testid="stMain"] [data-testid="stWidgetLabel"] *, [data-testid="stMain"] [data-testid="stCaptionContainer"] *,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] *, .main p, .main label, .main span{color:var(--ink)}
[data-testid="stMain"] [data-testid="stCaptionContainer"] *{color:var(--muted)!important}
.stTabs [data-baseweb="tab"] p{color:var(--muted)!important;font-weight:500}
.stTabs [aria-selected="true"] p{color:var(--ink)!important;font-weight:600}
[data-testid="stMain"] .kpi .lbl, [data-testid="stMain"] .label{color:var(--brass)!important}
[data-testid="stMain"] .up{color:var(--good)!important}[data-testid="stMain"] .down{color:var(--bad)!important}
[data-testid="stMain"] .hero-word, [data-testid="stMain"] .hero-meaning em{color:var(--brass)!important}
[data-testid="stMain"] .footer, [data-testid="stMain"] .footer *{color:#c9d0c7!important}
[data-testid="stMain"] .footer .fb{color:var(--mist)!important}
[data-testid="stMain"] .footer .fb span{color:var(--brass)!important}
[data-testid="stMain"] div.stButton > button *, [data-testid="stMain"] div.stDownloadButton > button *{color:#f4f6f1!important}
[data-testid="stMain"] input, [data-testid="stMain"] textarea, [data-baseweb="select"] > div{background:var(--paper)!important;
  color:var(--ink)!important}
[data-testid="stMain"] [data-testid="stExpander"] details, [data-testid="stFileUploaderDropzone"]{background:var(--paper)!important}
[data-testid="stChatMessage"]{background:var(--paper);border:1px solid var(--line);border-radius:10px}
.stSlider [data-baseweb="slider"] div[role="slider"]{background:var(--brass)!important;border-color:var(--brass)!important}
.stSlider [data-testid="stSliderThumbValue"], .stSlider [data-testid="stThumbValue"]{color:var(--brass)!important}
.block-container{padding-top:3.4rem!important}
/* sidebar radio: hide the round dot, keep the pill */
section[data-testid="stSidebar"] [role="radiogroup"] label > div:not(:has(p)){display:none!important}
/* hide Streamlit's automatic link icons next to headings */
[data-testid="stHeaderActionElements"], .nav-card h4 a, .section a, .page-head h2 a{display:none!important}
section[data-testid="stSidebar"] [role="radiogroup"] input{display:none}
section[data-testid="stSidebar"] [data-testid="stExpander"] details{background:rgba(255,255,255,.05);
  border-color:rgba(255,255,255,.15)}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.06)!important}
</style>""", unsafe_allow_html=True)


# ================================================================ helpers
@st.cache_data
def load(path):
    return A.load_data(path)


def show(fig, height=380):
    ink, muted, line = "#18241e", "#5a6860", "#d3d9d0"
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=55, b=10),
                      font=dict(family="Hanken Grotesk, sans-serif", color=ink, size=13),
                      title_font=dict(family="Gloock, Georgia, serif", size=19, color=ink),
                      legend=dict(font=dict(color=ink)), hoverlabel=dict(font_family="Hanken Grotesk"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=COFFEE)
    fig.update_xaxes(gridcolor=line, linecolor=line, tickfont=dict(color=muted), title_font=dict(color=muted))
    fig.update_yaxes(gridcolor=line, linecolor=line, tickfont=dict(color=muted), title_font=dict(color=muted))
    st.plotly_chart(fig, use_container_width=True, theme=None)


def rupee(x):
    return f"₹{x:,.0f}"


def kpi_card(col, icon, label, value, change=None, suffix="% vs prev period"):
    if change is None:
        dl = "<span class='flat'>&nbsp;</span>"
    else:
        cls, arrow = ("up", "▲") if change >= 0 else ("down", "▼")
        dl = f"<span class='{cls}'>{arrow} {abs(change):.1f}{suffix}</span>"
    col.markdown(f"<div class='kpi fadein'><div class='lbl'>{icon} {label}</div>"
                 f"<div class='val'>{value}</div><div class='dl'>{dl}</div></div>", unsafe_allow_html=True)


def section(title, sub=None):
    st.markdown(f"<div class='section'>{title}</div>", unsafe_allow_html=True)
    if sub:
        st.caption(sub)


def page_header(page):
    icon, title = page.split(" ", 1)
    st.markdown(f"<div class='page-head fadein'><div class='label'>{icon} {CAFE} · {CITY}</div><h2>{title}</h2>"
                f"<p>{PAGES[page]} · {start:%d %b %Y} – {end:%d %b %Y}</p></div>", unsafe_allow_html=True)


def go_to(page):
    st.session_state.page = page


def insight_box(text):
    st.markdown(f"<div class='insight'>{text.replace('**', '')}</div>", unsafe_allow_html=True)


# ================================================================ sidebar
if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

with st.sidebar:
    st.markdown(f"<p class='brand'><span class='bn'>{CAFE}</span></p>", unsafe_allow_html=True)
    st.markdown(f"<p class='brand-sub'>Sales analytics · {CITY}</p>", unsafe_allow_html=True)
    st.radio("Navigate", list(PAGES), key="page", label_visibility="collapsed")
    st.markdown("---")

with st.sidebar:
    with st.expander("📅 Date & data filters", expanded=st.session_state.page != "🏠 Home"):
        up = st.file_uploader("Upload cleaned sales CSV (optional)", type="csv")
        df_all = load(up if up is not None else "cafe_clean.csv")
        dmin, dmax = df_all["date"].min().date(), df_all["date"].max().date()
        all_ot = sorted(df_all["order_type"].unique())
        all_cat = sorted(df_all["category"].unique())
        all_pay = sorted(df_all["payment_method"].unique())
        quick = st.radio("Period", ["All", "Last 30 days", "Last 7 days", "Custom"], horizontal=True)
        if quick == "Last 30 days":
            start, end = max(dmin, dmax - pd.Timedelta(days=29)), dmax
        elif quick == "Last 7 days":
            start, end = max(dmin, dmax - pd.Timedelta(days=6)), dmax
        elif quick == "Custom":
            dr = st.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
            start, end = dr if isinstance(dr, (list, tuple)) and len(dr) == 2 else (dmin, dmax)
        else:
            start, end = dmin, dmax
        otypes = st.multiselect("Order type", all_ot, all_ot)
        cats = st.multiselect("Category", all_cat, all_cat)
        pays = st.multiselect("Payment method", all_pay, all_pay)
        hours = st.slider("Hours of day", 7, 22, (7, 22))
    with st.expander("⚙️ Settings"):
        target = st.number_input("Monthly revenue target (₹)", 10000, 1000000, 60000, step=5000)
        api_key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""),
                                help="Free key at aistudio.google.com. Without it, the bot answers basic questions.")
        model_name = st.text_input("Gemini model", "gemini-2.5-flash")
    st.markdown("---")
    st.markdown(f"<small>👨‍💻 Built by <b>{AUTHOR}</b><br>"
                f"<a href='{LINKEDIN}' target='_blank'>LinkedIn</a> · "
                f"<a href='{GITHUB}' target='_blank'>GitHub</a></small>", unsafe_allow_html=True)


def apply_filters(d):
    return d[d["order_type"].isin(otypes) & d["category"].isin(cats)
             & d["payment_method"].isin(pays) & d["hour"].between(*hours)]


df = apply_filters(df_all[(df_all["date"].dt.date >= start) & (df_all["date"].dt.date <= end)])
page = st.session_state.page

if df.empty:
    st.warning("No data for these filters. Open 'Date & data filters' in the sidebar and widen them.")
    st.stop()

span = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
prev = apply_filters(df_all[(df_all["date"] >= pd.Timestamp(start) - pd.Timedelta(days=span))
                            & (df_all["date"] < pd.Timestamp(start))])
k = A.kpis(df)
kp = A.kpis(prev) if not prev.empty else None


def chg(key):
    if kp is None or not kp[key]:
        return None
    return (k[key] / kp[key] - 1) * 100


# ================================================================ pages
def page_home():
    st.markdown(f"""<div class='hero fadein'>
<div class='hero-word'>{CAFE}</div>
<p class='hero-meaning'>A neighbourhood café in {CITY}</p>
<p class='lede'>{TAGLINE}</p>
<span class='open-now'>Analytics live</span><span class='meta'>📍 {CITY}</span>
<span class='meta'>{dmin:%b} – {dmax:%b %Y}</span><span class='meta'>Project by {AUTHOR}</span>
</div>""", unsafe_allow_html=True)

    c = st.columns(4)
    kpi_card(c[0], "💰", "Total revenue", rupee(k["revenue"]))
    kpi_card(c[1], "🧾", "Bills served", f"{k['bills']:,}")
    kpi_card(c[2], "🛍️", "Average bill", rupee(k["avg_bill"]))
    kpi_card(c[3], "⭐", "App rating", f"{k['rating']:.1f} / 5" if pd.notna(k["rating"]) else "–")

    st.write("")
    section("Explore the dashboard")
    names = [p for p in PAGES if p != "🏠 Home"]
    for row in range(0, len(names), 4):
        cols = st.columns(4)
        for col, p in zip(cols, names[row:row + 4]):
            icon, title = p.split(" ", 1)
            with col:
                st.markdown(f"<div class='nav-card fadein'><div class='ic'>{icon}</div><h4>{title}</h4>"
                            f"<p>{PAGES[p]}</p></div>", unsafe_allow_html=True)
                st.button("Open", key=f"nav_{p}", on_click=go_to, args=(p,), use_container_width=True)
        st.write("")

    section("Today's top insights")
    for s in A.auto_insights(df)[:3]:
        insight_box(s)


def page_overview():
    c = st.columns(5)
    kpi_card(c[0], "💰", "Revenue", rupee(k["revenue"]), chg("revenue"))
    kpi_card(c[1], "📈", "Profit", rupee(k["profit"]), chg("profit"))
    kpi_card(c[2], "🧾", "Bills", f"{k['bills']:,}", chg("bills"))
    kpi_card(c[3], "🛍️", "Avg bill", rupee(k["avg_bill"]), chg("avg_bill"))
    kpi_card(c[4], "📦", "Items sold", f"{k['items_sold']:,}", chg("items_sold"))
    st.write("")
    t1, t2, t3 = st.tabs(["📈 Trend", "🎯 Target", "🥧 Breakdown"])
    with t1:
        d = A.daily_series(df)
        metric = st.radio("Show", ["revenue", "profit", "bills"], horizontal=True, format_func=str.title)
        fig = go.Figure()
        fig.add_bar(x=d["date"], y=d[metric], name=f"Daily {metric}", marker_color="#b9c7b0",
                    hovertemplate="%{x|%a %d %b}<br>%{y:,.0f}<extra></extra>")
        fig.add_scatter(x=d["date"], y=d[metric].rolling(7, min_periods=1).mean(), name="7-day average",
                        line=dict(color="#a87a22", width=3))
        for s, e, name in A.FESTIVALS:
            if pd.Timestamp(s) <= d["date"].max() and pd.Timestamp(e) >= d["date"].min():
                fig.add_vrect(x0=s, x1=e, fillcolor="#6e8b5f", opacity=0.12, line_width=0,
                              annotation_text=f"🎉 {name}", annotation_position="top left")
        fig.update_layout(title=f"Daily {metric} with 7-day trend", legend=dict(orientation="h", y=1.12),
                          xaxis=dict(rangeslider=dict(visible=True), type="date"))
        show(fig, 450)
        mo = df.groupby(df["date"].dt.to_period("M")).agg(Revenue=("line_total", "sum"),
                                                           Profit=("profit", "sum")).reset_index()
        mo["date"] = mo["date"].dt.strftime("%b %Y")
        show(px.bar(mo, x="date", y=["Revenue", "Profit"], barmode="group", title="Monthly revenue vs profit",
                    labels={"value": "₹", "date": "", "variable": ""}, text_auto=".2s"), 340)
    with t2:
        mo = df.groupby(df["date"].dt.to_period("M"))["line_total"].sum()
        cur = mo.iloc[-1] if len(mo) else 0
        top = max(target, cur) * 1.2
        g = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=cur, number={"prefix": "₹", "valueformat": ",.0f"},
            delta={"reference": target, "valueformat": ",.0f", "prefix": "₹"},
            title={"text": f"{mo.index[-1].strftime('%B %Y') if len(mo) else ''} vs target"},
            gauge={"axis": {"range": [0, top]}, "bar": {"color": "#a87a22"},
                   "steps": [{"range": [0, target * .7], "color": "rgba(168,64,42,.12)"},
                             {"range": [target * .7, target], "color": "rgba(236,220,182,.6)"},
                             {"range": [target, top], "color": "rgba(110,139,95,.22)"}],
                   "threshold": {"line": {"color": "#2c4a3a", "width": 4}, "value": target}}))
        c1, c2 = st.columns([1.4, 1])
        with c1:
            show(g, 340)
        with c2:
            pct = cur / target * 100 if target else 0
            st.write("")
            st.progress(min(pct / 100, 1.0), text=f"{pct:.0f}% of monthly target")
            tm = pd.DataFrame({"Month": mo.index.strftime("%b %Y"), "Revenue": mo.values})
            tm["Hit target"] = tm["Revenue"].apply(lambda v: "✅" if v >= target else "❌")
            st.dataframe(tm, hide_index=True, use_container_width=True,
                         column_config={"Revenue": st.column_config.NumberColumn(format="₹%d")})
            st.caption("Change the target under ⚙️ Settings in the sidebar.")
    with t3:
        c1, c2 = st.columns(2)
        with c1:
            ot = df.groupby("order_type")["line_total"].sum().reset_index()
            show(px.pie(ot, names="order_type", values="line_total", hole=.6, title="Revenue by order type"), 360)
        with c2:
            ct = df.groupby("category")["line_total"].sum().reset_index()
            show(px.pie(ct, names="category", values="line_total", hole=.6, title="Revenue by category"), 360)


def page_menu():
    me, pop_cut, mar_cut = A.menu_engineering(df)
    t1, t2, t3 = st.tabs(["⭐ Menu matrix", "🏆 Top items", "🔍 Item explorer"])
    with t1:
        st.caption("Each item placed by popularity (units sold) and profit per unit. Click legend to filter.")
        fig = px.scatter(me, x="qty", y="profit_per_unit", size="revenue", color="class", text="item",
                         hover_data={"revenue": ":,.0f", "profit": ":,.0f", "action": True},
                         labels={"qty": "Units sold", "profit_per_unit": "Profit per unit (₹)"},
                         color_discrete_map={"⭐ Star": "#a87a22", "🐴 Plowhorse": "#5a6860",
                                             "🧩 Puzzle": "#6e8b5f", "🐶 Dog": "#a8402a"})
        fig.add_vline(x=pop_cut, line_dash="dash", line_color="grey")
        fig.add_hline(y=mar_cut, line_dash="dash", line_color="grey")
        fig.update_traces(textposition="top center", textfont_size=10)
        show(fig, 500)
        advice = {"⭐ Star": "Keep & feature", "🐴 Plowhorse": "Small price rise",
                  "🧩 Puzzle": "Promote more", "🐶 Dog": "Rework or remove"}
        cc = st.columns(4)
        for col, cl in zip(cc, advice):
            items = me.loc[me["class"] == cl, "item"].tolist()
            col.markdown(f"<div class='card'><b>{cl}</b> · {len(items)}<br><small><i>{advice[cl]}</i></small>"
                         f"<br><small>{', '.join(items) if items else '—'}</small></div>", unsafe_allow_html=True)
    with t2:
        c1, c2 = st.columns(2)
        n = c1.slider("How many items?", 5, 25, 10)
        rank_by = c2.radio("Rank by", ["profit", "revenue", "qty"], horizontal=True,
                           format_func=lambda x: {"qty": "Units sold"}.get(x, x.title()))
        top = me.nlargest(n, rank_by).sort_values(rank_by)
        show(px.bar(top, x=rank_by, y="item", orientation="h", color="category", text_auto=",.0f",
                    title=f"Top {n} items by {rank_by}", labels={"item": "", rank_by: rank_by.title()}),
             max(360, n * 28))
        show(px.treemap(me, path=["category", "item"], values="revenue", color="profit_per_unit",
                        color_continuous_scale=SCALE, title="Revenue treemap — click a category to zoom"), 440)
    with t3:
        item_sel = st.selectbox("Choose an item", me.sort_values("revenue", ascending=False)["item"])
        it = df[df["item"] == item_sel]
        r = me[me["item"] == item_sel].iloc[0]
        ic = st.columns(4)
        kpi_card(ic[0], "📦", "Units sold", f"{int(r['qty']):,}")
        kpi_card(ic[1], "💰", "Revenue", rupee(r["revenue"]))
        kpi_card(ic[2], "📈", "Profit", rupee(r["profit"]))
        kpi_card(ic[3], "🏷️", "Class", r["class"])
        st.info(f"Recommended action: {r['action']}")
        c1, c2 = st.columns(2)
        with c1:
            iw = it.groupby(pd.Grouper(key="date", freq="W-MON"))["quantity"].sum().reset_index()
            show(px.line(iw, x="date", y="quantity", markers=True, title="Weekly units",
                         labels={"quantity": "Units", "date": "Week"}), 320)
        with c2:
            ih = it.groupby("hour")["quantity"].sum().reset_index()
            show(px.bar(ih, x="hour", y="quantity", title="Units by hour",
                        labels={"quantity": "Units", "hour": "Hour"}), 320)


def page_time():
    dl = df.groupby(["date", "day_name"])["line_total"].sum().reset_index()
    wk = dl.groupby("day_name")["line_total"].mean().reindex(A.DAYS)
    t1, t2, t3 = st.tabs(["🕒 Peak times", "🏷️ Tuesday offer", "🎉 Festivals"])
    with t1:
        hm = (df.drop_duplicates("invoice_no").groupby(["day_name", "hour"]).size()
              .unstack(fill_value=0).reindex(A.DAYS).fillna(0))
        show(px.imshow(hm, aspect="auto", color_continuous_scale=SCALE, text_auto=True,
                       labels=dict(x="Hour of day", y="", color="Bills"),
                       title="Bills by weekday × hour (darker = busier)"), 380)
        c1, c2 = st.columns(2)
        with c1:
            hb = df.groupby("hour")["invoice_no"].nunique().reset_index(name="bills")
            peak = hb.loc[hb["bills"].idxmax(), "hour"]
            hb["type"] = hb["hour"].apply(lambda h: "Peak hour" if h == peak else "Other")
            show(px.bar(hb, x="hour", y="bills", color="type", title=f"Peak hour: {peak}:00",
                        color_discrete_map={"Peak hour": "#a87a22", "Other": "#b9c7b0"},
                        labels={"hour": "Hour", "bills": "Bills", "type": ""}), 330)
        with c2:
            w = wk.reset_index()
            show(px.bar(w, x="day_name", y="line_total", title="Average revenue by weekday", text_auto=",.0f",
                        color="line_total", color_continuous_scale=SCALE,
                        labels={"line_total": "Avg ₹", "day_name": ""}), 330)
        hr = df.groupby(["hour", "category"])["line_total"].sum().reset_index()
        show(px.area(hr, x="hour", y="line_total", color="category", title="What sells at which hour",
                     labels={"line_total": "Revenue (₹)", "hour": "Hour"}), 340)
    with t2:
        st.caption("Average daily sales on Tuesday (10% offer day) vs Wednesday and Thursday.")
        if wk[["Tuesday", "Wednesday", "Thursday"]].notna().all():
            mid = wk[["Wednesday", "Thursday"]].mean()
            diff = (wk["Tuesday"] / mid - 1) * 100
            td = df[df["day_name"] == "Tuesday"]
            lost = (td["quantity"] * td["unit_price"] * td["discount_pct"] / 100).sum()
            oc = st.columns(3)
            kpi_card(oc[0], "📅", "Tuesday avg/day", rupee(wk["Tuesday"]))
            kpi_card(oc[1], "📊", "Wed/Thu avg/day", rupee(mid))
            kpi_card(oc[2], "💸", "Discount given", rupee(lost))
            offer = pd.DataFrame({"Day": ["Tuesday (offer)", "Wednesday", "Thursday"],
                                  "Avg revenue": wk[["Tuesday", "Wednesday", "Thursday"]].values})
            show(px.bar(offer, x="Day", y="Avg revenue", color="Day", text_auto=",.0f"), 320)
            (st.success if diff > 5 else st.warning)(
                f"Tuesday sales are {diff:+.0f}% vs Wed/Thu. "
                + ("The offer is bringing extra customers." if diff > 5 else
                   "The offer isn't clearly bringing more customers — try a combo offer or move it to the weakest day."))
        else:
            st.info("Select a date range that includes Tuesdays, Wednesdays and Thursdays.")
    with t3:
        fl = A.is_festival(dl["date"])
        f_avg, n_avg = dl.loc[fl == 1, "line_total"].mean(), dl.loc[fl == 0, "line_total"].mean()
        if pd.notna(f_avg) and pd.notna(n_avg):
            c1, c2 = st.columns([2, 1])
            with c1:
                fc = pd.DataFrame({"Day type": ["Festival days", "Normal days"], "Avg revenue": [f_avg, n_avg]})
                show(px.bar(fc, x="Day type", y="Avg revenue", color="Day type", text_auto=",.0f",
                            title="Ganeshotsav vs normal days",
                            color_discrete_sequence=["#6e8b5f", "#b9c7b0"]), 340)
            with c2:
                st.write("")
                kpi_card(st, "🚀", "Festival uplift", f"{(f_avg / n_avg - 1) * 100:+.0f}%")
                st.caption("Plan extra stock, staff and festival specials for Navratri and Diwali.")
        else:
            st.info("No festival days in the selected range.")


def page_customers():
    t1, t2, t3, t4 = st.tabs(["🛵 Order channels", "💳 Payments & ratings", "🤖 AI segments", "🏆 Regulars"])
    with t1:
        commission = st.slider("Swiggy/Zomato commission (%)", 0, 35, 22)
        ot = df.groupby("order_type").agg(revenue=("line_total", "sum"), profit=("profit", "sum"),
                                          bills=("invoice_no", "nunique")).reset_index()
        ot["avg_bill"] = ot["revenue"] / ot["bills"]
        app = ot["order_type"].isin(["Swiggy", "Zomato"])
        ot["profit_after_commission"] = ot["profit"] - app * ot["revenue"] / 1.05 * commission / 100
        ot["real_margin_%"] = ot["profit_after_commission"] / (ot["revenue"] / 1.05) * 100
        c1, c2 = st.columns(2)
        with c1:
            ot2 = ot.rename(columns={"profit": "Before commission", "profit_after_commission": "After commission"})
            show(px.bar(ot2, x="order_type", y=["Before commission", "After commission"], barmode="group",
                        title="Profit before vs after commission",
                        labels={"value": "₹", "order_type": "", "variable": ""}), 350)
        with c2:
            show(px.bar(ot, x="order_type", y="real_margin_%", color="order_type", text_auto=".0f",
                        title="Real profit margin (%)",
                        labels={"order_type": "", "real_margin_%": "Margin (%)"}).update_layout(showlegend=False), 350)
        st.dataframe(ot, hide_index=True, use_container_width=True, column_config={
            "order_type": "Order type", "bills": "Bills",
            "revenue": st.column_config.NumberColumn("Revenue", format="₹%d"),
            "profit": st.column_config.NumberColumn("Profit", format="₹%d"),
            "avg_bill": st.column_config.NumberColumn("Avg bill", format="₹%d"),
            "profit_after_commission": st.column_config.NumberColumn("After commission", format="₹%d"),
            "real_margin_%": st.column_config.NumberColumn("Real margin", format="%.1f%%")})
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            pm = df.drop_duplicates("invoice_no")["payment_method"].value_counts().reset_index()
            show(px.pie(pm, names="payment_method", values="count", hole=.6, title="Bills by payment method"), 360)
        with c2:
            rt = df.drop_duplicates("invoice_no").dropna(subset=["customer_rating"])
            if rt.empty:
                st.info("No ratings in this selection.")
            else:
                rd = rt.groupby(["order_type", "customer_rating"]).size().reset_index(name="orders")
                rd["customer_rating"] = rd["customer_rating"].astype(int).astype(str) + "★"
                show(px.bar(rd, x="customer_rating", y="orders", color="order_type", barmode="group",
                            title=f"App ratings (avg {rt['customer_rating'].mean():.2f}★)",
                            labels={"customer_rating": "Rating", "order_type": ""}), 360)
    with t3:
        st.caption("Loyalty customers grouped by Recency, Frequency and Monetary value with K-Means clustering.")
        rfm = A.rfm_segments(df, st.slider("Number of segments", 3, 4, 4))
        if rfm.empty:
            st.info("Not enough loyalty customers in this selection.")
        else:
            seg = rfm.groupby("segment").agg(customers=("customer_id", "count"), avg_recency=("recency", "mean"),
                                             avg_visits=("frequency", "mean"),
                                             total_spend=("monetary", "sum")).reset_index()
            c1, c2 = st.columns([1, 1.6])
            with c1:
                show(px.pie(seg, names="segment", values="customers", hole=.55, title="Customers by segment"), 400)
            with c2:
                show(px.scatter_3d(rfm, x="recency", y="frequency", z="monetary", color="segment",
                                   hover_name="customer_id", title="3D segments (drag to rotate)",
                                   labels={"recency": "Days since visit", "frequency": "Visits",
                                           "monetary": "Spend ₹"}), 400)
            st.dataframe(seg, hide_index=True, use_container_width=True, column_config={
                "avg_recency": st.column_config.NumberColumn("Avg days since visit", format="%.0f"),
                "avg_visits": st.column_config.NumberColumn("Avg visits", format="%.1f"),
                "total_spend": st.column_config.NumberColumn("Total spend", format="₹%d")})
            st.markdown("<div class='card'>💎 <b>Champions</b> → free item / loyalty card · 😊 <b>Loyal</b> → upsell "
                        "combos · 🙂 <b>Occasional</b> → 'visit 3, get 1 free' · ⚠️ <b>At risk</b> → WhatsApp "
                        "win-back offer</div>", unsafe_allow_html=True)
            st.download_button("⬇️ Download segments (CSV)", rfm.to_csv(index=False), "customer_segments.csv")
    with t4:
        reg = (df[df["customer_id"] != ""].groupby("customer_id")
               .agg(visits=("invoice_no", "nunique"), spend=("line_total", "sum"), last_visit=("date", "max"))
               .nlargest(10, "spend").reset_index())
        st.dataframe(reg, hide_index=True, use_container_width=True, column_config={
            "spend": st.column_config.ProgressColumn("Spend", format="₹%d", min_value=0,
                                                     max_value=float(reg["spend"].max() if len(reg) else 1)),
            "last_visit": st.column_config.DateColumn("Last visit", format="DD MMM YYYY")})


def page_forecast():
    t1, t2 = st.tabs(["🔮 Sales forecast", "🚨 Unusual days"])
    try:
        with t1:
            horizon = st.slider("Days to forecast", 7, 60, 30)
            hist, fc, mape = A.forecast(df, horizon)
            fig = go.Figure()
            fig.add_scatter(x=hist["date"], y=hist["revenue"], name="Actual", line=dict(color="#2c4a3a"))
            fig.add_scatter(x=fc["date"], y=fc["high"], line=dict(width=0), showlegend=False, hoverinfo="skip")
            fig.add_scatter(x=fc["date"], y=fc["low"], fill="tonexty", line=dict(width=0),
                            fillcolor="rgba(168,122,34,.18)", name="80% range")
            fig.add_scatter(x=fc["date"], y=fc["forecast"], name="Forecast", line=dict(color="#a87a22", width=3))
            fig.update_layout(title="Actual vs forecast daily revenue", legend=dict(orientation="h", y=1.12),
                              hovermode="x unified")
            show(fig, 440)
            f = st.columns(4)
            kpi_card(f[0], "🔮", f"Next {horizon} days", rupee(fc["forecast"].sum()))
            kpi_card(f[1], "📅", "Per day", rupee(fc["forecast"].mean()))
            kpi_card(f[2], "🏆", "Best day", fc.loc[fc["forecast"].idxmax(), "date"].strftime("%a %d %b"))
            kpi_card(f[3], "🎯", "Model error (MAPE)", f"{mape:.0f}%" if pd.notna(mape) else "–")
            st.caption("Ridge regression on weekday pattern, growth trend and festival calendar; "
                       "tested on the last 14 days.")
            st.download_button("⬇️ Download forecast (CSV)",
                               fc.round({"forecast": 0, "low": 0, "high": 0}).to_csv(index=False), "forecast.csv")
        with t2:
            an = A.anomalies(df)
            fig = px.line(an, x="date", y="revenue", labels={"revenue": "Revenue (₹)", "date": ""},
                          title="Isolation Forest flags days that behaved very differently")
            fig.add_scatter(x=an.loc[an.anomaly, "date"], y=an.loc[an.anomaly, "revenue"], mode="markers",
                            marker=dict(color="#a8402a", size=13, symbol="x"), name="Unusual day")
            show(fig, 380)
            st.dataframe(an.loc[an.anomaly, ["date", "revenue", "fitted", "type"]].rename(
                columns={"fitted": "expected"}), hide_index=True, use_container_width=True, column_config={
                "date": st.column_config.DateColumn("Date", format="ddd DD MMM YYYY"),
                "revenue": st.column_config.NumberColumn("Actual", format="₹%d"),
                "expected": st.column_config.NumberColumn("Expected", format="₹%d")})
            st.caption("Rain, a stock-out, staff absence or a local event often explains these days.")
    except Exception as e:
        st.info(f"Need at least ~3 weeks of data for forecasting. ({e})")


def page_tools():
    t1, t2 = st.tabs(["🛒 Combo ideas", "💰 Price simulator"])
    with t1:
        min_c = st.slider("Minimum bills together", 2, 10, 4)
        pairs = A.basket_pairs(df, min_c)
        if pairs.empty:
            st.info("No pairs reach this minimum. Lower the slider.")
        else:
            cols = st.columns(3)
            for i, (_, p) in enumerate(pairs.head(3).iterrows()):
                price = df[df["item"].isin([p.item_a, p.item_b])].groupby("item")["unit_price"].first().sum()
                cols[i].markdown(f"<div class='card fadein'><b>🍱 Combo {i + 1}</b><br>{p.pair}<br>"
                                 f"<s>₹{price:,.0f}</s> → <b style='color:#a87a22;font-size:1.2rem'>"
                                 f"₹{price * 0.9:,.0f}</b><br><small>Together in {p.orders_together} bills · "
                                 f"lift {p.lift:.2f}</small></div>", unsafe_allow_html=True)
            show(px.bar(pairs.head(12).sort_values("lift"), x="lift", y="pair", orientation="h",
                        color="orders_together", color_continuous_scale=SCALE,
                        title="Items bought together (lift > 1 = more than chance)", labels={"pair": ""}), 440)
    with t2:
        c1, c2, c3 = st.columns(3)
        item = c1.selectbox("Item", sorted(df["item"].unique()))
        change = c2.slider("Price change (%)", -30, 30, 10)
        elast = c3.slider("Price sensitivity", -3.0, 0.0, -1.0, 0.1,
                          help="-1: a 10% price rise cuts units by 10%. Chai/snacks ≈ -1.5, specialty ≈ -0.5")
        before, after = A.price_simulation(df, item, change, elast)

        def pc(a, b):
            return (a / b - 1) * 100 if b else None

        m = st.columns(4)
        kpi_card(m[0], "🏷️", "New price", rupee(after["price"]), pc(after["price"], before["price"]), "%")
        kpi_card(m[1], "📦", "Units", f"{after['qty']:.0f}", pc(after["qty"], before["qty"]), "%")
        kpi_card(m[2], "💰", "Revenue", rupee(after["revenue"]), pc(after["revenue"], before["revenue"]), "%")
        kpi_card(m[3], "📈", "Profit", rupee(after["profit"]), pc(after["profit"], before["profit"]), "%")
        curve = pd.DataFrame([{"change_%": p, "profit": A.price_simulation(df, item, p, elast)[1]["profit"]}
                              for p in range(-30, 31, 2)])
        best = curve.loc[curve["profit"].idxmax()]
        fig = px.line(curve, x="change_%", y="profit", markers=True, title=f"Profit vs price change — {item}",
                      labels={"change_%": "Price change (%)", "profit": "Profit (₹)"})
        fig.add_vline(x=best["change_%"], line_dash="dash", line_color="#6e8b5f",
                      annotation_text=f"Best: {best['change_%']:+.0f}%")
        fig.add_vline(x=change, line_color="#a87a22", annotation_text="You", annotation_position="bottom right")
        show(fig, 360)


def page_chat():
    if not api_key:
        st.info("Add a free Gemini API key under ⚙️ Settings for full AI answers. "
                "Without it, the assistant answers basic questions.")
    if "chat" not in st.session_state:
        st.session_state.chat = [("assistant", f"Namaste! 👋 I'm the {CAFE} assistant, built by {AUTHOR}. "
                                               "Ask me about sales, items, customers, offers or forecasts.")]
    sugg = ["Which items should I remove?", "How to boost weak days?", "Suggest 3 combos with prices",
            "Are Swiggy/Zomato profitable?", "Plan for the next festival", "Summarise in 5 points"]
    sc = st.columns(6)
    preset = None
    for i, q in enumerate(sugg):
        if sc[i].button(q, use_container_width=True, key=f"sugg{i}"):
            preset = q

    box = st.container(height=480, border=True)
    with box:
        for role, msg in st.session_state.chat:
            with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "🌿"):
                st.markdown(msg)
    question = preset or st.chat_input("Ask about your café's data…")

    def ask_gemini(q):
        system = (f"You are a friendly, practical business analyst for {CAFE}, a small café in {CITY}. "
                  "Answer using ONLY the data summary. Use ₹ amounts and specific numbers, give clear actions, "
                  "keep answers under 160 words with short bullets, and reply in the user's language "
                  f"(English, Hindi or Marathi). If the data can't answer, say so.\n\nDATA SUMMARY:\n{A.data_context(df)}")
        hist = [{"role": "user" if r == "user" else "model", "parts": [{"text": m}]}
                for r, m in st.session_state.chat[1:][-8:]]
        hist.append({"role": "user", "parts": [{"text": q}]})
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                          headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                          json={"systemInstruction": {"parts": [{"text": system}]}, "contents": hist}, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    if question:
        with box:
            with st.chat_message("user", avatar="🧑‍💼"):
                st.markdown(question)
            with st.chat_message("assistant", avatar="🌿"):
                with st.spinner("Thinking…"):
                    try:
                        answer = ask_gemini(question) if api_key else A.rule_based_answer(question, df)
                    except Exception as e:
                        answer = f"⚠️ AI service error ({e}).\n\nBasic answer: {A.rule_based_answer(question, df)}"
                st.markdown(answer)
        st.session_state.chat += [("user", question), ("assistant", answer)]

    if len(st.session_state.chat) > 1:
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download chat", "\n\n".join(f"{r.upper()}: {m}" for r, m in st.session_state.chat),
                           "brew_bites_chat.txt", use_container_width=True)
        if c2.button("🗑️ Clear chat", use_container_width=True):
            del st.session_state["chat"]
            st.rerun()


def page_report():
    insights = A.auto_insights(df)
    me, _, _ = A.menu_engineering(df)

    def names(cl, n=3):
        lst = me.loc[me["class"] == cl].sort_values("revenue", ascending=False)["item"].head(n).tolist()
        return ", ".join(lst) if lst else "—"

    wk = df.groupby(["date", "day_name"])["line_total"].sum().groupby("day_name").mean()
    peak_h = df.groupby("hour")["invoice_no"].nunique().idxmax()
    t1, t2, t3, t4 = st.tabs(["📄 Summary", "✅ Recommendations", "🧹 Method", "👨‍💻 About"])
    with t1:
        st.markdown(f"""<div class='card'>Between <b>{start:%d %b %Y}</b> and <b>{end:%d %b %Y}</b>, {CAFE} made
<b>{rupee(k['revenue'])}</b> from <b>{k['bills']:,}</b> bills (average bill <b>{rupee(k['avg_bill'])}</b>), with a
profit of <b>{rupee(k['profit'])}</b> before rent and salaries.</div>""", unsafe_allow_html=True)
        for s in insights:
            insight_box(s)
        report = (f"{CAFE.upper()} — SALES ANALYTICS REPORT\nPrepared by {AUTHOR} ({EMAIL})\n"
                  f"Period: {start:%d %b %Y} to {end:%d %b %Y}\n\nRevenue: {rupee(k['revenue'])} | "
                  f"Profit: {rupee(k['profit'])} | Bills: {k['bills']} | Avg bill: {rupee(k['avg_bill'])}\n\n"
                  "KEY FINDINGS\n" + "\n".join("- " + s.replace("**", "") for s in insights))
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download report (TXT)", report, "brew_bites_report.txt", use_container_width=True)
        c2.download_button("⬇️ Download data (CSV)", df.to_csv(index=False), "brew_bites_data.csv",
                           use_container_width=True)
    with t2:
        st.markdown(f"""
1. **Promote high-margin, less-ordered items** ({names('🧩 Puzzle')}) with photos and counter display.
2. **Small price rise on popular low-margin items** ({names('🐴 Plowhorse')}) — test it in Smart Tools.
3. **Rework or remove weak items** ({names('🐶 Dog')}).
4. **Replace the flat Tuesday discount** with combos of items customers already buy together.
5. **Run an offer on {wk.idxmin()}**, the weakest day.
6. **Staff up around {peak_h}:00**, the busiest hour.
7. **Push direct orders** (WhatsApp/phone) to save 20–25% aggregator commission.
8. **Start a loyalty card** for Champions and win-back offers for at-risk customers.
9. **Plan festival menus, stock and staff** early.
""")
    with t3:
        st.markdown("""
| Issue found | Fix applied |
|---|---|
| 6 duplicate (double-billed) rows | Removed |
| 9 blank payment methods | Filled from order type, else *Unknown* |
| 7 messy item names | Standardised (`vada pav ` → `Vada Pav`) |
| 3 impossible quantities | Treated as typos, set to 1 |
| 4 refund rows | Separated from sales |
| Text dates | Converted; added hour, weekday, month |
| Totals | Recalculated GST, line total and profit |

**Tech stack:** Python · Pandas · NumPy · Scikit-learn (K-Means, Ridge regression, Isolation Forest) ·
market basket analysis · Plotly · Streamlit · Google Gemini API
""")
    with t4:
        st.markdown(f"""<div class='author fadein'><h3 style='margin:0'>{AUTHOR}</h3>
<p style='margin:4px 0 10px'>Data Analyst · B.E. Information Technology · Pune</p>
This project was designed and completed by <b>{AUTHOR}</b> — from data cleaning and analysis to machine-learning
models, business recommendations and this interactive AI dashboard.<br><br>
📧 <a href='mailto:{EMAIL}'>{EMAIL}</a> · 🔗 <a href='{LINKEDIN}' target='_blank'>LinkedIn</a> ·
💻 <a href='{GITHUB}' target='_blank'>GitHub</a><br><br><i>Available for freelance data analytics and dashboard projects.</i>
</div>""", unsafe_allow_html=True)
        st.caption("This demo uses simulated sales data for a sample café.")


# ================================================================ router
ROUTES = {"🏠 Home": page_home, "📊 Sales Overview": page_overview, "🍽️ Menu Insights": page_menu,
          "⏰ Time & Offers": page_time, "👥 Orders & Customers": page_customers, "🔮 AI Forecast": page_forecast,
          "🧰 Smart Tools": page_tools, "💬 AI Chatbot": page_chat, "📄 Report & About": page_report}

if page != "🏠 Home":
    c1, c2 = st.columns([1, 6])
    c1.button("← Home", on_click=go_to, args=("🏠 Home",), use_container_width=True)
    page_header(page)
ROUTES[page]()

st.markdown(f"<div class='footer'><div class='fb'>{CAFE}</div>"
            f"<div style='margin-top:6px'>AI sales analytics for a café in {CITY} · Designed & developed by "
            f"<b>{AUTHOR}</b> · <a href='{LINKEDIN}' target='_blank'>LinkedIn</a> · "
            f"<a href='{GITHUB}' target='_blank'>GitHub</a> · © 2026</div></div>", unsafe_allow_html=True)