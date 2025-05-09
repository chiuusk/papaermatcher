import pandas as pd

# 定义必须的列名（包括 '会议名' 和 '会议名称' ）
required_cols = ['会议名称', '会议名', '会议方向', '会议主题方向', '细分关键词', '动态出版标记', '截稿时间', '官网链接']

# 判断并清理列名中的空格
if '会议名称' not in st.session_state.conference_file.columns.str.strip() and '会议名' not in st.session_state.conference_file.columns.str.strip():
    st.error(f"❌ 缺少必要字段：会议名称 或 会议名")
    st.stop()

# 确保没有缺少任何必需的字段
for col in required_cols:
    if col not in st.session_state.conference_file.columns.str.strip():
        st.error(f"❌ 缺少必要字段：{col}")
        st.stop()

# 处理"会议名称"或"会议名"字段
conference_name = None
if '会议名称' in st.session_state.conference_file.columns.str.strip():
    conference_name = st.session_state.conference_file['会议名称']
elif '会议名' in st.session_state.conference_file.columns.str.strip():
    conference_name = st.session_state.conference_file['会议名']

# 显示会议名称，确认字段是否加载成功
st.write("会议名称字段内容：", conference_name.head())
