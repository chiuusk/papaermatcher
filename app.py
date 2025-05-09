import streamlit as st
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 页面配置
st.set_page_config(page_title="论文会议智能推荐", layout="wide")
st.title("📚 论文会议智能推荐系统")

# 文件上传部分
st.sidebar.header("1️⃣ 上传论文文件（PDF 或 Word）")
paper_file = st.sidebar.file_uploader("上传 PDF 或 Word 文件", type=["pdf", "docx"])

st.sidebar.header("2️⃣ 上传会议 Excel 文件")
conf_file = st.sidebar.file_uploader("上传会议列表文件（Excel）", type=["xlsx"])

# 获取当前时间
now = datetime.datetime.now()

# 提取论文文本
def extract_text_from_file(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        for page in reader.pages[:2]:
            text += page.extract_text() or ""
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

# 从会议官网提取关键词
def extract_keywords_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        return text
    except:
        return ""

# 主逻辑
if paper_file and conf_file:
    with st.spinner("正在分析论文与会议匹配度..."):
        try:
            # 1. 读取论文内容
            paper_text = extract_text_from_file(paper_file)

            # 提取关键词
            tfidf_vec = TfidfVectorizer(stop_words='english', max_features=10)
            paper_tfidf = tfidf_vec.fit_transform([paper_text])
            paper_keywords = tfidf_vec.get_feature_names_out()

            st.markdown("### 📄 自动提取的论文关键词")
            st.write(", ".join(paper_keywords))

            # 2. 读取会议数据
            df = pd.read_excel(conf_file)

            # 列名映射
            df = df.rename(columns={"会议名": "会议名称"})

            required_columns = ["会议系列名", "会议名称", "当前状态", "官网链接", "会议地点", "会议方向", "会议主题方向", "细分关键词", "截稿时间"]
            if not all(col in df.columns for col in required_columns):
                st.error(f"Excel 缺少必要字段，请确保包含：{', '.join(required_columns)}")
            else:
                # 3. 过滤条件
                df = df[
                    (df["当前状态"] == "征稿阶段") &
                    (df["官网链接"].notna()) &
                    (df["会议地点"].notna())
                ]

                # 构建会议关键词文本
                df["综合关键词"] = df[["会议方向", "会议主题方向", "细分关键词"]].astype(str).agg(" ".join, axis=1)

                # 访问官网内容并附加
                website_texts = []
                for link in df["官网链接"]:
                    website_texts.append(extract_keywords_from_url(link))
                df["官网内容"] = website_texts

                # 合并关键词和网页文本做匹配
                df["匹配文本"] = df["综合关键词"] + " " + df["官网内容"]

                # 计算相似度
                conf_tfidf = tfidf_vec.transform(df["匹配文本"])
                similarity = cosine_similarity(paper_tfidf, conf_tfidf).flatten()
                df["匹配度"] = similarity

                # 距离截稿时间
                df["距离截稿"] = df["截稿时间"].apply(lambda d: (pd.to_datetime(d) - now).days if pd.notnull(d) else None)

                # 推荐前2名
                top_matches = df.sort_values(by="匹配度", ascending=False).head(2)

                st.markdown("### 🏆 推荐会议")
                for _, row in top_matches.iterrows():
                    st.markdown(f"""
                    #### {row['会议系列名']} - {row['会议名称']}
                    - **官网链接：** [{row['官网链接']}]({row['官网链接']})
                    - **匹配理由：** 关键词内容相符（匹配度: {row['匹配度']:.2f}）
                    - **距离截稿时间：** {row['距离截稿']} 天
                    """)

                st.success("推荐完成！")

        except Exception as e:
            st.error(f"运行出错：{e}")
