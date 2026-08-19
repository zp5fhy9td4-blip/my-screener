import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="全自動株スクリーナー", page_icon="🍎", layout="wide"
)
st.title("🍎 リアルタイム銘柄スクリーナー")

# 監視対象の低位・材料株リスト
SCAN_LIST = [
    "3323",
    "8946",
    "4591",
    "5856",
    "3936",
    "2315",
    "3782",
    "2330",
    "6731",
    "1757",
    "3814",
]


@st.cache_data(ttl=300)
def auto_scan():
    results = []
    for code in SCAN_LIST:
        ticker = f"{code}.T"
        try:
            df = yf.Ticker(ticker).history(period="1mo")
            if len(df) >= 20:
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                pct = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

                avg_vol = df["Volume"].iloc[-6:-1].mean()
                vol_ratio = (
                    latest["Volume"] / avg_vol if avg_vol > 0 else 0.0
                )

                # RSI(14) の安全な計算
                delta = df["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]

                if loss == 0 or pd.isna(loss):
                    rsi = 100.0 if gain > 0 else 50.0
                else:
                    rs = gain / loss
                    rsi = 100.0 - (100.0 / (1.0 + rs))

                # 移動平均
                ma5 = df["Close"].rolling(5).mean().iloc[-1]
                ma20 = df["Close"].rolling(20).mean().iloc[-1]

                results.append(
                    {
                        "コード": code,
                        "現在値": f"{round(latest['Close'], 1)}円",
                        "前日比%": round(pct, 2),
                        "出来高倍率": round(vol_ratio, 2),
                        "RSI": round(rsi, 1),
                        "5日線": round(ma5, 1),
                        "20日線": round(ma20, 1),
                    }
                )
        except Exception:
            pass
    return pd.DataFrame(results)


with st.spinner("最新データを自動スキャン中..."):
    df = auto_scan()

if not df.empty:
    tab1, tab2 = st.tabs(["🔥 出来高急増（デイ候補）", "📉 押し目候補"])

    with tab1:
        # 出来高1.5倍以上かつ前日比プラス
        day_df = df[(df["出来高倍率"] >= 1.5) & (df["前日比%"] > 0)]
        if not day_df.empty:
            st.dataframe(day_df, use_container_width=True)
        else:
            st.info("条件に合う急増銘柄はありません。全監視リストを表示します:")
            st.dataframe(df, use_container_width=True)

    with tab2:
        # 5日線 > 20日線 かつ RSI 50以下
        oshi_df = df[(df["5日線"] > df["20日線"]) & (df["RSI"] <= 50)]
        if not oshi_df.empty:
            st.dataframe(oshi_df, use_container_width=True)
        else:
            st.info("現在、押し目条件に該当する銘柄はありません。")

