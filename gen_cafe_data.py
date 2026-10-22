"""Generate realistic sample sales data for Brew & Bytes Café (simulated, for demo use).

python gen_cafe_data.py            -> brew_bytes_sales_jul_sep_2026.csv  (Jul–Sep 2026, raw/messy)
                                       brew_bytes_sales_oct_2026.csv      (Oct 2026, raw/messy, for "Add New Data")
"""
import numpy as np
import pandas as pd

# item, category, price (₹, before GST), cost, base popularity, tags
MENU = [
    ("Espresso",              "Coffee",             120, 30, 3, {"hot", "morning"}),
    ("Americano",             "Coffee",             140, 32, 4, {"hot", "morning"}),
    ("Cappuccino",            "Coffee",             160, 42, 9, {"hot", "morning"}),
    ("Café Latte",            "Coffee",             170, 45, 8, {"hot", "morning"}),
    ("Hazelnut Latte",        "Coffee",             200, 55, 4, {"hot"}),
    ("Cold Coffee",           "Coffee",             180, 50, 10, {"cold"}),
    ("Iced Latte",            "Coffee",             190, 52, 5, {"cold"}),
    ("Caramel Frappé",        "Coffee",             230, 70, 4, {"cold"}),
    ("Masala Chai",           "Tea & Mocktails",     60, 14, 7, {"hot", "morning"}),
    ("Lemon Iced Tea",        "Tea & Mocktails",    140, 30, 4, {"cold"}),
    ("Virgin Mojito",         "Tea & Mocktails",    160, 35, 5, {"cold", "evening"}),
    ("Oreo Shake",            "Shakes",             200, 60, 6, {"cold"}),
    ("Chocolate Shake",       "Shakes",             190, 58, 4, {"cold"}),
    ("Veg Grilled Sandwich",  "Sandwiches & Wraps", 150, 50, 8, {"food", "morning"}),
    ("Paneer Tikka Sandwich", "Sandwiches & Wraps", 190, 68, 6, {"food"}),
    ("Paneer Wrap",           "Sandwiches & Wraps", 210, 75, 4, {"food"}),
    ("Classic Veg Burger",    "Snacks",             160, 55, 6, {"food", "evening"}),
    ("Peri Peri Fries",       "Snacks",             140, 38, 9, {"food", "evening"}),
    ("Cheesy Garlic Bread",   "Snacks",             160, 45, 6, {"food", "evening"}),
    ("Loaded Nachos",         "Snacks",             210, 65, 3, {"food", "evening"}),
    ("Margherita Pizza",      "Pizza & Pasta",      280, 95, 7, {"food", "evening"}),
    ("Farmhouse Pizza",       "Pizza & Pasta",      340, 120, 5, {"food", "evening"}),
    ("Paneer Tikka Pizza",    "Pizza & Pasta",      360, 130, 4, {"food", "evening"}),
    ("White Sauce Pasta",     "Pizza & Pasta",      260, 85, 6, {"food", "evening"}),
    ("Red Sauce Pasta",       "Pizza & Pasta",      240, 78, 3, {"food", "evening"}),
    ("Chocolate Brownie",     "Desserts",           150, 45, 5, {"dessert"}),
    ("Choco Lava Cake",       "Desserts",           170, 50, 4, {"dessert"}),
    ("Blueberry Cheesecake",  "Desserts",           240, 85, 2, {"dessert"}),
]
STAFF = ["Rohit", "Sneha", "Amit"]
HOURS = list(range(9, 23))                                               # café open 9 am – 11 pm
HOUR_W = np.array([4, 5, 5, 6, 7, 6, 5, 6, 8, 10, 10, 9, 7, 4], float)   # evening peak


