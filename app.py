import streamlit as st
import pandas as pd
import fitz  # 用于解析PDF文件
import docx  # 用于解析Word文件
from io import BytesIO
import os
import time
import datetime

# 文件上传区域，增高以便拖拽文件
def file_uploader(label, file_types=None, height=300):
    uploaded_file = st.file_uploader(label, type=file_types, help="Drag and drop your file here.", label_visibility="collapsed")
    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name}")
    return uploaded_file

# 提取PDF文件的内容
def extract_pdf_content(file):
    doc = fitz.open(file)
    content = ""
    for page in doc:
        content += page.get_text("text")
    return content

# 提取Word文件的内容
def extract_word_content(file):
    doc = docx.Document(file)
    content = ""
    for para in doc.paragraphs:
        content += para.text + "\n"
    return content

# 提取论文标题、摘要和关键词
def extract_paper_content(file):
    if file is None:
        return "", "", []

    if file.type == "application/pdf":
        content = extract_pdf_content(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        content = extract_word_content(file)
    else:
        return "", "", []

    title = content.split("\n")[0]  # 假设标题是文档的第一行
    abstract = ""  # 摘要区域
    keywords = []  # 关键词区域

    # 简单的假设：摘要和关键词在文档中是标题后出现的
    lines = content.split("\n")
    is_abstract = False
    for line in lines:
        if line.lower().startswith("abstract"):
            is_abstract = True
            continue
        if is_abstract and line.strip() == "":
            break
        if is_abstract:
            abstract += line + " "
        if "keywords" in line.lower():
            keywords.append(line.strip())

    return title, abstract, keywords

# 提取学科方向分析（假设简单的关键词匹配）
def analyze_paper_subject(title, abstract, keywords):
    # 假设的学科方向分析函数
    academic_field = "未能识别明确的学科方向"
    explanation = "请检查论文中的关键词和摘要内容"

    if 'machine learning' in title.lower() or 'deep learning' in abstract.lower():
        academic_field = "计算机科学"
        explanation = "根据论文标题和摘要分析，此论文属于计算机科学领域，涉及机器学习和深度学习方向"
    elif 'biotechnology' in title.lower() or 'genetics' in abstract.lower():
        academic_field = "生物技术"
        explanation = "根据论文标题和摘要分析，此论文属于生物技术领域，涉及基因技术方向"
    else:
        academic_field = "其他"
        explanation = "未能明确识别学科领域，可能属于其他学科方向"

    return academic_field, explanation

# 会议文件匹配
def perform_matching(paper_keywords, conference_data):
    # 示例匹配
    matches = []
    for index, row in conference_data.iterrows():
        if any(keyword.lower() in row['会议名称'].lower() for keyword in paper_keywords):
            matches.append(row['会议名称'])

    if not matches:
        matches.append("未找到完全匹配的会议，基于学科方向推荐：计算机科学领域")

    return matches

# 展示进度条
def show_progress_bar():
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.05)
        progress.progress(i + 1)

# 主函数
def main():
    st.title("论文会议匹配工具")

    # 上传会议文件
    conference_file = file_uploader("上传会议文件", ["xlsx"], 300)
    if conference_file:
        conference_data = pd.read_excel(conference_file)
        st.write(conference_data.head())  # 显示会议数据

    # 上传论文文件
    paper_file = file_uploader("上传论文文件", ["pdf", "docx"], 300)
    if paper_file:
        title, abstract, keywords = extract_paper_content(paper_file)

        # 显示论文标题、摘要、关键词
        st.subheader("论文标题")
        st.write(title)
        st.subheader("论文摘要")
        st.write(abstract)
        st.subheader("论文关键词")
        st.write(", ".join(keywords))

        # 论文学科分析
        academic_field, explanation = analyze_paper_subject(title, abstract, keywords)
        st.subheader("学科方向分析")
        st.write(f"学科方向: {academic_field}")
        st.write(f"分析说明: {explanation}")

        # 进行会议匹配
        if conference_file:
            st.subheader("匹配结果")
            matches = perform_matching(keywords, conference_data)
            for match in matches:
                st.write(match)

        show_progress_bar()  # 展示进度条

if __name__ == "__main__":
    main()
