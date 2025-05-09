import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import tempfile
import os

st.set_page_config(layout="wide")
st.title("📄 论文匹配会议助手")

# 初始化模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 初始化 session_state
for key in ["conference_file", "paper_file"]:
    if key not in st.session_state:
        st.session_state[key] = None

# 左右布局
col1, col2 = st.columns(2)

# 上传会议文件
with col1:
    st.subheader("📅 上传会议文件")
    conference_uploaded = st.file_uploader("选择包含会议信息的Excel文件", type=["xlsx"], key="conf_uploader")
    if st.button("❌ 清除会议文件"):
        st.session_state.conference_file = None
        conference_uploaded = None

    if conference_uploaded:
        try:
            df = pd.read_excel(conference_uploaded)
            df.columns = df.columns.str.strip()

            # 字段名标准化
            rename_map = {}
            if "会议名称" in df.columns:
                rename_map["会议名称"] = "会议名"
            df.rename(columns=rename_map, inplace=True)

            required_columns = ["会议名", "会议方向", "会议主题方向", "细分关键词"]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                st.error(f"❌ 缺少必要字段：{ ' / '.join(missing) }")
            else:
                st.session_state.conference_file = df
                st.success("✅ 会议文件上传并读取成功")
        except Exception as e:
            st.error(f"❌ 会议文件读取失败：{e}")

# 上传论文文件
with col2:
    st.subheader("📝 上传论文文件（PDF）")
    paper_uploaded = st.file_uploader("上传论文 PDF 文件", type=["pdf"], key="paper_uploader")
    if st.button("❌ 清除论文文件"):
        st.session_state.paper_file = None
        paper_uploaded = None

    if paper_uploaded:
        try:
            # 临时保存 PDF
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, paper_uploaded.name)
            with open(temp_path, "wb") as f:
                f.write(paper_uploaded.read())

            # 读取 PDF 文本
            reader = PdfReader(temp_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            st.session_state.paper_file = text.strip()
            st.success("✅ 论文内容提取成功")
        except Exception as e:
            st.error(f"❌ PDF 处理失败：{e}")

# 执行匹配
if st.session_state.conference_file is not None and st.session_state.paper_file is not None:
    st.divider()
    st.subheader("📊 匹配结果")

    paper_embedding = model.encode(st.session_state.paper_file, convert_to_tensor=True)
    results = []

    for _, row in st.session_state.conference_file.iterrows():
        row_text = " ".join(str(row[col]) for col in ["会议方向", "会议主题方向", "细分关键词"] if pd.notna(row[col]))
        row_embedding = model.encode(row_text, convert_to_tensor=True)
        similarity = util.cos_sim(paper_embedding, row_embedding).item()
        results.append({
            "会议名": row["会议名"],
            "会议方向": row["会议方向"],
            "会议主题方向": row["会议主题方向"],
            "细分关键词": row["细分关键词"],
            "匹配分数": round(similarity, 4)
        })

    sorted_results = sorted(results, key=lambda x: x["匹配分数"], reverse=True)
    st.dataframe(pd.DataFrame(sorted_results), use_container_width=True)
