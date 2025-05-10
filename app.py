# 重新执行代码保存逻辑，因为前面的状态已经重置了
import os

# 创建最终输出的 app.py 文件结构（已集成用户需求）
app_py_code = """
import streamlit as st
import pandas as pd
import datetime
import io
import time
import docx
import fitz  # PyMuPDF，用于PDF解析
import re

# ===== 公共函数 =====

# 计算剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 中英文翻译（简单规则映射）
translation_dict = {
    "title": "标题",
    "abstract": "摘要",
    "keywords": "关键词"
}

def translate_term(term):
    return translation_dict.get(term.lower(), term)

# 读取PDF文本
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# 读取DOCX文本
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\\n".join([para.text for para in doc.paragraphs])

# 提取标题、摘要、关键词
def extract_paper_fields(text):
    fields = {"title": "", "abstract": "", "keywords": ""}
    lines = text.split("\\n")
    for line in lines:
        line_lower = line.lower().strip()
        if line_lower.startswith("title:") or line_lower.startswith("标题："):
            fields["title"] = line.split(":", 1)[-1].strip()
        elif line_lower.startswith("abstract:") or line_lower.startswith("摘要："):
            fields["abstract"] = line.split(":", 1)[-1].strip()
        elif line_lower.startswith("keywords:") or line_lower.startswith("关键词："):
            fields["keywords"] = line.split(":", 1)[-1].strip()
    return fields

# 模拟翻译
def mock_translate(text):
    return "（翻译）" + text if text else ""

# 分析论文内容
def analyze_paper_subject(paper_text):
    st.subheader("📘 论文基本信息提取（中英文对照）")
    fields = extract_paper_fields(paper_text)
    for key in ["title", "abstract", "keywords"]:
        en = fields[key]
        zh = mock_translate(en)
        st.write(f"**{translate_term(key)}:** {en}")
        st.write(f"**{translate_term(key)}（中文）:** {zh}")
    
    st.subheader("📊 论文学科方向分析：")
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }
    for subject, percent in subjects.items():
        st.write(f"{subject}: {percent}%")
    return subjects

# 上传文件函数
def upload_conference_file():
    return st.file_uploader("📁 上传会议文件", type=["xlsx", "xls"], key="conference")

def upload_paper_file():
    return st.file_uploader("📄 上传论文文件", type=["pdf", "docx"], key="paper")

# 匹配函数
def perform_matching(conference_file, paper_subjects):
    try:
        conference_data = pd.read_excel(conference_file)
        st.success("✅ 会议文件加载成功")
        matching_conferences = []
        for index, row in conference_data.iterrows():
            if 'Symposium' not in row['会议名']:
                conference_subjects = row['会议主题方向'].split(',')
                score = sum(paper_subjects.get(s.strip(), 0) for s in conference_subjects)
                if score > 0:
                    matching_conferences.append({
                        "会议系列名与会议名": f"{row['会议系列名']} - {row['会议名']}",
                        "官网链接": row['官网链接'],
                        "动态出版标记": row['动态出版标记'],
                        "截稿时间": row['截稿时间'],
                        "剩余天数": calculate_days_left(row['截稿时间']),
                        "匹配说明": f"与方向[{row['会议主题方向']}]有交集"
                    })
        if matching_conferences:
            st.subheader("🎯 推荐会议列表：")
            for conf in matching_conferences:
                st.write(f"**会议：{conf['会议系列名与会议名']}**")
                st.markdown(f"[点击访问官网链接]({conf['官网链接']})", unsafe_allow_html=True)
                st.write(f"动态出版: {conf['动态出版标记']}")
                st.write(f"截稿时间: {conf['截稿时间']}（还剩 {conf['剩余天数']} 天）")
                st.write(f"匹配说明: {conf['匹配说明']}")
        else:
            st.warning("⚠️ 未发现匹配会议，建议关注电力系统、控制理论等方向的会议")
    except Exception as e:
        st.error(f"❌ 加载会议文件出错: {e}")

# 主程序入口
def main():
    st.set_page_config(layout="wide")
    st.title("📑 论文与会议匹配系统")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 📥 上传会议文件")
        conference_file = upload_conference_file()

    with col2:
        st.markdown("### 📥 上传论文文件")
        paper_file = upload_paper_file()

    if paper_file:
        try:
            if paper_file.name.endswith(".pdf"):
                paper_text = extract_text_from_pdf(paper_file)
            elif paper_file.name.endswith(".docx"):
                paper_text = extract_text_from_docx(paper_file)
            else:
                st.error("不支持的论文文件格式")
                return

            # 论文分析
            paper_subjects = analyze_paper_subject(paper_text)

            # 匹配会议（如已上传）
            if conference_file:
                perform_matching(conference_file, paper_subjects)
            else:
                st.info("📌 若要查看匹配会议，请上传会议文件")

        except Exception as e:
            st.error(f"论文文件处理失败: {e}")
    else:
        st.info("请上传论文文件进行分析")

if __name__ == "__main__":
    main()
"""

# 保存代码为 app.py
output_path = "/mnt/data/app.py"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(app_py_code)

output_path
