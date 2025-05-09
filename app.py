import streamlit as st
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import tempfile
import os

# 初始化模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 学科领域库（可根据实际需要扩展）
academic_fields = [
    "计算机科学", "电子工程", "生物医学", "化学", "物理", "材料科学", 
    "医学", "人工智能", "数据科学", "社会学", "心理学", "环境科学", 
    "经济学", "教育学", "社会学", "地理学", "法学"
]

# 提取论文文本
def extract_paper_text(pdf_file):
    """从PDF文件中提取文本"""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + " "
    return text.strip()

# 提取学科方向
def extract_paper_research_field(text):
    """
    从论文文本中提取研究方向的简单方法：可以根据文本嵌入计算与已知学科方向的相似度
    """
    # 用模型计算论文文本的嵌入向量
    paper_embedding = model.encode(text, convert_to_tensor=True)

    # 创建学科方向的嵌入向量
    field_embeddings = model.encode(academic_fields, convert_to_tensor=True)

    # 计算与每个学科方向的相似度
    similarities = util.cos_sim(paper_embedding, field_embeddings).cpu().numpy().flatten()

    # 按相似度排序并返回前三个学科方向及其相似度
    top_indexes = similarities.argsort()[::-1][:3]
    result = [(academic_fields[idx], similarities[idx]) for idx in top_indexes]
    total_similarity = sum([similarity for _, similarity in result])
    
    # 返回学科方向及其对应的百分比
    result_with_percentage = [(field, round(similarity / total_similarity * 100, 2)) for field, similarity in result]
    return result_with_percentage

# Streamlit 页面设置
st.set_page_config(layout="wide")
st.title("📄 论文分析工具")

# 上传论文文件
uploaded_file = st.file_uploader("上传论文 PDF 文件", type=["pdf"])

if uploaded_file:
    st.success("✅ 论文文件上传成功！正在提取信息...")

    # 提取论文文本
    paper_text = extract_paper_text(uploaded_file)

    # 进行学科方向分析
    paper_fields = extract_paper_research_field(paper_text)

    # 显示论文的学科方向及其占比
    st.subheader("📚 论文学科专业方向分析")
    st.write("### 论文涉及的学科方向：")
    for field, percentage in paper_fields:
        st.write(f"**{field}**: {percentage}%")

    st.write("### 请确认论文涉及的学科方向及占比。")
    st.write("如果有误，请修改或调整相关参数。")
