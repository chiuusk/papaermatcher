import streamlit as st
import pandas as pd
import os
import fitz  # PyMuPDF，用于PDF解析
import docx  # 用于解析Word文档

# 论文内容提取功能
def extract_text_from_pdf(file):
    doc = fitz.open(file)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

def extract_paper_content(paper_file):
    if paper_file is not None:
        file_extension = paper_file.name.split('.')[-1].lower()
        if file_extension == "pdf":
            return extract_text_from_pdf(paper_file)
        elif file_extension == "docx":
            return extract_text_from_docx(paper_file)
        else:
            st.error("Unsupported file format. Please upload a PDF or Word document.")
            return None
    return None

# 学科分析函数（简单的关键词分析）
def analyze_paper_subject(title, abstract, keywords):
    # 示例关键词，您可以根据需要扩展
    science_keywords = {
        "computer science": ["algorithm", "AI", "machine learning", "data", "computer", "programming"],
        "biology": ["DNA", "gene", "biotechnology", "protein", "cell", "genetics"],
        "chemistry": ["molecule", "reaction", "atom", "chemical", "compound", "organic"],
        "physics": ["quantum", "thermodynamics", "mechanics", "particle", "atom", "energy"]
    }
    
    paper_text = f"{title} {abstract} {keywords}"
    analysis_results = {}
    
    for field, terms in science_keywords.items():
        score = sum(paper_text.lower().count(term) for term in terms)
        if score > 0:
            analysis_results[field] = score
    
    if analysis_results:
        sorted_results = sorted(analysis_results.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[0]  # 返回最匹配的学科方向
    else:
        return ("No clear subject direction identified", "N/A")

# 文件上传和分析
def main():
    st.title("论文与会议匹配工具")

    # 上传会议文件区域
    conference_file = st.file_uploader("上传会议文件 (Excel)", type=["xlsx"], label_visibility="collapsed")
    conference_data = None

    if conference_file:
        conference_data = pd.read_excel(conference_file)
        st.write("会议文件上传成功")

    # 上传论文文件区域
    paper_file = st.file_uploader("上传论文文件 (PDF 或 Word)", type=["pdf", "docx"], label_visibility="collapsed")
    if paper_file:
        paper_content = extract_paper_content(paper_file)
        if paper_content:
            # 提取论文的标题、摘要和关键词（假设这些在文章的开头部分）
            title = paper_content.split('\n')[0]  # 假设标题是文章的第一行
            abstract = paper_content.split('\n')[1]  # 假设摘要是文章的第二行
            keywords = paper_content.split('\n')[2]  # 假设关键词是文章的第三行

            st.write("论文标题:", title)
            st.write("论文摘要:", abstract)
            st.write("论文关键词:", keywords)
            
            # 学科方向分析
            heading, result = analyze_paper_subject(title, abstract, keywords)
            st.subheader(f"学科分析结果: {heading}")
            st.write(f"匹配学科: {result}")

            # 根据分析结果生成推荐会议
            if conference_data is not None:
                matches = []
                for index, row in conference_data.iterrows():
                    conference_name = row['会议名称']
                    conference_subject = row.get('学科方向', '')
                    if heading.lower() in conference_subject.lower():
                        matches.append(conference_name)

                if matches:
                    st.subheader("推荐匹配会议")
                    for match in matches:
                        st.write(f"- {match}")
                else:
                    st.write("未找到完全匹配的会议，基于学科方向进行推荐。")

                    # 模糊匹配推荐（以学科方向为基础）
                    st.write("推荐会议（模糊匹配）：")
                    for index, row in conference_data.iterrows():
                        conference_name = row['会议名称']
                        conference_subject = row.get('学科方向', '')
                        if heading.lower() in conference_subject.lower():
                            st.write(f"- {conference_name}")

# 文件上传区域增加高度
st.markdown("""
    <style>
    .streamlit-expanderHeader {
        font-size: 20px;
    }
    div.stFileUploader {
        height: 100px;
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
