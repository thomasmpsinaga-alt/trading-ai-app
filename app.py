import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import requests
from openai import OpenAI
import os

# ================= CONFIG =================
st.set_page_config(page_title="Trading AI PRO MAX", layout="wide")
st.title("🚀 Trading AI PRO MAX")

# ================= INPUT =================
pair = st.selectbox("Pair", ["XAUUSD", "EURUSD", "BTC-USD"])
tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h"])
balance = st.number_input("Balance", value=1000)

api_key = st.text_input("OpenAI API Key", type="password")

uploaded = st.file_uploader("Upload Chart (Optional)")

# ================= DATA =================
def get_data(symbol, interval):
    if symbol == "XAUUSD":
        symbol = "GC=F"

    df = yf.download(symbol, period="5d", interval=interval)
    df.dropna(inplace=True)
    return df

# ================= INDICATORS =================
def add_indicators(df):
    df["ema50"] = ta.trend.ema_indicator(df["Close"], 50)
    df["ema200"] = ta.trend.ema_indicator(df["Close"], 200)
    df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    df["adx"] = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"]).adx()
    df["atr"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()
    return df

# ================= NEWS =================
def get_news():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        data = requests.get(url).json()
        return [n for n in data if n.get("impact") == "High"][:3]
    except:
        return []

# ================= AI =================
def ai_analysis(prompt, key):
    try:
        client = OpenAI(api_key=key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except:
        return "AI error"

# ================= MAIN =================
if st.button("🔥 Analisis Sekarang"):
    with st.spinner("Analyzing..."):

        df = get_data(pair, tf)
        df = add_indicators(df)

        last = df.iloc[-1]

        # TREND
        trend = "bullish" if last["ema50"] > last["ema200"] else "bearish"

        # ENTRY
        entry = last["Close"]
        sl = entry - last["atr"] if trend == "bullish" else entry + last["atr"]
        tp1 = entry + (entry - sl)
        tp2 = entry + 2 * (entry - sl)

        # CONFIDENCE
        score = 0
        if trend == "bullish":
            score += 1
        if last["rsi"] < 30:
            score += 1
        if last["adx"] > 25:
            score += 1

        confidence = score * 33

        signal = "WAIT"
        if score >= 2:
            signal = "BUY" if trend == "bullish" else "SELL"

        # NEWS
        news = get_news()

        # AI TEXT
        prompt = f"""
        Buat analisis trading profesional:

        Pair: {pair}
        Trend: {trend}
        Price: {entry}
        RSI: {last['rsi']}
        ADX: {last['adx']}

        Format seperti signal trader pro.
        """

        ai_text = ai_analysis(prompt, api_key)

        # OUTPUT
        st.subheader("📊 ANALISIS AI")
        st.write(ai_text)

        st.subheader("🔥 TRADE SETUP")

        st.markdown(f"""
**Signal:** {signal}  
**Confidence:** {confidence}%

Entry: {entry}  
SL: {sl}  
TP1: {tp1}  
TP2: {tp2}
""")

        if len(news) > 0:
            st.error("🚨 HIGH IMPACT NEWS — HINDARI TRADING")

        st.success("✅ Selesai")
