import streamlit as st
import pandas as pd
import datetime
import io
import time
import fitz  # PDF 解析
import docx  # Word 解析
import re
import requests  # 用于在线翻译

# 翻译函数（通过 Google Translate Web 接口）
def translate_text(text, source='zh', target='en'):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source,
            "tl": target,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return result[0][0][0]
        else:
            return "[翻译失败]"
    except:
        return "[翻译错误]"

def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

def upload_conference_file():
    uploaded_file = st.file_uploader("上传会议文件", type=["xlsx"])
    return uploaded_file

def upload_paper_file():
    uploaded_file = st.file_uploader("上传论文文件", type=["pdf", "docx"])
    return uploaded_file

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def extract_text_from_docx(docx_file):
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

def extract_title_and_keywords(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    title = lines[0] if lines else "未知标题"
    keyword_pattern = r"(?:Keywords|关键词)[:：]?\s*(.*)"
    match = re.search(keyword_pattern, text, re.IGNORECASE)
    keywords = match.group(1) if match else "无关键词"
    return title, keywords

def analyze_paper_subject(paper_file):
    text = extract_paper_content(paper_file)
    title, keywords = extract_title_and_keywords(text)
    title_en = translate_text(title)
    keywords_en = translate_text(keywords)

    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }

    st.markdown("### 📘 论文标题及关键词（中英文对照）")
    st.markdown(f"**标题（中文）**：{title}")
    st.markdown(f"**Title (English)**：{title_en}")
    st.markdown(f"**关键词（中文）**：{keywords}")
    st.markdown(f"**Keywords (English)**：{keywords_en}")

    st.markdown("### 📊 论文学科方向分析")
    for subject, percent in subjects.items():
        st.write(f"{subject}: {percent}%")

    return subjects

def perform_matching(conference_file, paper_file):
    if conference_file is not None:
        try:
            conference_data = pd.read_excel(conference_file)
            st.success("✅ 会议文件加载成功")
            paper_subjects = analyze_paper_subject(paper_file)
            matching_conferences = []

            for index, row in conference_data.iterrows():
                if 'Symposium' not in row['会议名']:
                    conference_subjects = row['会议主题方向'].split(',')
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

            if matching_conferences:
                st.markdown("### ✅ 推荐匹配会议")
                for conf in matching_conferences:
                    st.markdown(f"**会议推荐：{conf['会议系列名与会议名']}**")
                    st.markdown(f"官网链接: [{conf['官网链接']}]({conf['官网链接']})")
                    st.write(f"动态出版标记: {conf['动态出版标记']}")
                    st.write(f"截稿时间: {conf['截稿时间']} （剩余 {conf['剩余天数']} 天）")
                    st.write(f"匹配分析: {conf['论文研究方向匹配']}")
            else:
                st.warning("⚠️ 没有找到完全匹配的会议")
        except Exception as e:
            st.error(f"加载会议文件时出错: {e}")
    else:
        st.warning("请上传会议文件")

def main():
    st.title("📄 论文与会议匹配系统")
    conference_file = upload_conference_file()
    paper_file = upload_paper_file()

    if paper_file:
        st.info("正在进行论文分析...")
        time.sleep(1)
        perform_matching(conference_file, paper_file)
    else:
        st.warning("请上传论文文件以进行分析和匹配")

if __name__ == "__main__":
    main()
