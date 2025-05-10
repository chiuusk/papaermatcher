import streamlit as st
import pandas as pd
import re
import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googletrans import Translator

st.set_page_config(page_title="会议匹配助手", layout="wide")

if 'conference_df' not in st.session_state:
    st.session_state.conference_df = None

translator = Translator()

def extract_title_abstract_keywords(text):
    lines = text.splitlines()
    title, abstract, keywords = "", "", ""
    title_found, abstract_found, keywords_found = False, False, False

    for i, line in enumerate(lines):
        clean_line = line.strip()
        if not title_found and 5 < len(clean_line) < 200:
            title = clean_line
            title_found = True
            continue

        if not abstract_found and re.search(r'摘要|Abstract', clean_line, re.IGNORECASE):
            abstract_lines = []
            for j in range(i+1, len(lines)):
                l = lines[j].strip()
                if re.search(r'关键词|关键字|Keywords|Index Terms', l, re.IGNORECASE):
                    break
                abstract_lines.append(l)
            abstract = " ".join(abstract_lines).strip()
            abstract_found = True
            continue

        if not keywords_found and re.search(r'关键词|关键字|Keywords|Index Terms', clean_line, re.IGNORECASE):
            keywords = re.sub(r'(关键词|关键字|Keywords|Index Terms)[:：]?', '', clean_line, flags=re.IGNORECASE).strip()
            keywords_found = True
            continue

    return title, abstract, keywords

def translate_text(text, src='auto', dest='en'):
    try:
        return translator.translate(text, src=src, dest=dest).text
    except Exception:
        return text

def analyze_subject_direction(text, top_k=5):
    return jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)

def match_conference(paper_text, conference_df):
    tfidf = TfidfVectorizer()
    corpus = [paper_text] + conference_df["简介"].fillna("").tolist()
    tfidf_matrix = tfidf.fit_transform(corpus)
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    conference_df["匹配分数"] = cosine_sim
    return conference_df.sort_values(by="匹配分数", ascending=False).head(5)

# 页面布局
st.title("📌 论文智能匹配会议推荐工具")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📅 上传会议文件")
    conf_file = st.file_uploader("上传会议Excel文件", type=["xls", "xlsx"], key="conf")
    if conf_file:
        st.session_state.conference_df = pd.read_excel(conf_file)
        st.success("✅ 会议文件上传成功")

with col2:
    st.header("📄 上传论文文件")
    paper_file = st.file_uploader("上传论文（TXT格式）", type=["txt"], key="paper")
    if paper_file:
        paper_text = paper_file.read().decode("utf-8")
        title, abstract, keywords = extract_title_abstract_keywords(paper_text)

        if not (title or abstract):
            st.error("❌ 无法识别标题或摘要，请检查论文格式。")
        else:
            st.subheader("📋 提取内容结构")
            st.markdown(f"**标题识别：** {title}")
            st.markdown(f"**摘要识别：** {abstract}")
            st.markdown(f"**关键词识别：** {keywords}")

            # 翻译
            title_en = translate_text(title)
            abstract_en = translate_text(abstract)
            keywords_en = translate_text(keywords)

            st.subheader("🌐 中英文对照")
            st.markdown(f"- **标题**: {title}  \n  **Title**: {title_en}")
            st.markdown(f"- **摘要**: {abstract}  \n  **Abstract**: {abstract_en}")
            st.markdown(f"- **关键词**: {keywords}  \n  **Keywords**: {keywords_en}")

            st.subheader("📊 学科方向关键词分析")
            combined_text = f"{title} {abstract} {keywords}"
            directions = analyze_subject_direction(combined_text)
            for word, score in directions:
                st.write(f"- `{word}`（权重: {round(score, 3)}）")

            if st.session_state.conference_df is not None:
                st.subheader("📎 推荐匹配的会议")
                result_df = match_conference(combined_text, st.session_state.conference_df.copy())
                for idx, row in result_df.iterrows():
                    st.markdown(f"### 🔹 {row['会议名']}")
                    st.markdown(f"- 匹配分数：{round(row['匹配分数'], 4)}")
                    st.markdown(f"- 官网链接：[{row['官网链接']}]({row['官网链接']})")
                    st.markdown("---")
            else:
                st.warning("⚠️ 请先上传会议Excel文件")
