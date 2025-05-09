import streamlit as st
import pdfplumber
import docx
import pandas as pd
import datetime
import re
import nltk
from sentence_transformers import SentenceTransformer, util

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

model = SentenceTransformer('all-MiniLM-L6-v2')


# ========== 工具函数 ==========

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text


def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_sections(text):
    text = text.replace('\n', ' ')
    sentences = sent_tokenize(text)

    title = sentences[0] if len(sentences) > 0 else ""
    abstract = next((s for s in sentences if "abstract" in s.lower()), "")
    keywords = re.findall(r"[Kk]eywords?\s*[:：]?\s*(.*?)\.", text)
    conclusion = next((s for s in sentences[::-1] if "conclusion" in s.lower()), "")

    return {
        "title": title.strip(),
        "abstract": abstract.strip(),
        "keywords": keywords[0].strip() if keywords else "",
        "conclusion": conclusion.strip()
    }


def match_conference(paper_embedding, conference_df):
    results = []

    for _, row in conference_df.iterrows():
        keywords = f"{row['会议方向']} {row['会议主题方向']} {row['细分关键词']}"
        conf_embedding = model.encode(keywords, convert_to_tensor=True)
        score = util.cos_sim(paper_embedding, conf_embedding).item()

        # 提取会议相关关键词和方向
        matched_keywords = []
        for keyword in [row['会议方向'], row['会议主题方向'], row['细分关键词']]:
            if keyword.lower() in paper_embedding.lower():
                matched_keywords.append(keyword)

        results.append({
            "会议名称": row["会议名称"],
            "官网链接": row["官网链接"],
            "截稿时间": row["截稿时间"],
            "匹配度": score,
            "匹配关键词": matched_keywords,
            "会议方向": row['会议方向'],
            "细分关键词": row['细分关键词']
        })

    top2 = sorted(results, key=lambda x: x["匹配度"], reverse=True)[:2]

    # 计算距离截稿时间
    for conf in top2:
        try:
            conf["剩余天数"] = (
                datetime.datetime.strptime(conf["截稿时间"], "%Y-%m-%d") - datetime.datetime.now()
            ).days
        except:
            conf["剩余天数"] = "未知"
    
    return top2


# ========== Streamlit 界面 ==========

st.title("📄 论文学科方向识别与会议推荐工具")

# 上传论文
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

    # 论文向量化
    combined_text = " ".join([
        sections["title"], sections["abstract"], sections["keywords"], sections["conclusion"]
    ])
    paper_embedding = model.encode(combined_text, convert_to_tensor=True)

    # 上传会议文件
    st.subheader("📋 上传会议信息文件（CSV）")
    conference_file = st.file_uploader("包含字段：会议名称、会议方向、会议主题方向、细分关键词、截稿时间（YYYY-MM-DD）、官网链接", type=["csv"])

    if conference_file:
        conf_df = pd.read_csv(conference_file)
        st.success("会议信息读取成功，共加载 {} 条记录。".format(len(conf_df)))

        recommendations = match_conference(paper_embedding, conf_df)

        st.subheader("🎯 推荐会议")
        for rec in recommendations:
            st.markdown(f"""
            ### [{rec['会议名称']}]({rec['官网链接']})
            - **匹配理由**: 论文中的关键词与会议方向匹配：{', '.join(rec['匹配关键词'])}
            - **匹配度**: {rec['匹配度']:.2f}
            - **距离截稿时间**: {rec['剩余天数']} 天
            """)

# 底部
st.markdown("---")
st.markdown("由 GPT + Sentence Transformers 提供语义分析支持")
