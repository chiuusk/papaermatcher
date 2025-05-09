import streamlit as st
import pdfplumber
import docx
import pandas as pd
import datetime
from sentence_transformers import SentenceTransformer, util
import os

# 初始化模型
model = SentenceTransformer('all-MiniLM-L6-v2')

st.title("📄 智能论文匹配推荐会议工具")

# Session state 存储上传文件
if 'conference_file' not in st.session_state:
    st.session_state.conference_file = None
if 'paper_file' not in st.session_state:
    st.session_state.paper_file = None

# 上传会议文件（Excel）
st.header("① 上传会议文件（Excel）")
conference_uploaded = st.file_uploader("包含字段：会议名称、会议方向、会议主题方向、细分关键词、动态出版标记、截稿时间、官网链接", type=["xlsx"], key="conf_upload")

if st.button("清除会议文件"):
    st.session_state.conference_file = None
    conference_uploaded = None

if conference_uploaded:
    try:
        conf_df = pd.read_excel(conference_uploaded, engine='openpyxl')
        required_cols = ['会议名称', '会议方向', '会议主题方向', '细分关键词', '动态出版标记', '截稿时间', '官网链接']
        for col in required_cols:
            if col not in conf_df.columns:
                st.error(f"❌ 缺少必要字段：{col}")
                st.stop()
        st.success("✅ 会议文件上传成功")
        st.session_state.conference_file = conf_df
    except Exception as e:
        st.error(f"会议文件读取失败：{e}")
        st.stop()

# 上传论文文件（Word 或 PDF）
st.header("② 上传论文文件（Word 或 PDF）")
paper_uploaded = st.file_uploader("上传论文文件（PDF 或 Word）", type=["pdf", "docx"], key="paper_upload")

if st.button("清除论文文件"):
    st.session_state.paper_file = None
    paper_uploaded = None

if paper_uploaded:
    try:
        def extract_text(file):
            if file.name.endswith(".pdf"):
                with pdfplumber.open(file) as pdf:
                    return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
            elif file.name.endswith(".docx"):
                doc = docx.Document(file)
                return "\n".join(p.text for p in doc.paragraphs)
            else:
                return ""

        paper_text = extract_text(paper_uploaded)

        # 简单分段提取摘要、关键词、结论
        def extract_sections(text):
            text_lower = text.lower()
            abstract, keywords, conclusion = "", "", ""

            if "abstract" in text_lower:
                abstract = text[text_lower.find("abstract"):text_lower.find("introduction") if "introduction" in text_lower else 1000]
            if "keywords" in text_lower:
                keywords = text[text_lower.find("keywords"):text_lower.find("\n", text_lower.find("keywords") + 8)]
            if "conclusion" in text_lower:
                conclusion = text[text_lower.find("conclusion"):text_lower.find("references") if "references" in text_lower else len(text)]

            return abstract + " " + keywords + " " + conclusion

        extracted_text = extract_sections(paper_text)
        paper_embedding = model.encode(extracted_text, convert_to_tensor=True)

        results = []

        for _, row in st.session_state.conference_file.iterrows():
            all_text = f"{row['会议方向']} {row['会议主题方向']} {row['细分关键词']}"
            conf_embedding = model.encode(all_text, convert_to_tensor=True)
            score = float(util.cos_sim(paper_embedding, conf_embedding)[0])

            # 匹配关键词详细展示
            matched_keywords = []
            if isinstance(row['细分关键词'], str):
                for keyword in row['细分关键词'].split(','):
                    if keyword.strip().lower() in extracted_text.lower():
                        matched_keywords.append(keyword.strip())

            try:
                deadline = pd.to_datetime(row['截稿时间'], errors='coerce')
                days_left = (deadline - datetime.datetime.now()).days if not pd.isnull(deadline) else "未知"
            except:
                days_left = "未知"

            results.append({
                "会议名称": row['会议名称'],
                "官网链接": row['官网链接'],
                "匹配度": score,
                "匹配关键词": matched_keywords,
                "距离截稿时间": days_left
            })

        top_results = sorted(results, key=lambda x: x["匹配度"], reverse=True)[:2]

        st.header("🎯 推荐会议结果")
        for res in top_results:
            st.subheader(res["会议名称"])
            st.markdown(f"🔗 [会议官网链接]({res['官网链接']})")
            st.markdown(f"📌 匹配理由：**相似度 {res['匹配度']:.2f}**，关键词匹配：{', '.join(res['匹配关键词']) if res['匹配关键词'] else '无关键词匹配'}")
            st.markdown(f"⏰ 距离截稿时间：{res['距离截稿时间']} 天")
            st.markdown("---")

    except Exception as e:
        st.error(f"处理时出错：{e}")
