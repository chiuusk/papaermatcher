import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from PyPDF2 import PdfReader
import time

# Load model for matching
model = SentenceTransformer('all-MiniLM-L6-v2')

def analyze_subject_direction(text):
    # Placeholder function for analyzing paper's research direction
    # You can replace this with an actual subject classification model or logic
    if "Reinforcement Learning" in text:
        return {
            "Machine Learning": 60,
            "Control Engineering": 30,
            "Electrical Engineering": 10
        }
    # Add more logic for other subject directions
    return {
        "Other": 100
    }

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def match_paper_to_conference(paper_text, conferences_df):
    paper_direction = analyze_subject_direction(paper_text)
    paper_direction_str = ", ".join([f"{k}: {v}%" for k, v in paper_direction.items()])
    
    st.write(f"论文的学科方向分析结果：{paper_direction_str}")
    
    # Using the title, abstract, and keywords of the paper to calculate similarity
    paper_embedding = model.encode([paper_text])
    conference_names = conferences_df['会议名'] + " " + conferences_df['会议系列名']
    conference_embeddings = model.encode(conference_names.tolist())
    
    similarities = cosine_similarity(paper_embedding, conference_embeddings)
    matched_indices = np.argsort(similarities[0])[::-1][:3]  # Get top 3 matching conferences
    
    results = []
    for idx in matched_indices:
        conf_row = conferences_df.iloc[idx]
        results.append({
            "会议名称": conf_row['会议名'],
            "会议系列名": conf_row['会议系列名'],
            "官网链接": conf_row['官网链接'],
            "截稿时间": conf_row['截稿时间'],
            "匹配理由": f"该会议与论文的学科方向（{paper_direction_str}）相关，适合该论文的研究方向。"
        })
    
    return results

# Streamlit UI
st.title('论文与会议匹配工具')

# 上传会议文件（只上传一次）
conference_file = st.file_uploader("上传会议文件", type=["xlsx"], key="conference_uploader")

if conference_file:
    # Read the uploaded conference file
    conferences_df = pd.read_excel(conference_file)
    st.session_state.conferences_df = conferences_df
    st.write("会议文件已上传。")

# 上传论文文件（允许多次上传）
paper_file = st.file_uploader("上传论文文件", type=["pdf"], key="paper_uploader")

if paper_file:
    paper_text = extract_text_from_pdf(paper_file)
    if 'conferences_df' in st.session_state:
        # Perform matching only if conference file has been uploaded
        with st.spinner("正在进行论文与会议匹配..."):
            results = match_paper_to_conference(paper_text, st.session_state.conferences_df)
            time.sleep(2)  # Simulate processing time
        st.write("匹配结果：")
        for result in results:
            st.write(f"**会议名称**: {result['会议名称']}")
            st.write(f"**会议系列名**: {result['会议系列名']}")
            st.write(f"**官网链接**: {result['官网链接']}")
            st.write(f"**截稿时间**: {result['截稿时间']}")
            st.write(f"**匹配理由**: {result['匹配理由']}")
    else:
        st.warning("请先上传会议文件。")

# 清除文件按钮
if st.button("清除会议文件"):
    st.session_state.conferences_df = None
    st.experimental_rerun()

if st.button("清除论文文件"):
    st.session_state.paper_uploader = None
    st.experimental_rerun()
