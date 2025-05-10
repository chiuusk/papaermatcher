import streamlit as st
import pandas as pd
import docx
import fitz  # PyMuPDF
import os

# 解析PDF文件内容
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(file)
        text = ''
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF解析失败: {str(e)}")
        return None

# 解析Word文件内容
def extract_text_from_word(file):
    try:
        doc = docx.Document(file)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        st.error(f"Word解析失败: {str(e)}")
        return None

# 提取论文内容
def extract_paper_content(paper_file):
    if paper_file is not None:
        file_extension = paper_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return extract_text_from_pdf(paper_file)
        elif file_extension == 'docx':
            return extract_text_from_word(paper_file)
        else:
            st.error("不支持的论文文件格式，仅支持PDF和Word文件")
            return None
    else:
        return None

# 会议文件解析
def extract_conference_content(conference_file):
    if conference_file is not None:
        try:
            df = pd.read_excel(conference_file)
            return df
        except Exception as e:
            st.error(f"会议文件解析失败: {str(e)}")
            return None
    else:
        return None

# 分析论文的学科方向
def analyze_paper_subject(title, abstract, keywords):
    # 简单的示例：通过标题、摘要和关键词分析学科
    subjects = {
        '计算机科学': ['machine learning', 'artificial intelligence', 'data science'],
        '生物学': ['biological', 'genetic', 'biochemistry'],
        '物理学': ['quantum', 'physics', 'thermodynamics'],
    }
    
    for subject, key_terms in subjects.items():
        if any(keyword.lower() in (title + abstract + keywords).lower() for keyword in key_terms):
            return subject
    return "未能识别明确的学科方向"

# 文章匹配会议
def perform_matching(paper_content, conference_data):
    matches = []
    for index, row in conference_data.iterrows():
        if any(keyword.lower() in paper_content.lower() for keyword in row['会议关键词'].split(',')):
            matches.append(row['会议名称'])
    return matches

# 设置Streamlit界面
def main():
    st.title("论文与会议匹配系统")

    # 设置上传区域
    col1, col2 = st.columns(2)
    with col1:
        conference_file = st.file_uploader("上传会议文件（Excel格式）", type=["xlsx"])
    with col2:
        paper_file = st.file_uploader("上传论文文件（PDF/Word格式）", type=["pdf", "docx"])

    if paper_file is not None:
        paper_content = extract_paper_content(paper_file)
        if paper_content:
            st.subheader("论文学科方向分析")
            title = "示例标题"
            abstract = "示例摘要内容，可能涉及计算机科学、人工智能等领域"
            keywords = "计算机科学, 人工智能, 数据科学"
            subject = analyze_paper_subject(title, abstract, keywords)
            st.write(f"匹配学科方向: {subject}")

    if conference_file is not None:
        conference_data = extract_conference_content(conference_file)
        if conference_data is not None and paper_file is not None:
            matches = perform_matching(paper_content, conference_data)
            st.subheader("推荐匹配会议")
            if matches:
                for match in matches:
                    st.write(match)
            else:
                st.write("没有找到完全匹配的会议，但以下会议可能相关：")
                # 你可以添加模糊匹配逻辑

if __name__ == "__main__":
    main()
