import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# 初始化模型
model = SentenceTransformer("all-MiniLM-L6-v2")

st.set_page_config(layout="wide")
st.title("📄 论文 - 会议匹配工具")

# 左右两列布局
left_col, right_col = st.columns(2)

# 上传会议文件
with left_col:
    st.header("📌 上传会议文件")
    conference_file = st.file_uploader("上传包含字段：会议名、会议方向、主题方向、细分领域", type=["xlsx"], key="conf_uploader")

    if st.button("❌ 清除会议文件", key="clear_conf"):
        st.session_state.conf_uploader = None
        conference_file = None

# 上传论文文件
with right_col:
    st.header("📄 上传论文文件")
    paper_file = st.file_uploader("上传包含标题、摘要、关键词字段的文件", type=["xlsx"], key="paper_uploader")

    if st.button("❌ 清除论文文件", key="clear_paper"):
        st.session_state.paper_uploader = None
        paper_file = None

# 显示匹配结果
if conference_file and paper_file:
    try:
        # 读取会议文件
        df_conf = pd.read_excel(conference_file, engine="openpyxl")
        df_conf.columns = df_conf.columns.str.strip()

        # 字段兼容处理
        if "会议名称" in df_conf.columns:
            df_conf.rename(columns={"会议名称": "会议名"}, inplace=True)

        required_conf_cols = {"会议名", "会议方向", "会议主题方向", "会议细分领域"}
        if not required_conf_cols.issubset(set(df_conf.columns)):
            st.error(f"❌ 会议文件缺少必要字段：{required_conf_cols - set(df_conf.columns)}")
        else:
            # 读取论文文件
            df_paper = pd.read_excel(paper_file, engine="openpyxl")
            df_paper.columns = df_paper.columns.str.strip()

            required_paper_cols = {"标题", "摘要", "关键词"}
            if not required_paper_cols.issubset(set(df_paper.columns)):
                st.error(f"❌ 论文文件缺少必要字段：{required_paper_cols - set(df_paper.columns)}")
            else:
                st.success("✅ 文件读取成功，正在匹配...")

                paper_texts = df_paper["标题"] + " " + df_paper["摘要"] + " " + df_paper["关键词"]
                paper_embeddings = model.encode(paper_texts.tolist(), convert_to_tensor=True)

                conf_texts = df_conf["会议方向"].astype(str) + " " + df_conf["会议主题方向"].astype(str) + " " + df_conf["会议细分领域"].astype(str)
                conf_embeddings = model.encode(conf_texts.tolist(), convert_to_tensor=True)

                results = []
                for i, paper_emb in enumerate(paper_embeddings):
                    sims = util.cos_sim(paper_emb, conf_embeddings)[0]
                    best_idx = sims.argmax().item()
                    best_score = sims[best_idx].item()
                    best_row = df_conf.iloc[best_idx]
                    results.append({
                        "论文标题": df_paper.loc[i, "标题"],
