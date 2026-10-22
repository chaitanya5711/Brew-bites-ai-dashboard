"""Analytics + AI logic for the Brew & Bytes Café dashboard (no Streamlit code here)."""
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FESTIVALS = [("2026-09-14", "2026-09-24", "Ganeshotsav"),
             ("2026-10-11", "2026-10-20", "Navratri/Dasara"),
             ("2026-11-06", "2026-11-10", "Diwali")]


# ---------------- data ----------------
def load_data(path="cafe_clean.csv"):
    df = pd.read_csv(path, parse_dates=["order_datetime"])
    df["date"] = df["order_datetime"].dt.normalize()
    df["hour"] = df["order_datetime"].dt.hour
    df["day_name"] = df["order_datetime"].dt.day_name()
    df["net_sales"] = (df["line_total"] - df["gst_5pct"]).round(2)
    df["customer_id"] = df["customer_id"].fillna("")
    return df


def is_festival(dates):
    dates = pd.to_datetime(pd.Series(dates))
    flag = pd.Series(0, index=dates.index)
    for s, e, _ in FESTIVALS:
        flag |= dates.between(s, e).astype(int)
    return flag.values


def kpis(df):
    bills = df.groupby("invoice_no")["line_total"].sum()
    days = df["date"].nunique() or 1
    return {
        "revenue": df["line_total"].sum(),
        "profit": df["profit"].sum(),
        "margin": df["profit"].sum() / df["net_sales"].sum() * 100 if len(df) else 0,
        "bills": bills.size,
        "avg_bill": bills.mean() if bills.size else 0,
        "items_sold": int(df["quantity"].sum()),
        "rev_per_day": df["line_total"].sum() / days,
        "rating": df.drop_duplicates("invoice_no")["customer_rating"].mean(),
    }


def daily_series(df):
    d = df.groupby("date").agg(revenue=("line_total", "sum"), bills=("invoice_no", "nunique"),
                               profit=("profit", "sum"))
    full = pd.date_range(d.index.min(), d.index.max(), freq="D")
    d = d.reindex(full, fill_value=0)
    d.index.name = "date"
    d["ma7"] = d["revenue"].rolling(7, min_periods=1).mean()
    return d.reset_index()


# ---------------- menu engineering ----------------
def menu_engineering(df):
    m = df.groupby(["item", "category"]).agg(qty=("quantity", "sum"), revenue=("line_total", "sum"),
                                             profit=("profit", "sum")).reset_index()
    m["profit_per_unit"] = m["profit"] / m["qty"]
    # classic menu-engineering rule: popular = at least 70% of average quantity
    pop_cut, margin_cut = 0.7 * m["qty"].mean(), m["profit_per_unit"].mean()

    def cls(r):
        hi_pop, hi_mar = r.qty >= pop_cut, r.profit_per_unit >= margin_cut
        if hi_pop and hi_mar: return "⭐ Star"
        if hi_pop: return "🐴 Plowhorse"
        if hi_mar: return "🧩 Puzzle"
        return "🐶 Dog"

    m["class"] = m.apply(cls, axis=1)
    advice = {"⭐ Star": "Keep quality, feature it on the menu",
              "🐴 Plowhorse": "Popular but low margin: small price rise or cheaper ingredients",
              "🧩 Puzzle": "High margin but rarely ordered: promote it, better placement/photo",
              "🐶 Dog": "Low sales and margin: consider removing or reworking"}
    m["action"] = m["class"].map(advice)
    return m.sort_values("profit", ascending=False), pop_cut, margin_cut


# ---------------- customers (RFM + KMeans) ----------------
def rfm_segments(df, k=4):
    c = df[df["customer_id"] != ""]
    if c["customer_id"].nunique() < k * 3:
        return pd.DataFrame()
    ref = c["date"].max() + pd.Timedelta(days=1)
    rfm = c.groupby("customer_id").agg(recency=("date", lambda x: (ref - x.max()).days),
                                       frequency=("invoice_no", "nunique"),
                                       monetary=("line_total", "sum")).reset_index()
    X = StandardScaler().fit_transform(np.column_stack([rfm.recency, np.log1p(rfm.frequency),
                                                        np.log1p(rfm.monetary)]))
    rfm["cluster"] = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(X)
    score = rfm.groupby("cluster").apply(
        lambda g: g.frequency.mean() + g.monetary.mean() / 200 - g.recency.mean() / 15, include_groups=False)
    names = ["💎 Champions", "😊 Loyal regulars", "🙂 Occasional", "⚠️ At risk / lost"]
    order = score.sort_values(ascending=False).index
    rfm["segment"] = rfm["cluster"].map({cl: names[i] for i, cl in enumerate(order)})
    return rfm.drop(columns="cluster")


