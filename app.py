import streamlit as st
import pandas as pd
import datetime
import io
import time
from googletrans import Translator  # 引入翻译库
import fitz  # 用于解析pdf文件
import docx  # 用于解析docx文件
import re

# 计算剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 文件上传处理函数
def upload_conference_file():
    uploaded_file = st.file_uploader("上传会议文件", type=["xlsx"])
    return uploaded_file

def upload_paper_file():
    uploaded_file = st.file_uploader("上传论文文件", type=["pdf", "docx"])
    return uploaded_file

# 论文内容提取
def extract_text_from_pdf(pdf_file):
    # 提取PDF文本
    doc = fitz.open(io.BytesIO(pdf_file.read()))
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def extract_text_from_docx(docx_file):
    # 提取Word文本
    doc = docx.Document(io.BytesIO(docx_file.read()))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_paper_content(paper_file):
    if paper_file is not None:
        if paper_file.type == "application/pdf":
            return extract_text_from_pdf(paper_file)
        elif paper_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_docx(paper_file)
    return ""

# 提取论文标题和关键词
def extract_title_and_keywords(text):
    # 假设标题是文档中的第一行，关键词根据正则匹配
    title = text.split("\n")[0]  # 假设标题在文档第一行
    keyword_pattern = r"(?:Keywords|关键词):\s*(.*)"  # 匹配关键词
    match = re.search(keyword_pattern, text, re.IGNORECASE)
    keywords = match.group(1) if match else "无关键词"
    return title, keywords

# 翻译函数
def translate_text(text):
    translator = Translator()
    translation = translator.translate(text, src='zh-cn', dest='en')
    return translation.text

# 论文文件学科分析
def analyze_paper_subject(paper_file):
    # 提取论文文本
    text = extract_paper_content(paper_file)
    
    # 提取标题和关键词
    title, keywords = extract_title_and_keywords(text)
    
    # 翻译标题和关键词
    title_en = translate_text(title)
    keywords_en = translate_text(keywords)
    
    # 模拟学科分析, 实际可使用NLP模型或规则
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }
    
    st.write("论文学科方向分析：")
    st.write(f"该论文涉及的学科及其比例：")
    for subject, percent in subjects.items():
        st.write(f"{subject}: {percent}%")
    
    st.write("论文标题及关键词（中英文对照）：")
    st.write(f"标题（中文）：{title}")
    st.write(f"Title (English): {title_en}")
    st.write(f"关键词（中文）：{keywords}")
    st.write(f"Keywords (English): {keywords_en}")
    
    return subjects

# 匹配函数
def perform_matching(conference_file, paper_file):
    if conference_file is not None:
        try:
            # 读取上传的会议文件
            conference_data = pd.read_excel(conference_file)  # 直接从上传的文件中读取
            st.write("会议文件加载成功")
            
            # 获取论文分析结果
            paper_subjects = analyze_paper_subject(paper_file)
            
            matching_conferences = []
            for index, row in conference_data.iterrows():
                # 检查会议是否符合条件，假设示例的匹配条件
                if 'Symposium' not in row['会议名']:
                    # 获取匹配的会议方向
                    conference_subjects = row['会议主题方向'].split(',')  # 假设会议的主题方向列是以逗号分隔
                    matching_score = 0
                    for subject in paper_subjects:
                        if subject in conference_subjects:
                            matching_score += paper_subjects[subject]
                    
                    if matching_score > 0:
                        matching_conferences.append({
                            "会议系列名与会议名": f"{row['会议系列名']} - {row['会议名']}",
                            "官网链接": row['官网链接'],
                            "动态出版标记": row['动态出版标记'],
                            "截稿时间": row['截稿时间'],
                            "剩余天数": calculate_days_left(row['截稿时间']),
                            "论文研究方向匹配": f"与{row['会议主题方向']}匹配"
                        })
            
            # 展示匹配的会议
            if matching_conferences:
                for conference in matching_conferences:
                    st.write(f"**会议推荐：{conference['会议系列名与会议名']}**")
                    st.write(f"官网链接: {conference['官网链接']}")
                    st.write(f"动态出版标记: {conference['动态出版标记']}")
                    st.write(f"截稿时间: {conference['截稿时间']} (距离截稿还有 {conference['剩余天数']} 天)")
                    st.write(f"匹配分析: {conference['论文研究方向匹配']}")
            else:
                st.write("没有找到完全匹配的会议，根据您的论文方向，推荐以下学科：")
                st.write("推荐学科: 电力系统工程, 控制理论, 计算机科学")
                st.write("可以参考这些方向的其他会议。")
        except Exception as e:
            st.error(f"加载会议文件时出错: {e}")
    else:
        st.error("请上传有效的会议文件")

# 主函数
def main():
    st.title("论文与会议匹配系统")
    
    # 上传会议文件区
    conference_file = upload_conference_file()
    
    # 上传论文文件区
    paper_file = upload_paper_file()
    
    # 如果论文文件上传了，进行进一步的分析与匹配
    if paper_file:
        st.write("正在进行论文分析...")
        time.sleep(1)  # 模拟分析时间
        perform_matching(conference_file, paper_file)  # 传递上传的会议文件进行匹配
    else:
        st.write("请先上传论文文件进行匹配。")

if __name__ == "__main__":
    main()
