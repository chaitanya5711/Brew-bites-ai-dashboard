"""Analytics + AI logic for the Tekdi Café dashboard (no Streamlit code here)."""
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FESTIVALS = [("2026-09-14", "2026-09-24", "Ganeshotsav"),
             ("2026-10-20", "2026-10-24", "Navratri/Dasara"),
             ("2026-11-06", "2026-11-11", "Diwali")]


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