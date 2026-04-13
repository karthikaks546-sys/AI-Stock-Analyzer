import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Stock Analyzer", page_icon="📈", layout="centered")

st.title("📈 AI Stock Analyzer")
st.caption("Technical analysis using RSI, MA20, Volume, Support & Resistance")
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
stock = st.text_input(
    "🔍 Enter NSE ticker symbol",
    value="TMCV.NS",
    placeholder="e.g. INFY.NS, RELIANCE.NS, TCS.NS ..."
)

analyze_btn = st.button("Analyze Stock 🚀", use_container_width=True)

# ── Main logic ────────────────────────────────────────────────────────────────
if analyze_btn:
    if not stock.strip():
        st.warning("⚠️ Please enter a ticker symbol.")
    else:
        with st.spinner("Fetching market data..."):

            # ── Get Data ──────────────────────────────────────────────────────
            data = yf.download(stock.strip(), period="6mo", progress=False)

            if data.empty:
                st.error("❌ No data found. Please check the ticker symbol and try again.")
                st.stop()

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # ── Indicators ────────────────────────────────────────────────────
            data['MA20'] = data['Close'].rolling(window=20).mean()

            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))

            data['Volume_MA20'] = data['Volume'].rolling(window=20).mean()

            # ── Support & Resistance ──────────────────────────────────────────
            support    = data['Low'].rolling(window=20).min().iloc[-1]
            resistance = data['High'].rolling(window=20).max().iloc[-1]

            # ── Buy / Sell Signals ────────────────────────────────────────────
            data['Buy_Signal']  = (data['RSI'] < 30)  & (data['Close'] < data['MA20'])
            data['Sell_Signal'] = (data['RSI'] > 70)  & (data['Close'] > data['MA20'])

            data = data.dropna()

            if data.empty:
                st.error("❌ Not enough data to compute indicators. Try a different ticker.")
                st.stop()

            # ── Latest values ─────────────────────────────────────────────────
            latest_rsi    = data['RSI'].iloc[-1].item()
            latest_price  = data['Close'].iloc[-1].item()
            latest_ma     = data['MA20'].iloc[-1].item()
            latest_volume = data['Volume'].iloc[-1].item()
            avg_volume    = data['Volume_MA20'].iloc[-1].item()
            latest_open   = data['Open'].iloc[-1].item()
            latest_close  = data['Close'].iloc[-1].item()

        st.divider()
        st.subheader(f"Results for: **{stock.upper()}**")

        # ── Metric cards ──────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Price",   f"₹{latest_price:.2f}")
        c2.metric("📊 MA20",    f"₹{latest_ma:.2f}")
        c3.metric("📉 RSI",     f"{latest_rsi:.2f}")
        c4.metric("📦 Volume",  f"{int(latest_volume):,}")

        st.divider()

        # ── Candlestick Analysis ──────────────────────────────────────────────
        st.subheader("🕯️ Candlestick Analysis")
        if abs(latest_open - latest_close) < 0.5:
            st.info("🟡 Doji → Market indecision")
        elif latest_close > latest_open:
            st.success("🟢 Bullish Candle → Buyers strong")
        else:
            st.error("🔴 Bearish Candle → Sellers strong")

        # ── Volume Analysis ───────────────────────────────────────────────────
        st.subheader("📦 Volume Analysis")
        if latest_volume > avg_volume:
            st.success("📊 High Volume → Strong move")
        else:
            st.warning("📊 Low Volume → Weak move")

        # ── Support & Resistance ──────────────────────────────────────────────
        st.subheader("📍 Support & Resistance")
        sr1, sr2 = st.columns(2)
        sr1.metric("🟢 Support",    f"₹{support:.2f}")
        sr2.metric("🔴 Resistance", f"₹{resistance:.2f}")

        # ── Price Position ────────────────────────────────────────────────────
        st.subheader("📌 Price Position")
        if latest_price <= support * 1.02:
            st.success("🟢 Near Support → Possible BUY zone")
        elif latest_price >= resistance * 0.98:
            st.error("🔴 Near Resistance → Possible SELL zone")
        else:
            st.info("⚪ In Middle Zone")

        # ── Final Decision ────────────────────────────────────────────────────
        st.subheader("🧠 Final Smart Decision")
        if latest_price < latest_ma:
            if latest_price <= support * 1.02:
                if latest_close > latest_open:
                    st.success("🟢 Possible Bounce (Bullish at Support)")
                else:
                    st.warning("⚠️ Risky Buy (Weak bounce signal)")
            else:
                st.error("📉 Strong Downtrend → Avoid")
        elif latest_price > latest_ma:
            if latest_price >= resistance * 0.98:
                if latest_close < latest_open:
                    st.error("🔴 Possible Reversal (Bearish at Resistance)")
                else:
                    st.warning("⚠️ Risky Sell (Weak reversal signal)")
            else:
                st.success("📈 Strong Uptrend → Hold / Buy")
        else:
            st.info("⚪ Sideways Market")

        # ── Trade Setup ───────────────────────────────────────────────────────
        st.subheader("🛒 Trade Setup")
        if data['Buy_Signal'].iloc[-1]:
            entry = latest_price
            tp    = entry * 1.05
            sl    = entry * 0.98
            st.success(f"🟢 **BUY TRADE**\n\n"
                       f"**Entry:** ₹{entry:.2f}  |  **Target:** ₹{tp:.2f}  |  **Stop Loss:** ₹{sl:.2f}")
        elif data['Sell_Signal'].iloc[-1]:
            entry = latest_price
            tp    = entry * 0.95
            sl    = entry * 1.02
            st.error(f"🔴 **SELL TRADE**\n\n"
                     f"**Entry:** ₹{entry:.2f}  |  **Target:** ₹{tp:.2f}  |  **Stop Loss:** ₹{sl:.2f}")
        else:
            st.info("⚪ No trade setup currently")

        buy_count  = int(data['Buy_Signal'].sum())
        sell_count = int(data['Sell_Signal'].sum())
        st.caption(f"Buy Signals (6mo): {buy_count}  |  Sell Signals (6mo): {sell_count}")

        # ── Charts ────────────────────────────────────────────────────────────
        st.divider()
        st.subheader("📈 Charts")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Price + MA + signals
        ax1.plot(data['Close'], label="Close Price")
        ax1.plot(data['MA20'],  label="MA20")
        ax1.scatter(data.index[data['Buy_Signal']],
                    data.loc[data['Buy_Signal'],  'Close'],
                    marker='^', color='green', label='Buy Signal', zorder=5)
        ax1.scatter(data.index[data['Sell_Signal']],
                    data.loc[data['Sell_Signal'], 'Close'],
                    marker='v', color='red',   label='Sell Signal', zorder=5)
        ax1.set_title("Price & Moving Average (MA20)")
        ax1.legend()

        # RSI
        ax2.plot(data['RSI'], label="RSI", color='purple')
        ax2.axhline(70, color='red',   linestyle='--', linewidth=0.8)
        ax2.axhline(30, color='green', linestyle='--', linewidth=0.8)
        ax2.set_title("RSI Indicator")
        ax2.legend()

        plt.tight_layout()
        st.pyplot(fig)

        st.divider()
        st.caption("⚠️ **Disclaimer:** This app is for learning purposes only. Not financial advice.")