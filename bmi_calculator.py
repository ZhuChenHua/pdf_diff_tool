import streamlit as st

# 设置应用标题
st.title("BMI 计算器")

# 添加输入框
height = st.number_input("请输入您的身高（厘米）", min_value=0.0, step=0.1)
weight = st.number_input("请输入您的体重（公斤）", min_value=0.0, step=0.1)

# 计算 BMI
if st.button("计算 BMI"):
    if height > 0 and weight > 0:
        bmi = weight / ((height / 100) ** 2)
        st.success(f"您的 BMI 是：{bmi:.2f}")
        if bmi < 18.5:
            st.warning("您的体重偏轻")
        elif bmi < 24:
            st.info("您的体重正常")
        else:
            st.error("您的体重偏重")
    else:
        st.error("请输入有效的身高和体重")