def generate(start, end, seed, seq0, festival, closed_day, growth, extra_items=(), rainy=False):
    rng = np.random.default_rng(seed)
    menu = MENU + list(extra_items)
    names = [m[0] for m in menu]
    tags = [m[5] for m in menu]
    base_pop = np.array([m[4] for m in menu], float)
    idx_of = lambda tag: [i for i, t in enumerate(tags) if tag in t]
    customers = [f"CUST{n:04d}" for n in range(1, 321)]                # loyalty members
    cust_w = np.random.default_rng(7).pareto(1.2, len(customers)) + 1   # same regulars every month
    dates = pd.date_range(start, end, freq="D")
    rows, seq = [], seq0

    for d in dates:
        if d == pd.Timestamp(closed_day):
            continue                                                     # closed (power cut / heavy rain)
        lam = 5.6
        if d.dayofweek >= 5: lam *= 1.55                                 # weekends busier
        if d.dayofweek == 0: lam *= 0.8                                  # slow Mondays
        if pd.Timestamp(festival[0]) <= d <= pd.Timestamp(festival[1]):
            lam *= 1.7                                                   # festival crowd
        lam *= growth(d, dates[0])
        promo = d.dayofweek == 1                                         # Tuesday 10% off offer

        for _ in range(rng.poisson(lam)):
            seq += 1
            hour = int(rng.choice(HOURS, p=HOUR_W / HOUR_W.sum()))
            ts = d + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)))
            otype = rng.choice(["Dine-in", "Takeaway", "Swiggy", "Zomato"], p=[0.55, 0.15, 0.17, 0.13])
            app = otype in ("Swiggy", "Zomato")
            pay = "Online (App)" if app else rng.choice(["UPI", "Cash", "Card"], p=[0.70, 0.18, 0.12])
            w = base_pop.copy()
            if hour < 12: w[idx_of("morning")] *= 2.5                     # coffee & sandwiches in the morning
            if hour >= 18 or d.dayofweek >= 5: w[idx_of("evening")] *= 1.8   # pizza, fries, mojitos later
            if rainy: w[idx_of("hot")] *= 1.4                             # monsoon: hot drinks
            if app: w[idx_of("food")] *= 1.6                              # delivery is mostly food
            k = rng.choice([1, 2, 3, 4], p=[0.30, 0.40, 0.20, 0.10])
            items = rng.choice(len(menu), size=k, replace=False, p=w / w.sum())
            cust = rng.choice(customers, p=cust_w / cust_w.sum()) if (not app and rng.random() < 0.45) else ""
            rating = int(rng.choice([1, 2, 3, 4, 5], p=[0.04, 0.06, 0.15, 0.4, 0.35])) if (app and rng.random() < 0.6) else ""
            disc = 10 if promo else (5 if app and rng.random() < 0.35 else 0)
            who = STAFF[0] if hour < 16 else STAFF[1]                     # shift-wise cashier
            if d.dayofweek >= 5 and rng.random() < 0.4: who = STAFF[2]    # weekend helper
            inv = f"BB/26-27/{seq:05d}"
            for i in items:
                name, cat, price, cost = menu[i][:4]
                qty = int(rng.choice([1, 2, 3], p=[0.80, 0.17, 0.03]))
                rows.append([inv, ts, otype, pay, name, cat, qty, price, cost, disc, cust, who, rating])

    df = pd.DataFrame(rows, columns=["invoice_no", "order_datetime", "order_type", "payment_method",
                                     "item", "category", "quantity", "unit_price", "unit_cost",
                                     "discount_pct", "customer_id", "cashier", "customer_rating"])
    sub = df.quantity * df.unit_price * (1 - df.discount_pct / 100)
    df["gst_5pct"] = (sub * 0.05).round(2)
    df["line_total"] = (sub * 1.05).round(2)

    # --- small, realistic data-entry mess for the cleaning step ---
    n = len(df)
    i = rng.choice(n, 9, replace=False); df.loc[i, "payment_method"] = ""
    i = rng.choice(n, 7, replace=False); df.loc[i, "item"] = df.loc[i, "item"].str.lower() + " "
    i = rng.choice(n, 3, replace=False); df.loc[i, "quantity"] = [20, 12, 30]          # typo quantities
    df.loc[i, "line_total"] = (df.loc[i, "quantity"] * df.loc[i, "unit_price"] * 1.05).round(2)
    i = rng.choice(n, 4, replace=False); df.loc[i, "line_total"] *= -1                 # refunds
    df = pd.concat([df, df.sample(6, random_state=3)]).sort_values(["order_datetime", "invoice_no"])  # double-billed
    df["order_datetime"] = df["order_datetime"].dt.strftime("%d-%m-%Y %H:%M")
    return df


if __name__ == "__main__":
    q3 = generate("2026-07-01", "2026-09-30", seed=4, seq0=411, festival=("2026-09-14", "2026-09-24"),
                  closed_day="2026-08-18", growth=lambda d, d0: 1 + 0.2 * (d - d0).days / 91, rainy=True)
    q3.to_csv("brew_bytes_sales_jul_sep_2026.csv", index=False)
    oct_ = generate("2026-10-01", "2026-10-31", seed=2026, seq0=1300, festival=("2026-10-11", "2026-10-20"),
                    closed_day="2026-10-02", growth=lambda d, d0: 1.2,
                    extra_items=[("Hot Chocolate", "Coffee", 180, 55, 4, {"hot"})])   # new item launched in Oct
    oct_.to_csv("brew_bytes_sales_oct_2026.csv", index=False)
    for name, d in [("Jul–Sep", q3), ("Oct", oct_)]:
        print(name, d.shape, "bills", d.invoice_no.nunique(), "revenue", round(d.line_total.sum()))
