import streamlit as st
import pandas as pd
import pdfplumber
import docx
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import os

st.set_page_config(page_title="论文匹配推荐系统", layout="wide")
st.title("📄 论文智能匹配推荐会议")

model = SentenceTransformer("all-MiniLM-L6-v2")

# 文件状态初始化
if "paper_file" not in st.session_state:
    st.session_state.paper_file = None
if "conference_file" not in st.session_state:
    st.session_state.conference_file = None


# -------------------- 文件上传区块 --------------------

st.header("1️⃣ 上传会议文件（Excel）")
conf_col1, conf_col2 = st.columns([4, 1])

with conf_col1:
    uploaded_conf = st.file_uploader(
        "上传包含会议信息的 Excel 文件（会议名称、方向、主题、细分关键词、官网链接、截稿时间...）",
        type=["xlsx"],
        key="conference_uploader"
    )
    if uploaded_conf:
        st.session_state.conference_file = uploaded_conf

with conf_col2:
    if st.button("🗑 清除会议文件"):
        st.session_state.conference_file = None


st.divider()

st.header("2️⃣ 上传论文文件（PDF / Word）")
paper_col1, paper_col2 = st.columns([4, 1])

with paper_col1:
    uploaded_paper = st.file_uploader(
        "上传需要匹配的论文文件",
        type=["pdf", "docx"],
        key="paper_uploader"
    )
    if uploaded_paper:
        st.session_state.paper_file = uploaded_paper

with paper_col2:
    if st.button("🗑 清除论文文件"):
        st.session_state.paper_file = None

st.divider()

# -------------------- 工具函数 --------------------

def extract_text(file):
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    else:
        return ""
    return text


def extract_sections(text):
    # 简单分段抽取 title, abstract, keywords, conclusion（可优化）
    sections = {
        "title": text.split("\n")[0],
        "abstract": "",
        "keywords": "",
        "conclusion": "",
    }
    lowered = text.lower()
    if "abstract" in lowered:
        sections["abstract"] = text[lowered.find("abstract"):lowered.find("introduction") if "introduction" in lowered else 1000]
    if "keywords" in lowered:
        start = lowered.find("keywords")
        end = lowered.find("\n", start + 8)
        sections["keywords"] = text[start:end].replace("Keywords", "").replace(":", "").strip()
    if "conclusion" in lowered:
        start = lowered.find("conclusion")
        sections["conclusion"] = text[start:start + 800]
    return sections


def compute_similarity(text1, text2):
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    return float(util.cos_sim(emb1, emb2)[0])


# -------------------- 匹配逻辑 --------------------

def match_and_display(paper_text, conference_df):
    sections = extract_sections(paper_text)
    combined_text = " ".join([sections[k] for k in ["title", "abstract", "keywords", "conclusion"] if sections[k]])

    best_matches = []

    for _, row in conference_df.iterrows():
        conf_name = row["会议名称"]
        direction = str(row.get("会议方向", ""))
        topic = str(row.get("会议主题方向", ""))
        sub_keywords = str(row.get("细分关键词", ""))
        deadline = str(row.get("截稿时间", ""))
        link = row.get("官网链接", "")

        full_conf_info = " ".join([direction, topic, sub_keywords])
        similarity = compute_similarity(combined_text, full_conf_info)

        # 匹配关键词记录
        matched_terms = []
        for word in sub_keywords.split(","):
            word = word.strip().lower()
            if word and word in combined_text.lower():
                matched_terms.append(word)

        try:
            deadline_date = pd.to_datetime(deadline)
            days_left = (deadline_date - datetime.now()).days
        except:
            days_left = "未知"

        best_matches.append({
            "会议名称": conf_name,
            "匹配分数": round(similarity, 3),
            "匹配关键词": ", ".join(matched_terms) if matched_terms else "无明显关键词匹配",
            "官网链接": link,
            "距离截稿时间": f"{days_left} 天" if isinstance(days_left, int) else "无法解析"
        })

    sorted_matches = sorted(best_matches, key=lambda x: x["匹配分数"], reverse=True)[:2]

    st.subheader("📌 推荐会议")
    for match in sorted_matches:
        st.markdown(f"""
        **会议名称：** {match['会议名称']}  
        **匹配分数：** {match['匹配分数']}  
        **关键词匹配：** {match['匹配关键词']}  
        **官网链接：** [{match['官网链接']}]({match['官网链接']})  
        **距离截稿时间：** {match['距离截稿时间']}  
        ---
        """)


# -------------------- 主执行逻辑 --------------------

if st.session_state.paper_file and st.session_state.conference_file:
    try:
        conf_df = pd.read_excel(st.session_state.conference_file)
        paper_text = extract_text(st.session_state.paper_file)
        if not paper_text.strip():
            st.error("论文内容为空，可能提取失败")
        else:
            match_and_display(paper_text, conf_df)
    except Exception as e:
        st.error(f"处理时出错：{e}")
