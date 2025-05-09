import pandas as pd
import streamlit as st

# 读取会议文件
if 'conference_file' in st.session_state:
    try:
        conference_file = pd.read_excel(st.session_state.conference_file)
        st.session_state.conference_file = conference_file
    except Exception as e:
        st.error(f"文件读取出错: {e}")
        st.stop()

# 定义必须的列名（包括 '会议名' 和 '会议名称'）
required_cols = ['会议名称', '会议名', '会议方向', '会议主题方向', '细分关键词', '动态出版标记', '截稿时间', '官网链接']

# 获取实际列名
columns = st.session_state.conference_file.columns.str.strip()

# 检查是否存在 '会议名' 或 '会议名称'
if '会议名称' not in columns and '会议名' not in columns:
    st.error("❌ 缺少必要字段：会议名称 或 会议名")
    st.stop()

# 确保没有缺少其他必要的字段
for col in required_cols:
    if col not in columns:
        st.error(f"❌ 缺少必要字段：{col}")
        st.stop()

# 处理"会议名称"或"会议名"字段
conference_name = None
if '会议名称' in columns:
    conference_name = st.session_state.conference_file['会议名称']
elif '会议名' in columns:
    conference_name = st.session_state.conference_file['会议名']

# 显示会议名称，确认字段是否加载成功
st.write("会议名称字段内容：", conference_name.head())
