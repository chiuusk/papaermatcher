import pandas as pd
import streamlit as st

# 设置session_state存储状态
if 'conference_file' not in st.session_state:
    st.session_state.conference_file = None

# 上传会议文件
conference_file = st.file_uploader("上传会议文件", type=["xlsx"])

# 如果有文件上传，读取文件并存储
if conference_file is not None:
    try:
        # 读取 Excel 文件并存入 session_state
        st.session_state.conference_file = pd.read_excel(conference_file)
        st.success("会议文件上传成功！")
    except Exception as e:
        st.error(f"文件读取出错: {e}")
        st.session_state.conference_file = None

# 如果文件已上传，显示文件内容
if st.session_state.conference_file is not None:
    st.write("会议文件内容预览：")
    st.dataframe(st.session_state.conference_file.head())

# 显示清除文件按钮
if st.session_state.conference_file is not None:
    if st.button("清除会议文件"):
        st.session_state.conference_file = None
        st.experimental_rerun()

# 检查是否存在文件
if st.session_state.conference_file is None:
    st.error("❌ 请先上传会议文件")
    st.stop()

# 获取实际列名
columns = st.session_state.conference_file.columns.str.strip()

# 定义必须的列名（包括 '会议名' 和 '会议名称'）
required_cols = ['会议名称', '会议名', '会议方向', '会议主题方向', '细分关键词', '动态出版标记', '截稿时间', '官网链接']

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

# 其他处理逻辑...
