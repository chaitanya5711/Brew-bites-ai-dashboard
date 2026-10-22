<img src="logo.svg" width="72" alt="Brew & Bytes Café logo">

# Brew & Bytes Café — AI-Powered Sales Analytics Dashboard

An end-to-end analytics project for a neighbourhood café in Ichalkaranji: **raw billing data → cleaning → analysis →
machine learning → business recommendations**, delivered as an interactive Streamlit dashboard with an AI chatbot.

> Sample case study built on **simulated** sales data (Jul–Oct 2026) to demonstrate what the dashboard can do for
> a real café, restaurant or retail shop.

**🔗 Live demo:** _add your Streamlit link here_

## Features
| Page | What it shows |
|---|---|
| 📊 Sales Overview | Revenue, profit, bills, average bill, daily trend with festivals, monthly target gauge |
| 🍽️ Menu Insights | Menu-engineering matrix (Stars / Plowhorses / Puzzles / Dogs), top items, item explorer |
| ⏰ Time & Offers | Peak-hour heatmap, best/worst days, Tuesday-offer test, festival uplift |
| 👥 Orders & Customers | Dine-in vs Swiggy/Zomato profit after commission, payments, ratings, **K-Means customer segments** |
| 🔮 AI Forecast | **Ridge-regression** sales forecast with confidence band, **Isolation Forest** anomaly detection |
| 🧰 Smart Tools | **Market-basket** combo ideas (support, confidence, lift) and a what-if price simulator |
| 💬 AI Chatbot | Ask questions in English, Hindi or Marathi — answered from the data via **Google Gemini** |
| 📄 Report & About | Executive summary, data-driven recommendations, cleaning log, downloadable report |
| 📥 Add New Data | Upload a raw CSV/Excel billing export → **cleaned automatically**, merged without duplicates, undo & history |

## Tech stack
Python · Pandas · NumPy · Scikit-learn · Plotly · Streamlit · Google Gemini API

## Run locally
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Optional: set `GEMINI_API_KEY` (free at aistudio.google.com) for full AI chatbot answers.

## Project structure
```
app.py               # Streamlit dashboard (pages, design, chatbot, data upload)
cafe_analytics.py    # analytics, ML models, cleaning & merge pipeline
cafe_clean.csv       # cleaned sample data (Jul–Sep 2026)
sample_new_data/     # a raw October file to try the "Add New Data" feature
.streamlit/config.toml
```

## Author
**Chaitanya Jadhav** — Data Analyst, Pune ·
[LinkedIn](https://www.linkedin.com/in/chaitanyatj369344259/) · [GitHub](https://github.com/chaitanya5711) ·
jadhavchaitanya5911@gmail.com

Available for freelance data analytics and dashboard projects.
