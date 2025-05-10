import streamlit as st
import pandas as pd
import os
from io import BytesIO
import fitz  # PyMuPDF用于解析PDF
import docx  # 用于解析Word文档

# 解析PDF文件
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 解析Word文件
def extract_text_from_word(doc_file):
    doc = docx.Document(doc_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# 论文内容提取：标题、摘要和关键字
def extract_paper_content(file):
    if file.type == "application/pdf":
        text = extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_word(file)
    else:
        return None, None, None

    # 假设从文本中提取标题、摘要和关键字
    # 这里只是一个简单的实现，实际情况下可能需要更复杂的处理
    title = "提取的标题"  # 示例
    abstract = "提取的摘要"  # 示例
    keywords = ["关键词1", "关键词2", "关键词3"]  # 示例

    return title, abstract, keywords

# 假设一个学科方向分析的简单函数
def analyze_paper_subject(title, abstract, keywords):
    # 基于标题、摘要和关键词分析学科方向
    subject = "未能识别明确的学科方向"
    if "计算机" in title or "计算机" in abstract:
        subject = "计算机科学"
    elif "生物" in title or "生物" in abstract:
        subject = "生物科学"
    return subject

# 显示论文文件上传区
def show_upload_section():
    st.sidebar.header("上传论文文件")
    paper_file = st.sidebar.file_uploader("选择PDF或Word文件", type=["pdf", "docx"])
    return paper_file

# 显示会议文件上传区
def show_conference_upload_section():
    st.sidebar.header("上传会议文件")
    conference_file = st.sidebar.file_uploader("选择会议文件 (Excel格式)", type=["xlsx"])
    return conference_file

# 进行论文与会议的匹配
def perform_matching(paper_file, conference_file):
    title, abstract, keywords = extract_paper_content(paper_file)
    if title and abstract and keywords:
        subject = analyze_paper_subject(title, abstract, keywords)
        st.write(f"论文学科方向分析: {subject}")
    else:
        st.write("无法提取论文内容")

    if conference_file:
        conference_data = pd.read_excel(conference_file)
        st.write("会议文件数据:")
        st.write(conference_data)

# Streamlit应用主函数
def main():
    st.title("论文与会议匹配系统")

    # 上传文件
    paper_file = show_upload_section()
    conference_file = show_conference_upload_section()

    if paper_file and conference_file:
        perform_matching(paper_file, conference_file)

if __name__ == "__main__":
    main()
