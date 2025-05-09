import streamlit as st
import pandas as pd
import os
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import tempfile

# 加载语义模型（小模型，适合部署）
model = SentenceTransformer('all-MiniLM-L6-v2')

st.set_page_config(layout="wide")
st.title("📄 论文匹配会议推荐系统")

# 文件上传区域（左右布局）
left_col, right_col = st.columns(2)

with left_col:
    st.header("📁 上传会议文件")
    conference_file = st.file_uploader("上传会议文件（包含‘会议名’、‘会议方向’、‘会议主题方向’、‘细分方向’等字段）", type=["xlsx"], key="conf")
    if st.button("❌ 清除会议文件", key="clear_conf"):
        st.experimental_rerun()

with right_col:
    st.header("📄 上传论文文件")
    paper_file = st.file_uploader("上传PDF论文文件（支持中文）", type=["pdf"], key="paper")
    if st.button("❌ 清除论文文件", key="clear_paper"):
        st.experimental_rerun()

# 功能函数：提取PDF纯文本
def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    text = ""
    with open(tmp_path, 'rb') as f:
        pdf = PdfReader(f)
        for page in pdf.pages:
            text += page.extract_text() or ""
    os.remove(tmp_path)
    return text.strip()

# 匹配逻辑
def match_conferences(paper_text, df):
    paper_embedding = model.encode(paper_text, convert_to_tensor=True)
    results = []

    for _, row in df.iterrows():
        row_text = " ".join([str(row.get(col, '')) for col in ['会议名', '会议方向', '会议主题方向', '细分方向']])
        conf_embedding = model.encode(row_text, convert_to_tensor=True)
        score = float(util.cos_sim(paper_embedding, conf_embedding))
        results.append({
            "会议名": row.get("会议名", "N/A"),
            "匹配度": round(score * 100, 2),
            "会议方向": row.get("会议方向", ""),
            "主题方向": row.get("会议主题方向", ""),
            "细分方向": row.get("细分方向", "")
        })

    results = sorted(results, key=lambda x: x["匹配度"], reverse=True)
    return results[:5]

# 主逻辑
if conference_file:
    try:
        conf_df = pd.read_excel(conference_file, engine="openpyxl")
        conf_df.columns = conf_df.columns.str.strip()

        # 字段标准化
        if "会议名称" in conf_df.columns and "会议名" not in conf_df.columns:
            conf_df.rename(columns={"会议名称": "会议名"}, inplace=True)

        required_fields = ["会议名", "会议方向", "会议主题方向", "细分方向"]
        if not all(field in conf_df.columns for field in required_fields):
            st.warning("❌ 缺少必要字段：会议名 / 会议方向 / 会议主题方向 / 细分方向")
        elif paper_file:
            with st.spinner("⏳ 正在提取论文内容..."):
                paper_text = extract_text_from_pdf(paper_file)
            if not paper_text:
                st.error("❌ 无法从PDF中提取文本。请检查文件内容。")
            else:
                st.success("✅ 提取完成，正在匹配...")
                top_matches = match_conferences(paper_text, conf_df)
                st.markdown("### 🎯 匹配结果：")
                st.table(pd.DataFrame(top_matches))
    except Exception as e:
        st.error(f"❌ 文件处理出错：{e}")
else:
    st.info("请先上传会议文件和论文文件。")
