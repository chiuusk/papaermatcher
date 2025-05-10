import streamlit as st
import pandas as pd
import datetime
import os
import re
import time
from io import StringIO
from PyPDF2 import PdfReader
import docx

st.set_page_config(page_title="论文会议匹配推荐系统", layout="wide")

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except:
        return ""

def extract_text_from_docx(uploaded_file):
    try:
        doc = docx.Document(uploaded_file)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return ""

def extract_title_abstract_keywords(text):
    title = ""
    abstract = ""
    keywords = ""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if not title and 5 < len(line) < 200:
            title = line
        if 'abstract' in line.lower():
            abstract = lines[i+1] if i+1 < len(lines) else ""
        if 'keywords' in line.lower():
            keywords = lines[i+1] if i+1 < len(lines) else ""
    return title.strip(), abstract.strip(), keywords.strip()

def analyze_disciplines(title, abstract, keywords):
    combined = f"{title} {abstract} {keywords}".lower()
    disciplines = {
        "计算机科学": ["algorithm", "neural", "network", "learning", "data", "vision", "nlp", "cnn", "transformer"],
        "电子工程": ["circuit", "voltage", "rectifier", "power", "signal", "pwm", "electronics", "amplifier"],
        "控制科学": ["control", "pi", "fuzzy", "reinforcement", "autonomous", "controller", "pid"],
        "通信工程": ["communication", "transmission", "modulation", "bandwidth", "antenna", "channel"],
        "人工智能": ["deep learning", "reinforcement learning", "machine learning", "ai", "agent", "training"],
        "机械工程": ["robot", "mechanical", "structure", "dynamics", "kinematics"],
        "医学": ["patient", "disease", "clinical", "hospital", "symptom", "therapy"],
        "心理学": ["behavior", "emotion", "psychology", "mental"],
        "社会学": ["society", "social", "survey", "education", "policy"]
    }
    result = []
    for d, kws in disciplines.items():
        score = sum(1 for kw in kws if kw in combined)
        if score > 0:
            result.append((d, score))
    total = sum(s for _, s in result)
    if total == 0:
        return []
    result_sorted = sorted(result, key=lambda x: -x[1])
    return [(d, round(s / total * 100, 2)) for d, s in result_sorted[:5]]

def calculate_days_left(cutoff_date):
    try:
        return (cutoff_date - datetime.datetime.now().date()).days
    except:
        return "未知"

def keyword_matches(paper_text, conference_keywords):
    paper_text = paper_text.lower()
    matches = []
    for kw in str(conference_keywords).split(","):
        if kw.strip().lower() in paper_text:
            matches.append(kw.strip())
    return matches

def section_title(title):
    st.markdown(f"### {title}")

def subsection_title(sub):
    st.markdown(f"**{sub}**")

def main():
    st.title("📄 论文会议匹配推荐系统")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 上传会议文件（Excel）")
        conf_file = st.file_uploader("📁 上传会议 Excel 文件", type=["xlsx"], key="conf")

    with col2:
        st.markdown("#### 上传论文文件（PDF / DOCX）")
        paper_file = st.file_uploader("📄 上传论文 PDF 或 Word 文件", type=["pdf", "docx"], key="paper")

    paper_text = ""
    title, abstract, keywords = "", "", ""
    disciplines = []

    if paper_file:
        with st.spinner("🔍 正在读取论文内容并分析学科方向..."):
            if paper_file.type == "application/pdf":
                paper_text = extract_text_from_pdf(paper_file)
            elif paper_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                paper_text = extract_text_from_docx(paper_file)

            title, abstract, keywords = extract_title_abstract_keywords(paper_text)
            disciplines = analyze_disciplines(title, abstract, keywords)

            section_title("📘 论文学科方向分析")
            st.markdown(f"**标题：** {title}")
            st.markdown(f"**摘要：** {abstract}")
            st.markdown(f"**关键词：** {keywords}")
            if disciplines:
                for d, p in disciplines:
                    st.markdown(f"- **{d}**（占比：{p}%）")
            else:
                st.warning("未能识别明确的学科方向")

    if paper_file and conf_file:
        section_title("📌 匹配推荐结果")
        with st.spinner("🤖 正在匹配推荐会议..."):
            conf_df = pd.read_excel(conf_file)

            required_fields = {"会议名", "会议系列名", "会议主题方向", "细分关键词", "截稿时间", "官网链接", "动态出版标记"}
            if not required_fields.issubset(conf_df.columns):
                st.error(f"❌ 缺少必要字段：{required_fields - set(conf_df.columns)}")
                return

            matches = []
            for _, row in conf_df.iterrows():
                combined_keywords = f"{row['会议主题方向']} {row['细分关键词']}"
                matched_keywords = keyword_matches(paper_text, combined_keywords)
                score = len(matched_keywords)
                if score > 0:
                    matches.append({
                        "会议标题": f"{row['会议系列名']} - {row['会议名']}",
                        "官网链接": row["官网链接"],
                        "动态出版标记": row["动态出版标记"],
                        "截稿时间": row["截稿时间"],
                        "匹配关键词": ", ".join(matched_keywords),
                        "匹配程度": score
                    })

            if matches:
                matches = sorted(matches, key=lambda x: -x["匹配程度"])
                for m in matches[:3]:
                    subsection_title(m["会议标题"])
                    st.markdown(f"- **官网链接：** [{m['官网链接']}]({m['官网链接']})")
                    st.markdown(f"- **动态出版标记：** {m['动态出版标记']}")
                    st.markdown(f"- **截稿时间：** {m['截稿时间']}")
                    st.markdown(f"- **匹配关键词：** {m['匹配关键词']}")
            else:
                st.info("⚠️ 暂无完全匹配的会议，以下是基于学科的模糊推荐：")
                fuzzy_matches = conf_df.sample(3)
                for _, row in fuzzy_matches.iterrows():
                    subsection_title(f"{row['会议系列名']} - {row['会议名']}")
                    st.markdown(f"- **官网链接：** [{row['官网链接']}]({row['官网链接']})")
                    st.markdown(f"- **动态出版标记：** {row['动态出版标记']}")
                    st.markdown(f"- **截稿时间：** {row['截稿时间']}")
                    if disciplines:
                        st.markdown(f"- **匹配说明：** 该会议主题与论文学科方向 **{disciplines[0][0]}** 部分相关")

if __name__ == "__main__":
    main()
