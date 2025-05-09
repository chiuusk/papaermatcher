import streamlit as st
import pandas as pd
import datetime
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="论文匹配推荐", layout="wide")
st.title("📚 论文会议匹配推荐系统")

st.sidebar.header("1️⃣ 上传论文 PDF")
pdf_file = st.sidebar.file_uploader("上传论文 PDF 文件", type=["pdf"])

st.sidebar.header("2️⃣ 上传会议列表 Excel")
conf_file = st.sidebar.file_uploader("上传会议 Excel 文件", type=["xlsx"])

st.sidebar.header("3️⃣ 设置匹配参数")
days_today = datetime.datetime.now()

if pdf_file and conf_file:
    # 读取 PDF 文件
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages[:2]:  # 取前两页提取信息
        text += page.extract_text() or ""

    # 简单提取关键词（可换更复杂的模型）
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
    tfidf = vectorizer.fit_transform([text])
    paper_keywords = vectorizer.get_feature_names_out()

    st.markdown("### 📄 论文提取信息")
    st.write("**自动识别关键词：**", ", ".join(paper_keywords))

    # 读取会议数据
    df = pd.read_excel(conf_file)
    st.write("会议列表：", df.head())  # 显示会议数据，帮助检查是否读取成功

    # 假设会议列表中有"会议标题"列和"会议主题"列，你可以修改为实际列名
    conference_titles = df['Conference Title']  # 替换为实际的会议标题列
    conference_topics = df['Conference Topics']  # 替换为实际的会议主题列
    
    # 抓取会议网站的关键词（假设会议网站列在 Excel 中）
    def get_conference_keywords(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        keywords_meta = soup.find('meta', {'name': 'keywords'})
        if keywords_meta:
            return keywords_meta.get('content', '')
        else:
            keywords_div = soup.find('div', {'class': 'conference-keywords'})
            return keywords_div.text.strip() if keywords_div else "无关键词"

    # 获取会议关键词（假设会议 Excel 文件中有 URL 列）
    conference_keywords = []
    for url in df['Conference URL']:  # 假设会议 URL 列名为 'Conference URL'
        keywords = get_conference_keywords(url)
        conference_keywords.append(keywords)

    df['Keywords'] = conference_keywords

    # 合并会议标题、主题和爬取的关键词，作为与论文匹配的文本数据
    conference_texts = conference_titles + " " + conference_topics + " " + df['Keywords']
    
    # 计算论文与每个会议的相似度（基于会议标题、主题和关键词）
    vectorizer = TfidfVectorizer(stop_words='english')
    conf_tfidf = vectorizer.fit_transform(conference_texts)
    paper_tfidf = vectorizer.transform([text])

    # 计算相似度
    similarities = cosine_similarity(paper_tfidf, conf_tfidf)
    
    # 找到最匹配的会议
    matched_conferences = df.iloc[similarities.argmax()]
    st.write("### 最匹配的会议")
    st.write(matched_conferences)
    
    # 在上传文件后刷新页面
    st.experimental_rerun()
