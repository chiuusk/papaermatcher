import streamlit as st
import pandas as pd
import datetime
import io
import time
import re
from docx import Document
import fitz  # PyMuPDF，用于PDF解析
import requests

# 使用第三方API翻译（无需安装库）
def translate_text(text, target_lang="zh"):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params)
        result = response.json()
        return "".join([item[0] for item in result[0]])
    except:
        return "(翻译失败)"

# 提取 PDF 文本
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF解析失败: {e}")
        return ""

# 提取 Word 文本
def extract_text_from_word(file):
    try:
        document = Document(file)
        text = "\n".join([para.text for para in document.paragraphs])
        return text
    except Exception as e:
        st.error(f"Word解析失败: {e}")
        return ""

# 提取论文题目
def extract_title(text):
    lines = text.split('\n')
    for line in lines:
        if 5 < len(line) < 200 and line.strip().istitle():
            return line.strip()
    return lines[0].strip() if lines else "无法识别题目"

# 提取关键词
def extract_keywords(text):
    patterns = [r"(?i)(Keywords|Index Terms)[:：]?\s*(.*)"]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(2)
    return "无法识别关键词"

# 模拟学科分析（你可以换成模型）
def analyze_paper_subject(text):
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }
    return subjects

# 计算剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 主函数
def main():
    st.set_page_config(layout="wide")
    st.title("论文与会议匹配系统")

    col1, col2 = st.columns(2)

    with col1:
        st.header("上传会议文件")
        conference_file = st.file_uploader("上传会议 Excel 文件", type=["xlsx"], key="conf")

    with col2:
        st.header("上传论文文件")
        paper_file = st.file_uploader("上传论文文件 (PDF 或 Word)", type=["pdf", "docx"], key="paper")

    # 如果上传了论文文件，立即分析
    if paper_file:
        st.markdown("## 📄 论文内容解析结果")
        file_text = ""
        if paper_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(paper_file)
        elif paper_file.name.endswith(".docx"):
            file_text = extract_text_from_word(paper_file)

        if not file_text.strip():
            st.error("未能成功提取论文内容")
            return

        # 提取题目与关键词
        title = extract_title(file_text)
        keywords = extract_keywords(file_text)

        # 翻译结果
        title_zh = translate_text(title)
        keywords_zh = translate_text(keywords)

        st.subheader("论文题目")
        st.write(f"**中文：** {title_zh}")
        st.write(f"**英文：** {title}")

        st.subheader("关键词")
        st.write(f"**中文：** {keywords_zh}")
        st.write(f"**英文：** {keywords}")

        # 学科分析
        st.subheader("学科方向分析")
        subjects = analyze_paper_subject(file_text)
        for subject, percent in subjects.items():
            st.write(f"- {subject}: {percent}%")

        # 如果会议文件也上传了，进行匹配
        if conference_file:
            try:
                conf_data = pd.read_excel(conference_file)
                st.markdown("## 🎯 匹配推荐的会议")
                matches = []
                for _, row in conf_data.iterrows():
                    conf_subjects = row.get('会议主题方向', '')
                    if not conf_subjects:
                        continue
                    conf_list = [x.strip() for x in conf_subjects.split(',')]
                    score = sum([subjects.get(s, 0) for s in conf_list])
                    if score > 0:
                        matches.append((score, row))

                matches.sort(reverse=True, key=lambda x: x[0])
                if matches:
                    for score, row in matches[:5]:
                        st.write(f"### ✅ 推荐会议: {row['会议系列名']} - {row['会议名']}")
                        st.write(f"- 会议方向: {row['会议主题方向']}")
                        st.write(f"- 匹配得分: {score}")
                        st.write(f"- 官网链接: [{row['官网链接']}]({row['官网链接']})")
                        if '截稿时间' in row and not pd.isna(row['截稿时间']):
                            cutoff = row['截稿时间']
                            if isinstance(cutoff, pd.Timestamp):
                                days_left = calculate_days_left(cutoff.date())
                                st.write(f"- 截稿时间: {cutoff.date()}（还有 {days_left} 天）")
                        st.markdown("---")
                else:
                    st.info("未匹配到适合的会议，请根据学科方向自行查找。")
            except Exception as e:
                st.error(f"会议文件解析失败：{e}")

if __name__ == "__main__":
    main()
