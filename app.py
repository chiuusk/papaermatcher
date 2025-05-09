import streamlit as st
import pandas as pd
import datetime
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
import requests

# 设置页面配置
st.set_page_config(page_title="论文会议匹配推荐", layout="wide")
st.title("📚 论文会议匹配推荐系统")

# 文件上传
st.sidebar.header("1️⃣ 上传论文 PDF")
pdf_file = st.sidebar.file_uploader("上传论文 PDF 文件", type=["pdf"])

st.sidebar.header("2️⃣ 上传会议列表 Excel")
conf_file = st.sidebar.file_uploader("上传会议 Excel 文件", type=["xlsx"])

# 设置匹配参数
st.sidebar.header("3️⃣ 设置匹配参数")
days_today = datetime.datetime.now()

# 文件上传后处理
if pdf_file and conf_file:
    with st.spinner('正在处理文件，请稍候...'):
        try:
            # 读取 PDF 文件
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages[:2]:  # 提取前两页
                text += page.extract_text() or ""
            
            # 提取论文关键词
            vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
            tfidf = vectorizer.fit_transform([text])
            paper_keywords = vectorizer.get_feature_names_out()

            st.markdown("### 📄 论文提取信息")
            st.write("**自动识别关键词：**", ", ".join(paper_keywords))

            # 读取会议数据
            df = pd.read_excel(conf_file)

            # 确认会议数据是否包含 "Keywords" 列
            if 'Keywords' not in df.columns:
                st.error("会议数据中缺少 'Keywords' 列，请检查文件格式。")
            else:
                conf_keywords = df['Keywords']  # 获取会议的关键词列
                st.write("**会议关键词：**", ", ".join(conf_keywords.head()))

                # 计算论文和会议之间的相似度
                vectorizer_conf = TfidfVectorizer(stop_words='english')
                tfidf_conf = vectorizer_conf.fit_transform(conf_keywords.astype(str))
                paper_tfidf = vectorizer_conf.transform([text])
                similarity_scores = cosine_similarity(paper_tfidf, tfidf_conf)

                # 显示相似度排序的会议
                st.markdown("### 🔍 匹配结果")
                similarity_df = pd.DataFrame(similarity_scores.T, columns=["相似度"], index=df["Conference Name"])
                similarity_df = similarity_df.sort_values(by="相似度", ascending=False)

                st.write(similarity_df)

                st.success('文件处理完成！')

        except Exception as e:
            st.error(f"文件处理时出错: {e}")

# 会议爬虫示例（可选）
st.sidebar.header("4️⃣ 可选 - 会议爬虫")
meeting_url = st.sidebar.text_input("输入会议网站URL（可选）")

if meeting_url:
    try:
        response = requests.get(meeting_url, timeout=10)  # 设置请求超时为10秒
        response.raise_for_status()  # 如果状态码不为 200，会抛出异常
        st.write("成功爬取网站数据")
    except requests.exceptions.RequestException as e:
        st.error(f"爬虫请求失败: {e}")
