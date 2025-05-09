import pandas as pd
import streamlit as st

# 初始化 session_state 用于存储上传的文件
if 'conference_file' not in st.session_state:
    st.session_state.conference_file = None

if 'paper_file' not in st.session_state:
    st.session_state.paper_file = None

# 上传会议文件，指定唯一key
conference_file = st.file_uploader("上传会议文件", type=["xlsx"], key="conference_uploader")

# 上传论文文件，指定唯一key
paper_file = st.file_uploader("上传论文文件", type=["pdf", "docx"], key="paper_uploader")

# 处理会议文件
if conference_file is not None:
    try:
        # 读取 Excel 文件并存入 session_state
        st.session_state.conference_file = pd.read_excel(conference_file)
        st.success("会议文件上传成功！")
    except Exception as e:
        st.error(f"会议文件读取出错: {e}")
        st.session_state.conference_file = None

# 处理论文文件
if paper_file is not None:
    try:
        # 论文文件处理逻辑（仅显示文件名）
        st.session_state.paper_file = paper_file
        st.success("论文文件上传成功！")
    except Exception as e:
        st.error(f"论文文件读取出错: {e}")
        st.session_state.paper_file = None

# 显示会议文件和论文文件内容（仅预览前几行）
if st.session_state.conference_file is not None:
    st.write("会议文件内容预览：")
    st.dataframe(st.session_state.conference_file.head())

if st.session_state.paper_file is not None:
    st.write(f"论文文件：{st.session_state.paper_file.name}")

# 清除会议文件和论文文件按钮
if st.session_state.conference_file is not None:
    if st.button("清除会议文件"):
        st.session_state.conference_file = None
        st.experimental_rerun()

if st.session_state.paper_file is not None:
    if st.button("清除论文文件"):
        st.session_state.paper_file = None
        st.experimental_rerun()

# 确保会议文件已上传且包含必要字段
if st.session_state.conference_file is None:
    st.error("❌ 请先上传会议文件")
    st.stop()

# 获取实际列名
columns = st.session_state.conference_file.columns.str.strip()

# 检查是否存在 '会议名' 字段
if '会议名' not in columns:
    st.error("❌ 缺少必要字段：会议名")
    st.stop()

# 显示会议名称字段的内容
conference_name = st.session_state.conference_file['会议名']
st.write("会议名称字段内容：", conference_name.head())

# 进一步处理论文文件（具体实现根据需求进行）
if st.session_state.paper_file is not None:
    # 处理论文文件的逻辑
    pass  # 根据需要提取论文的内容