# ---------------- basket analysis ----------------
def basket_pairs(df, min_count=4):
    baskets = df.groupby("invoice_no")["item"].apply(lambda s: sorted(set(s)))
    n = len(baskets)
    item_cnt = baskets.explode().value_counts()
    pair_cnt = {}
    for items in baskets:
        for a, b in combinations(items, 2):
            pair_cnt[(a, b)] = pair_cnt.get((a, b), 0) + 1
    rows = []
    for (a, b), c in pair_cnt.items():
        if c < min_count:
            continue
        sup = c / n
        conf = c / item_cnt[a]
        lift = sup / ((item_cnt[a] / n) * (item_cnt[b] / n))
        rows.append([f"{a} + {b}", a, b, c, sup * 100, conf * 100, lift])
    out = pd.DataFrame(rows, columns=["pair", "item_a", "item_b", "orders_together",
                                      "support_%", "confidence_%", "lift"])
    return out.sort_values(["lift", "orders_together"], ascending=False).reset_index(drop=True)


# ---------------- AI forecast + anomalies ----------------
def _features(dates, t0):
    dates = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    X = pd.get_dummies(dates.dt.day_name()).reindex(columns=DAYS, fill_value=0).astype(float)
    X["trend"] = (dates - t0).dt.days.values
    X["festival"] = is_festival(dates)
    return X


def forecast(df, horizon=30):
    d = daily_series(df)
    d = d[d["revenue"] > 0]                     # ignore closed days
    t0 = d["date"].min()
    X, y = _features(d["date"], t0), d["revenue"].values
    model = Ridge(alpha=1.0)

    # back-test on last 14 days
    cut = max(len(d) - 14, 10)
    model.fit(X.iloc[:cut], y[:cut])
    pred_bt = model.predict(X.iloc[cut:])
    mape = float(np.mean(np.abs((y[cut:] - pred_bt) / y[cut:])) * 100) if len(y) > cut else np.nan

    model.fit(X, y)
    resid = y - model.predict(X)
    sd = resid.std()
    fut = pd.date_range(d["date"].max() + pd.Timedelta(days=1), periods=horizon, freq="D")
    yhat = np.clip(model.predict(_features(fut, t0)), 0, None)
    fc = pd.DataFrame({"date": fut, "forecast": yhat,
                       "low": np.clip(yhat - 1.28 * sd, 0, None), "high": yhat + 1.28 * sd})
    hist = d[["date", "revenue"]].copy()
    hist["fitted"] = model.predict(X)
    return hist, fc, mape


def anomalies(df):
    hist, _, _ = forecast(df, 1)
    hist["residual"] = hist["revenue"] - hist["fitted"]
    bills = daily_series(df).set_index("date").loc[hist["date"], "bills"].values
    iso = IsolationForest(contamination=0.05, random_state=0)
    hist["anomaly"] = iso.fit_predict(np.column_stack([hist["residual"], bills])) == -1
    hist["type"] = np.where(hist["residual"] > 0, "Unusually high", "Unusually low")
    return hist


# ---------------- pricing simulator ----------------
def price_simulation(df, item, change_pct, elasticity):
    r = df[df["item"] == item]
    qty, price, cost = r["quantity"].sum(), r["unit_price"].mean(), r["unit_cost"].mean()
    new_price = price * (1 + change_pct / 100)
    new_qty = max(qty * (1 + elasticity * change_pct / 100), 0)
    before = {"price": price, "qty": qty, "revenue": qty * price, "profit": qty * (price - cost)}
    after = {"price": new_price, "qty": new_qty, "revenue": new_qty * new_price,
             "profit": new_qty * (new_price - cost)}
    return before, after


