import streamlit as st
import pdfplumber
import docx
import pandas as pd
import datetime
import re
from sentence_transformers import SentenceTransformer, util

# 使用轻量模型并强制 CPU
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

# ========== 工具函数 ==========

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def split_into_sentences(text):
    # 简易句子切分，不依赖 nltk
    text = text.replace('\n', ' ')
    return re.split(r'(?<=[。.!?])\s+', text)

def extract_sections(text):
    sentences = split_into_sentences(text)
    title = sentences[0] if len(sentences) > 0 else ""
    abstract = ""
    conclusion = ""

    for i, sentence in enumerate(sentences):
        if 'abstract' in sentence.lower():
            abstract = ' '.join(sentences[i:i+3])
        elif '关键词' in sentence or 'keywords' in sentence.lower():
            keywords_match = re.search(r'(关键词|keywords)\s*[:：]?\s*(.*)', sentence, re.IGNORECASE)
            if keywords_match:
                keywords = keywords_match.group(2).strip()
            else:
                keywords = ""
        elif 'conclusion' in sentence.lower() or '结论' in sentence:
            conclusion = ' '.join(sentences[i:i+3])

    return {
        "title": title.strip(),
        "abstract": abstract.strip(),
        "keywords": keywords if 'keywords' in locals() else "",
        "conclusion": conclusion.strip()
    }

def match_conference(paper_embedding, conference_df):
    results = []

    for _, row in conference_df.iterrows():
        conf_text = f"{row['会议方向']} {row['会议主题方向']} {row['细分关键词']}"
        conf_embedding = model.encode(conf_text, convert_to_tensor=True)
        score = util.cos_sim(paper_embedding, conf_embedding).item()

        matched_terms = []
        for term in row['细分关键词'].split(','):
            if term.strip().lower() in conf_text.lower():
                matched_terms.append(term.strip())

        results.append({
            "会议名称": row["会议名称"],
            "官网链接": row["官网链接"],
            "截稿时间": row["截稿时间"],
            "匹配度": score,
            "匹配关键词": matched_terms,
            "会议方向": row['会议方向'],
            "细分关键词": row['细分关键词']
        })

    top2 = sorted(results, key=lambda x: x["匹配度"], reverse=True)[:2]

    for conf in top2:
        try:
            conf["剩余天数"] = (
                datetime.datetime.strptime(conf["截稿时间"], "%Y-%m-%d") - datetime.datetime.now()
            ).days
        except:
            conf["剩余天数"] = "未知"

    return top2

# ========== Streamlit UI ==========

st.title("📄 论文学科方向识别与会议推荐工具")

paper_file = st.file_uploader("上传论文（PDF 或 Word）", type=["pdf", "docx"])
if paper_file:
    if paper_file.type == "application/pdf":
        full_text = extract_text_from_pdf(paper_file)
    else:
        full_text = extract_text_from_docx(paper_file)

    sections = extract_sections(full_text)
    st.subheader("📌 提取信息")
    st.markdown(f"**标题**: {sections['title']}")
    st.markdown(f"**摘要**: {sections['abstract']}")
    st.markdown(f"**关键词**: {sections['keywords']}")
    st.markdown(f"**结论段落**: {sections['conclusion']}")

    combined_text = " ".join([
        sections["title"], sections["abstract"], sections["keywords"], sections["conclusion"]
    ])
    paper_embedding = model.encode(combined_text, convert_to_tensor=True)

    st.subheader("📋 上传会议信息文件（CSV）")
    conference_file = st.file_uploader("包含字段：会议名称、会议方向、会议主题方向、细分
