import streamlit as st
import pandas as pd
import datetime
import time
import re
import fitz  # pymupdf，用于解析 PDF
import docx  # 用于解析 Word 文件

# ------------------- 基础函数 -------------------

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

# 提取论文题目
def extract_title(text):
    lines = text.strip().split('\n')
    for line in lines:
        if len(line.strip()) > 5 and len(line.strip()) < 200:
            return line.strip()
    return "未识别到标题"

# 提取关键词
def extract_keywords(text):
    patterns = [
        r"(?i)(关键词|Key words|Keywords)[:：]?\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(2).strip()
    return "未识别到关键词"

# 简单中英文判断（粗略）
def is_chinese(text):
    return any('\u4e00' <= ch <= '\u9fff' for ch in text)

# 模拟学科分析
def analyze_paper_subject(text):
    # 这里可替换为更复杂的 NLP 模型分析
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }
    return subjects

# ------------------- 文件上传 -------------------

def upload_conference_file():
    return st.file_uploader("上传会议文件", type=["xlsx"], key="conference_file")

def upload_paper_file():
    return st.file_uploader("上传论文文件", type=["pdf", "docx"], key="paper_file")

# ------------------- 主匹配逻辑 -------------------

def perform_matching(conference_file, paper_subjects):
    if conference_file is None:
        st.warning("未上传会议文件，无法进行会议匹配")
        return

    try:
        df = pd.read_excel(conference_file)
        st.success("会议文件加载成功")

        matching_conferences = []
        for _, row in df.iterrows():
            conference_subjects = row['会议主题方向'].split(',') if pd.notna(row['会议主题方向']) else []
            matching_score = sum(paper_subjects.get(subject.strip(), 0) for subject in conference_subjects)

            if matching_score > 0:
                matching_conferences.append({
                    "会议系列名与会议名": f"{row['会议系列名']} - {row['会议名']}",
                    "官网链接": row['官网链接'],
                    "动态出版标记": row['动态出版标记'],
                    "截稿时间": row['截稿时间'],
                    "剩余天数": calculate_days_left(row['截稿时间']),
                    "匹配分析": f"论文方向与 {row['会议主题方向']} 有关"
                })

        if matching_conferences:
            st.subheader("推荐匹配的会议：")
            for conf in matching_conferences:
                st.markdown(f"**会议推荐：{conf['会议系列名与会议名']}**")
                st.markdown(f"- 官网链接: [{conf['官网链接']}]({conf['官网链接']})")
                st.markdown(f"- 动态出版标记: {conf['动态出版标记']}")
                st.markdown(f"- 截稿时间: {conf['截稿时间']} (剩余 {conf['剩余天数']} 天)")
                st.markdown(f"- 匹配分析: {conf['匹配分析']}")
        else:
            st.info("未匹配到合适的会议，请根据学科方向查找其他会议")

    except Exception as e:
        st.error(f"会议文件读取失败: {e}")

# ------------------- 主函数 -------------------

def main():
    st.set_page_config(layout="wide")
    st.title("📄 论文与会议匹配系统")

    col1, col2 = st.columns(2)

    # 左侧上传会议文件
    with col1:
        st.header("📁 上传会议文件")
        conference_file = upload_conference_file()

    # 右侧上传论文文件并分析
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

            title = extract_title(text)
            keywords = extract_keywords(text)

            st.subheader("🎯 提取结果：")

            st.markdown(f"**题目（中文）：** {title}")
            st.markdown(f"**Title (English):** {title}")
            st.markdown(f"**关键词（中文）：** {keywords}")
            st.markdown(f"**Keywords (English):** {keywords}")

            subjects = analyze_paper_subject(text)

            st.subheader("📚 论文学科方向分析")
            for subject, weight in subjects.items():
                st.write(f"{subject}: {weight}%")

            perform_matching(conference_file, subjects)
        else:
            st.info("请上传论文文件进行分析")

if __name__ == "__main__":
    main()