# ---------------- automatic insights ----------------
def auto_insights(df):
    if df.empty:
        return ["No data for the selected filters."]
    out = []
    me, _, _ = menu_engineering(df)
    top_p = me.iloc[0]
    top_q = me.sort_values("qty", ascending=False).iloc[0]
    out.append(f"**{top_p['item']}** earns the most profit (₹{top_p['profit']:,.0f}), "
               f"while **{top_q['item']}** is the most ordered ({int(top_q['qty'])} units).")
    dogs = me[me["class"] == "🐶 Dog"]["item"].tolist()
    if dogs:
        out.append(f"Weak items (low sales and low margin): {', '.join(dogs[:4])}. Review or replace them.")

    hrs = df.groupby("hour")["invoice_no"].nunique()
    out.append(f"Busiest hour is **{hrs.idxmax()}:00–{hrs.idxmax() + 1}:00**; quietest is "
               f"{hrs.idxmin()}:00. Plan staff and fresh prep around this.")

    dl = df.groupby(["date", "day_name"])["line_total"].sum().reset_index()
    wk = dl.groupby("day_name")["line_total"].mean().reindex(DAYS).dropna()
    if len(wk) >= 5:
        out.append(f"**{wk.idxmax()}** is the best day (avg ₹{wk.max():,.0f}); **{wk.idxmin()}** "
                   f"is the weakest (avg ₹{wk.min():,.0f}) — a good day for an offer.")
        if "Tuesday" in wk and {"Wednesday", "Thursday"} <= set(wk.index):
            mid = wk[["Wednesday", "Thursday"]].mean()
            diff = (wk["Tuesday"] / mid - 1) * 100
            verdict = "is working" if diff > 5 else "is not clearly lifting sales"
            out.append(f"The Tuesday 10% offer {verdict}: Tuesday sales are {diff:+.0f}% vs Wed/Thu.")

    ot = df.groupby("order_type").agg(rev=("line_total", "sum"), prof=("profit", "sum"))
    ot["m"] = ot["prof"] / ot["rev"] * 100
    if {"Dine-in", "Swiggy"} <= set(ot.index):
        out.append(f"Dine-in margin is {ot.loc['Dine-in', 'm']:.0f}% vs Swiggy {ot.loc['Swiggy', 'm']:.0f}% "
                   "(before aggregator commission of ~20–25%), so push direct orders.")

    fest = df[is_festival(df["date"]) == 1]
    norm = df[is_festival(df["date"]) == 0]
    if not fest.empty and not norm.empty:
        f_avg = fest.groupby("date")["line_total"].sum().mean()
        n_avg = norm.groupby("date")["line_total"].sum().mean()
        out.append(f"Festival days bring **{(f_avg / n_avg - 1) * 100:+.0f}%** sales vs normal days. "
                   "Stock up and add festival specials.")

    pairs = basket_pairs(df)
    if not pairs.empty:
        p = pairs.iloc[0]
        out.append(f"**{p['pair']}** are often bought together (lift {p['lift']:.1f}) — "
                   "try a combo at a small discount.")

    rating = df.drop_duplicates("invoice_no")["customer_rating"].mean()
    if not np.isnan(rating):
        low = (df.drop_duplicates("invoice_no")["customer_rating"] <= 2).sum()
        out.append(f"App rating averages **{rating:.1f}/5** with {low} low (1–2★) ratings. "
                   "Check packaging and delivery time.")
    return out


