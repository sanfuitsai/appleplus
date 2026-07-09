import streamlit as st
import pandas as pd

st.title("學習時間分析器")

st.write("輸入每天的讀書時間，看看自己的學習狀況。")

day1 = st.number_input("星期一讀書幾分鐘？", min_value=0, value=30)
day2 = st.number_input("星期二讀書幾分鐘？", min_value=0, value=40)
day3 = st.number_input("星期三讀書幾分鐘？", min_value=0, value=50)
day4 = st.number_input("星期四讀書幾分鐘？", min_value=0, value=60)
day5 = st.number_input("星期五讀書幾分鐘？", min_value=0, value=45)

data = {
    "星期": ["一", "二", "三", "四", "五"],
    "讀書時間": [day1, day2, day3, day4, day5]
}

df = pd.DataFrame(data)

st.subheader("資料表")
st.dataframe(df)

st.subheader("長條圖")
st.bar_chart(df.set_index("星期"))

average = df["讀書時間"].mean()

st.write(f"平均每天讀書時間：{average:.1f} 分鐘")

if average < 30:
    st.warning("平均時間偏少，可以先從每天固定 20～30 分鐘開始。")
elif average < 60:
    st.info("學習習慣正在建立，可以嘗試增加複習時間。")
else:
    st.success("你的學習時間很穩定，接下來可以加強學習方法。")