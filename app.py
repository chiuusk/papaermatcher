import pandas as pd
import streamlit as st

# 页面设置
st.set_page_config(page_title="论文会议匹配助手", layout="wide")
st.title("📄 智能论文会议匹配")

# 初始化 session_state
if 'conference_df' not in st.session_state:
    st.session_state.conference_df = None

if 'paper_info' not in st.session_state:
    st.session_state.paper_info = None

# 创建左右列
left_col, right_col = st.columns(2)

# 左侧：上传会议文件
with left_col:
    st.subheader("📅 上传会议文件")
    conference_file = st.file_uploader("上传Excel格式的会议列表", type=["xlsx"], key="conf_upload")
    if conference_file:
        try:
            df = pd.read_excel(conference_file)
            df.columns = df.columns.str.strip()
            # 自动统一列名
            if '会议名称' in df.columns:
                df.rename(columns={'会议名称': '会议名'}, inplace=True)
            if '会议名' not in df.columns:
                st.error("❌ 文件中缺少“会议名”字段！请检查后重新上传。")
            else:
                st.session_state.conference_df = df
                st.success("✅ 会议文件读取成功！")
        except Exception as e:
            st.error(f"会议文件读取失败：{e}")

# 右侧：上传论文信息（仅提取文本）
with right_col:
    st.subheader("📝 上传论文文件")
    paper_file = st.file_uploader("上传PDF或DOCX论文文件", type=["pdf", "docx"], key="paper_upload")
    if paper_file:
        # 暂时用文件名模拟论文标题
        st.session_state.paper_info = {"标题": paper_file.name}
        st.success("✅ 论文文件上传成功！")

# 只有在两个文件都上传成功后才进行匹配
if st.session_state.conference_df is not None and st.session_state.paper_info is not None:
    st.divider()
    st.subheader("📊 匹配推荐结果")

    # 简化模拟匹配逻辑：假设会议方向字段叫“方向”，我们模拟判断
    paper_title = st.session_state.paper_info["标题"]
    paper_keywords = paper_title.lower().split()

    # 获取会议表
    df = st.session_state.conference_df.copy()

    # 简单关键词匹配逻辑（示意）
    matched_rows = []
    for idx, row in df.iterrows():
        row_text = " "._