# ---------------- data summary for the AI chat ----------------
def data_context(df):
    k = kpis(df)
    me, _, _ = menu_engineering(df)
    hrs = df.groupby("hour")["invoice_no"].nunique()
    wk = df.groupby(["date", "day_name"])["line_total"].sum().groupby("day_name").mean().reindex(DAYS)
    ot = df.groupby("order_type")[["line_total", "profit"]].sum().round(0)
    pay = df.drop_duplicates("invoice_no")["payment_method"].value_counts()
    monthly = df.groupby(df["date"].dt.to_period("M"))["line_total"].sum().round(0)
    return f"""Café sales data, {df['date'].min():%d %b %Y} to {df['date'].max():%d %b %Y}. Amounts in INR.
KPIs: revenue {k['revenue']:.0f}, profit {k['profit']:.0f}, margin {k['margin']:.1f}%, bills {k['bills']},
avg bill {k['avg_bill']:.0f}, revenue/day {k['rev_per_day']:.0f}, app rating {k['rating']:.2f}.
Items (qty, revenue, profit, class):
{me[['item', 'qty', 'revenue', 'profit', 'class']].round(0).to_string(index=False)}
Bills per hour: {hrs.to_dict()}
Avg revenue per weekday: {wk.round(0).to_dict()}
By order type: {ot.to_dict('index')}
Payment methods (bills): {pay.to_dict()}
Monthly revenue: {monthly.astype(str).to_dict()}
Insights: {' | '.join(auto_insights(df))}"""


def rule_based_answer(q, df):
    q = q.lower()
    k = kpis(df)
    me, _, _ = menu_engineering(df)
    if any(w in q for w in ["revenue", "sales", "earn", "income"]):
        return f"Total revenue is ₹{k['revenue']:,.0f} (₹{k['rev_per_day']:,.0f} per day) from {k['bills']} bills."
    if "profit" in q or "margin" in q:
        return f"Profit is ₹{k['profit']:,.0f}, a {k['margin']:.1f}% margin on net sales."
    if any(w in q for w in ["best", "top", "popular", "selling"]):
        t = me.sort_values("qty", ascending=False).head(3)["item"].tolist()
        return f"Top sellers: {', '.join(t)}. Most profitable: {me.iloc[0]['item']}."
    if any(w in q for w in ["worst", "remove", "weak"]):
        return "Weak items: " + ", ".join(me[me['class'] == '🐶 Dog']['item']) + "."
    if any(w in q for w in ["hour", "time", "peak", "busy"]):
        h = df.groupby("hour")["invoice_no"].nunique().idxmax()
        return f"Peak hour is {h}:00–{h + 1}:00."
    if any(w in q for w in ["day", "week"]):
        wk = df.groupby(["date", "day_name"])["line_total"].sum().groupby("day_name").mean()
        return f"Best day: {wk.idxmax()}, weakest: {wk.idxmin()}."
    if any(w in q for w in ["combo", "together", "pair"]):
        p = basket_pairs(df)
        return "Best combos: " + ", ".join(p.head(3)["pair"]) if not p.empty else "Not enough data."
    return ("I can answer about revenue, profit, best/worst items, peak hours, best days and combos. "
            "Add a Gemini API key in the sidebar for free-form questions.")


# =====================================================================================
# NEW DATA: read → clean → merge  (same steps as the Jupyter cleaning notebook)
# =====================================================================================
REQUIRED_COLS = ["invoice_no", "order_datetime", "order_type", "item", "quantity", "unit_price"]
OPTIONAL_COLS = ["payment_method", "category", "unit_cost", "discount_pct", "customer_id", "cashier",
                 "customer_rating", "line_total"]
MASTER_COLS = ["invoice_no", "order_datetime", "order_type", "payment_method", "item", "category", "quantity",
               "unit_price", "unit_cost", "discount_pct", "customer_id", "cashier", "customer_rating",
               "gst_5pct", "line_total", "profit", "date", "hour", "day_name", "month"]
COL_ALIASES = {"bill_no": "invoice_no", "bill_number": "invoice_no", "invoice": "invoice_no",
               "invoice_number": "invoice_no", "order_id": "invoice_no",
               "datetime": "order_datetime", "date_time": "order_datetime", "bill_date": "order_datetime",
               "order_date": "order_datetime", "timestamp": "order_datetime", "date": "order_datetime",
               "type": "order_type", "channel": "order_type", "order_channel": "order_type",
               "item_name": "item", "product": "item", "product_name": "item", "dish": "item",
               "qty": "quantity", "price": "unit_price", "rate": "unit_price", "mrp": "unit_price",
               "cost": "unit_cost", "cost_price": "unit_cost", "discount": "discount_pct",
               "discount_%": "discount_pct", "payment": "payment_method", "payment_mode": "payment_method",
               "mode": "payment_method", "customer": "customer_id", "rating": "customer_rating",
               "amount": "line_total", "total": "line_total", "total_amount": "line_total"}
