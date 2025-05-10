import streamlit as st
import os
import fitz  # PyMuPDF
import docx
import re

# ----------------------------
# PDF & Word 文本提取函数
# ----------------------------
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_word(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# ----------------------------
# 简单标题、关键词、摘要提取逻辑
# ----------------------------
def extract_title(text):
    # 假设标题为第一段最长句子
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        return max(lines[:5], key=len)
    return "未识别到标题"

def extract_keywords(text):
    # 规则匹配：关键词/关键字：xxx
    match = re.search(r"(关键词|关键字|Keywords|Key words)\s*[:：]\s*(.+)", text, re.IGNORECASE)
    if match:
        raw_keywords = match.group(2)
        return [kw.strip() for kw in re.split("[,，;；]", raw_keywords)]
    return []

def extract_abstract(text):
    # 匹配“摘要”或“Abstract”段落
    match = re.search(r"(摘要|Abstract)[\s：:]*([\s\S]{100,800})", text)
    if match:
        abstract = match.group(2).strip()
        # 截断至第一个空行或句号
        abstract = re.split(r"\n|\。", abstract)[0].strip()
        return abstract
    return "未识别到摘要"

# ----------------------------
# 翻译函数（模拟）
# ----------------------------
def translate_text(text):
    # 模拟翻译（实际你可以接入百度翻译或 OpenAI）
    return f"[英] {text}"

# ----------------------------
# 学科方向分析（简化示例）
# ----------------------------
def analyze_paper_subject(text):
    text_lower = text.lower()
    subjects = []
    if "machine learning" in text_lower or "深度学习" in text_lower:
        subjects.append(("人工智能", 0.8))
    if "wireless" in text_lower or "5g" in text_lower:
        subjects.append(("通信工程", 0.6))
    if "biology" in text_lower or "癌症" in text_lower:
        subjects.append(("生物医学", 0.7))
    if not subjects:
        subjects.append(("综合类", 0.5))
    return subjects

# ----------------------------
# Streamlit 页面逻辑
# ----------------------------
st.set_page_config(page_title="论文智能提取与会议匹配", layout="wide")
st.title("📄 论文内容提取助手")

uploaded_file = st.file_uploader("上传论文文件（支持 PDF / Word）", type=["pdf", "docx"])

if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            raw_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            raw_text = extract_text_from_word(uploaded_file)
        else:
            st.error("不支持的文件类型")
            st.stop()
        
        st.success("✅ 文本提取成功")

        # 提取结构信息
        title = extract_title(raw_text)
        keywords = extract_keywords(raw_text)
        abstract = extract_abstract(raw_text)

        title_en = translate_text(title)
        keywords_en = [translate_text(k) for k in keywords]
        abstract_en = translate_text(abstract)

        # 页面展示
        st.subheader("📌 标题 / Title")
        st.write(f"**原文：** {title}")
        st.write(f"**翻译：** {title_en}")

        st.subheader("🧠 摘要 / Abstract")
        st.write(f"**原文：** {abstract}")
        st.write(f"**翻译：** {abstract_en}")

        st.subheader("🗂️ 关键词 / Keywords")
        if keywords:
            for i, kw in enumerate(keywords):
                st.markdown(f"- {kw} / {keywords_en[i]}")
        else:
            st.warning("未识别到关键词")

        st.subheader("🔍 学科方向分析")
        subjects = analyze_paper_subject(raw_text)
        for subject, score in subjects:
            st.write(f"- **{subject}** （匹配度：{score*100:.1f}%）")

    except Exception as e:
        st.error(f"❌ 解析过程中出错：{e}")
