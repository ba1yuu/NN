import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
from FinMind.data import DataLoader

st.set_page_config(page_title="股票與加密貨幣走勢圖", layout="wide")


st.title("📈 股票、ETF 與幣種走勢圖（即時更新）")

# FinMind 登入設定
st.sidebar.title("🔐 FinMind 設定")
finmind_token = st.sidebar.text_input("請輸入你的 FinMind API Token", type="password")
api = None
if finmind_token:
    api = DataLoader()
    api.login_by_token(api_token=finmind_token)

    if st.sidebar.button("📋 顯示台股股票清單"):
        try:
            stock_info = api.taiwan_stock_info()
            st.sidebar.dataframe(stock_info[["stock_id", "stock_name"]].sort_values("stock_id").reset_index(drop=True))
        except Exception as e:
            st.sidebar.error(f"無法載入股票清單：{e}")

# 使用者輸入股票清單
user_input = st.text_input("請輸入股票、ETF 或幣種（格式：中文名稱:代號，用逗號分隔）", 
                          "台積電:2330.TW, Apple:AAPL, 比特幣:BTC-USD, 元大高股息ETF:0056.TW")

# 額外備註輸入區（可作為收藏筆記）
st.text_area("📌 收藏代碼備註區（不影響查詢，可記錄常用或喜愛代碼）")

refresh_rate = st.slider("資料刷新頻率（秒）", min_value=10, max_value=300, value=60, step=10)

# 使用者自選時間範圍
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("選擇開始日期", datetime.today() - timedelta(days=180))
with col2:
    end_date = st.date_input("選擇結束日期", datetime.today())

# 解析輸入文字
items = [item.strip() for item in user_input.split(',') if ':' in item]
name_code_pairs = [(name.strip(), code.strip()) for name, code in [x.split(':') for x in items]]

# 建立區塊畫圖
placeholder = st.empty()

# 資料主程式區塊
while True:
    with placeholder.container():
        for row_start in range(0, len(name_code_pairs), 4):
            cols = st.columns(4)
            for i, (name, code) in enumerate(name_code_pairs[row_start:row_start+4]):
                with cols[i]:
                    st.markdown(f"### {name}（{code}）")
                    try:
                        if code.endswith(".TW") and api:
                            stock_id = code.replace(".TW", "")
                            df = api.taiwan_stock_daily(
                                stock_id=stock_id,
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d')
                            )
                            if df.empty:
                                st.warning(f"⚠️ 找不到代碼 {code} 的資料")
                                continue
                            df.set_index("date", inplace=True)
                            st.line_chart(df['close'], height=200)
                            latest_price = float(df['close'].iloc[-1])
                            change = latest_price - float(df['close'].iloc[-2])
                            percent = (change / float(df['close'].iloc[-2])) * 100
                            st.markdown(f"成交價：{latest_price:.2f} 台幣")
                            color = "red" if change > 0 else "green" if change < 0 else "white"
                            st.markdown(f"<span style='color:{color}'>漲跌幅：{change:+.2f} ({percent:+.2f}%)</span>", unsafe_allow_html=True)
                        else:
                            df = yf.download(code, start=start_date, end=end_date)
                            if df.empty:
                                st.warning(f"⚠️ 找不到代碼 {code} 的資料")
                                continue
                            st.line_chart(df['Close'], height=200)
                            latest_price = float(df['Close'].iloc[-1])
                            change = latest_price - float(df['Close'].iloc[-2])
                            percent = (change / float(df['Close'].iloc[-2])) * 100
                            st.markdown(f"成交價：{latest_price:.2f} 美元")
                            color = "red" if change > 0 else "green" if change < 0 else "white"
                            st.markdown(f"<span style='color:{color}'>漲跌幅：{change:+.2f} ({percent:+.2f}%)</span>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"發生錯誤：{e}")

    # 等待重新整理
    time.sleep(refresh_rate)
    placeholder.empty()