QTY_LIMIT = 10          # one item × more than 10 on a café bill = typing error
DEFAULT_COST_RATIO = 0.35
DATE_FORMATS = ["%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M",
                "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
ORDER_TYPES = {"dine-in": "Dine-in", "dine in": "Dine-in", "dinein": "Dine-in", "dine": "Dine-in",
               "takeaway": "Takeaway", "take away": "Takeaway", "take-away": "Takeaway", "parcel": "Takeaway",
               "swiggy": "Swiggy", "zomato": "Zomato"}


def read_any(file, name):
    """Read an uploaded CSV or Excel file."""
    name = (name or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file, dtype=str)
    return pd.read_csv(file, dtype=str, keep_default_na=False)


def _parse_dates(col):
    s = col.astype("string").str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        todo = out.isna() & s.notna()
        if not todo.any():
            break
        out[todo] = pd.to_datetime(s[todo], format=fmt, errors="coerce")
    todo = out.isna() & s.notna()
    if todo.any():                                   # last try: let pandas guess (day first, Indian style)
        out[todo] = pd.to_datetime(s[todo], dayfirst=True, errors="coerce", format="mixed")
    return out


def clean_sales(raw, reference=None):
    """Clean a raw billing export. Returns (clean_df in master format, report rows)."""
    rep = []

    def note(issue, count, action):
        if count:
            rep.append({"Issue found": issue, "Rows": int(count), "Fix applied": action})

    df = raw.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    for alias, target in COL_ALIASES.items():
        if alias in df.columns and target not in df.columns:
            df = df.rename(columns={alias: target})
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(missing)
                         + ". Download the template on the 'File format' tab to see the expected columns.")
    for c in OPTIONAL_COLS:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[REQUIRED_COLS + OPTIONAL_COLS]

    text_cols = ["invoice_no", "order_type", "item", "payment_method", "category", "customer_id", "cashier"]
    for c in text_cols:
        df[c] = df[c].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    for c in ["quantity", "unit_price", "unit_cost", "discount_pct", "customer_rating", "line_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    blank = df.isna().all(axis=1) | df[["invoice_no", "item"]].isna().all(axis=1)
    note("Empty rows", blank.sum(), "Removed")
    df = df[~blank]

    d = df.duplicated()
    note("Duplicate (double-billed) rows", d.sum(), "Removed")
    df = df[~d].copy()

    # item names → match the café menu, ignoring case and spaces
    canon = {}
    if reference is not None and len(reference):
        canon = {str(i).strip().lower(): i for i in reference["item"].dropna().unique()}
    raw_item = df["item"].copy()
    key = df["item"].str.lower().str.replace(r"\s+", " ", regex=True)
    df["item"] = key.map(canon).fillna(df["item"].str.replace(r"\s+", " ", regex=True).str.title())
    note("Item names with wrong case / extra spaces", (raw_item.fillna("") != df["item"].fillna("")).sum(),
         "Standardised to menu names")

    ot = df["order_type"].str.lower().map(ORDER_TYPES)
    note("Order types written differently (e.g. 'dine in', 'parcel')",
         (ot.notna() & (ot != df["order_type"])).sum(), "Standardised")
    df["order_type"] = ot.fillna(df["order_type"].str.title()).fillna("Dine-in")

    dt = _parse_dates(df["order_datetime"])
    note("Unreadable or missing dates", dt.isna().sum(), "Removed")
    df["order_datetime"] = dt
    bad = df["order_datetime"].isna() | df["item"].isna() | df["unit_price"].isna() | (df["unit_price"] <= 0)
    note("Rows without item or price", (bad & df["order_datetime"].notna()).sum(), "Removed")
    df = df[~bad].copy()

    refund = (df["line_total"] < 0) | (df["quantity"] < 0)
    note("Refunds (negative amounts)", refund.sum(), "Separated from sales")
    df = df[~refund].copy()

    q_missing = df["quantity"].isna() | (df["quantity"] == 0)
    note("Missing quantity", q_missing.sum(), "Set to 1")
    df.loc[q_missing, "quantity"] = 1
    q_bad = df["quantity"] > QTY_LIMIT
    note(f"Impossible quantities (more than {QTY_LIMIT} of one item)", q_bad.sum(), "Treated as typos, set to 1")
    df.loc[q_bad, "quantity"] = 1
    df["quantity"] = df["quantity"].round().astype(int)

    app = df["order_type"].isin(["Swiggy", "Zomato"])
    pm_blank = df["payment_method"].isna()
    note("Blank payment methods", pm_blank.sum(), "Filled from order type, else 'Unknown'")
    df.loc[pm_blank & app, "payment_method"] = "Online (App)"
    df["payment_method"] = df["payment_method"].fillna("Unknown")

    # category and cost from the existing menu; new items get estimates
    if reference is not None and len(reference):
        menu = reference.drop_duplicates("item").set_index("item")
        df["category"] = df["category"].fillna(df["item"].map(menu["category"]))
        df["unit_cost"] = df["unit_cost"].fillna(df["item"].map(menu["unit_cost"]))
    new_items = sorted(df.loc[df["unit_cost"].isna(), "item"].unique())
    note("New menu items without cost (" + ", ".join(new_items[:5]) + ("…" if len(new_items) > 5 else "") + ")",
         df["unit_cost"].isna().sum(), f"Cost estimated at {DEFAULT_COST_RATIO:.0%} of price")
    df["unit_cost"] = df["unit_cost"].fillna(df["unit_price"] * DEFAULT_COST_RATIO).round(2)
    df["category"] = df["category"].fillna("Other")

    df["discount_pct"] = df["discount_pct"].fillna(0).clip(0, 100)
    df["customer_rating"] = df["customer_rating"].where(df["customer_rating"].between(1, 5))
    df["customer_id"] = df["customer_id"].fillna("")
    df["cashier"] = df["cashier"].fillna("")

    sub = df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
    df["gst_5pct"] = (sub * 0.05).round(2)
    df["line_total"] = (sub * 1.05).round(2)
    df["profit"] = (sub - df["quantity"] * df["unit_cost"]).round(2)
    df["date"] = df["order_datetime"].dt.strftime("%Y-%m-%d")
    df["hour"] = df["order_datetime"].dt.hour
    df["day_name"] = df["order_datetime"].dt.day_name()
    df["month"] = df["order_datetime"].dt.month_name()
    df["order_datetime"] = df["order_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    rep.append({"Issue found": "Totals, GST and profit", "Rows": len(df), "Fix applied": "Recalculated"})
    return df[MASTER_COLS].sort_values(["order_datetime", "invoice_no"]).reset_index(drop=True), rep


def read_master(path):
    return pd.read_csv(path, dtype={"invoice_no": str, "customer_id": str, "cashier": str},
                       keep_default_na=True).fillna({"customer_id": "", "cashier": ""})


def _row_key(d):
    return (d["invoice_no"].astype(str) + "|" + d["order_datetime"].astype(str).str[:16] + "|"
            + d["item"].astype(str) + "|" + d["quantity"].astype(str))


def merge_sales(master, new):
    """Add only rows not already in the master file. Returns (combined, rows_added, rows_skipped)."""
    seen = set(_row_key(master))
    is_new = ~_row_key(new).isin(seen)
    combined = pd.concat([master, new[is_new]], ignore_index=True)
    combined = combined.sort_values(["order_datetime", "invoice_no"]).reset_index(drop=True)
    return combined[MASTER_COLS], int(is_new.sum()), int((~is_new).sum())


def template_csv():
    return ("invoice_no,order_datetime,order_type,payment_method,item,category,quantity,unit_price,unit_cost,"
            "discount_pct,customer_id,cashier,customer_rating\n"
            "BB/26-27/02001,01-10-2026 08:15,Dine-in,UPI,Masala Chai,Beverages,2,40,10,0,CUST0012,Rohit,\n"
            "BB/26-27/02001,01-10-2026 08:15,Dine-in,UPI,Poha,Breakfast,1,60,15,0,CUST0012,Rohit,\n"
            "BB/26-27/02002,01-10-2026 13:40,Swiggy,Online (App),Veg Burger,Fast Food,1,130,45,5,,Rohit,4\n")