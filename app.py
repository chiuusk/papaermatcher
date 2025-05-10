import streamlit as st
import pandas as pd
import datetime
import time
import re
import fitz  # PyMuPDF
import docx
from deep_translator import GoogleTranslator

# ------------------- 工具函数 -------------------

def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_title(text):
    lines = text.strip().split('\n')
    for line in lines:
        if 5 < len(line.strip()) < 200:
            return line.strip()
    return "未识别到标题"

def extract_keywords(text):
    patterns = [
        r"(关键词|Key words|Keywords)[:：]?\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return "未识别到关键词"

def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return "(翻译失败)"

def analyze_paper_subject(text):
    return {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }

# ------------------- 文件上传 -------------------

def upload_conference_file():
    return st.file_uploader("上传会议文件", type=["xlsx"], key="conference_file")

def upload_paper_file():
    return st.file_uploader("上传论文文件", type=["pdf", "docx"], key="paper_file")

# ------------------- 匹配逻辑 -------------------

def perform_matching(conference_file, paper_subjects):
    if conference_file is None:
        st.warning("未上传会议文件，无法进行会议匹配")
        return

    try:
        df = pd.read_excel(conference_file)
        st.success("会议文件加载成功")

        matching_confs = []
        for _, row in df.iterrows():
            conf_subjects = row['会议主题方向'].split(',') if pd.notna(row['会议主题方向']) else []
            match_score = sum(paper_subjects.get(s.strip(), 0) for s in conf_subjects)
            if match_score > 0:
                matching_confs.append({
                    "会议": f"{row['会议系列名']} - {row['会议名']}",
                    "链接": row['官网链接'],
                    "出版标记": row['动态出版标记'],
                    "截稿": row['截稿时间'],
                    "剩余天数": calculate_days_left(row['截稿时间']),
                    "匹配分析": f"论文方向与 {row['会议主题方向']} 有关"
                })

        if matching_confs:
            st.subheader("🎯 推荐会议：")
            for c in matching_confs:
                st.markdown(f"**{c['会议']}**")
                st.markdown(f"- 官网链接: [{c['链接']}]({c['链接']})")
                st.markdown(f"- 动态出版标记: {c['出版标记']}")
                st.markdown(f"- 截稿时间: {c['截稿']} (剩余 {c['剩余天数']} 天)")
                st.markdown(f"- 匹配分析: {c['匹配分析']}")
        else:
            st.info("⚠️ 未匹配到合适的会议，请查看学科方向建议")
    except Exception as e:
        st.error(f"会议文件读取失败: {e}")

# ------------------- 主函数 -------------------

def main():
    st.set_page_config(layout="wide")
    st.title("📄 论文与会议匹配系统")

    col1, col2 = st.columns(2)

    with col1:
        st.header("📁 上传会议文件")
        conference_file = upload_conference_file()

    with col2:
        st.header("📄 上传论文文件")
        paper_file = upload_paper_file()

        if paper_file:
            st.success("论文文件上传成功，正在解析...")

            if paper_file.name.endswith(".pdf"):
                text = extract_text_from_pdf(paper_file)
            elif paper_file.name.endswith(".docx"):
                text = extract_text_from_docx(paper_file)
            else:
                st.error("不支持的文件格式")
                return

            title_cn = extract_title(text)
            keywords_cn = extract_keywords(text)
            title_en = translate_to_english(title_cn)
            keywords_en = translate_to_english(keywords_cn)

            st.subheader("📌 论文信息提取与翻译")
            st.markdown(f"**题目（中文）：** {title_cn}")
            st.markdown(f"**Title (English):** {title_en}")
            st.markdown(f"**关键词（中文）：** {keywords_cn}")
            st.markdown(f"**Keywords (English):** {keywords_en}")

            subjects = analyze_paper_subject(text)
            st.subheader("📚 学科方向分析")
            for subject, weight in subjects.items():
                st.write(f"{subject}: {weight}%")

            perform_matching(conference_file, subjects)
        else:
            st.info("请上传论文文件以进行提取分析")

if __name__ == "__main__":
    main()
