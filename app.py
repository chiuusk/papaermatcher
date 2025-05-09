import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from PyPDF2 import PdfReader
import tempfile
import os
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📄 论文匹配会议助手")

# 初始化模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 初始化 session_state
for key in ["conference_file", "paper_file"]:
    if key not in st.session_state:
        st.session_state[key] = None

# 左右布局
col1, col2 = st.columns(2)

# 上传会议文件
with col1:
    st.subheader("📅 上传会议文件")
    conference_uploaded = st.file_uploader("选择包含会议信息的Excel文件", type=["xlsx"], key="conf_uploader")
    if st.button("❌ 清除会议文件"):
        st.session_state.conference_file = None
        conference_uploaded = None

    if conference_uploaded:
        try:
            df = pd.read_excel(conference_uploaded)
            df.columns = df.columns.str.strip()

            # 字段名标准化
            rename_map = {}
            if "会议名称" in df.columns:
                rename_map["会议名称"] = "会议名"
            df.rename(columns=rename_map, inplace=True)

            required_columns = ["会议名", "会议方向", "会议主题方向", "细分关键词", "会议系列名", "官网链接", "动态出版标记", "截稿时间"]
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                st.error(f"❌ 缺少必要字段：{ ' / '.join(missing) }")
            else:
                st.session_state.conference_file = df
                st.success("✅ 会议文件上传并读取成功")
        except Exception as e:
            st.error(f"❌ 会议文件读取失败：{e}")

# 上传论文文件
with col2:
    st.subheader("📝 上传论文文件（PDF）")
    paper_uploaded = st.file_uploader("上传论文 PDF 文件", type=["pdf"], key="paper_uploader")
    if st.button("❌ 清除论文文件"):
        st.session_state.paper_file = None
        paper_uploaded = None

    if paper_uploaded:
        try:
            # 临时保存 PDF
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, paper_uploaded.name)
            with open(temp_path, "wb") as f:
                f.write(paper_uploaded.read())

            # 读取 PDF 文本
            reader = PdfReader(temp_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            st.session_state.paper_file = text.strip()
            st.success("✅ 论文内容提取成功")
        except Exception as e:
            st.error(f"❌ PDF 处理失败：{e}")

# 执行匹配
if st.session_state.conference_file is not None and st.session_state.paper_file is not None:
    st.divider()
    st.subheader("📊 匭配结果")

    paper_embedding = model.encode(st.session_state.paper_file, convert_to_tensor=True)
    results = []

    # 处理会议数据
    for _, row in st.session_state.conference_file.iterrows():
        row_text = " ".join(str(row[col]) for col in ["会议方向", "会议主题方向", "细分关键词"] if pd.notna(row[col]))
        row_embedding = model.encode(row_text, convert_to_tensor=True)
        similarity = util.cos_sim(paper_embedding, row_embedding).item()
        
        # 计算截稿时间
        if pd.notna(row.get("截稿时间", None)):
            try:
                deadline = datetime.strptime(str(row["截稿时间"]), "%Y-%m-%d")
                days_left = (deadline - datetime.now()).days
            except Exception as e:
                days_left = "未知"
        else:
            days_left = "未知"
        
        # 提取推荐信息
        results.append({
            "会议推荐标题": f"{row['会议系列名']} - {row['会议名']}",
            "官网链接": row["官网链接"],
            "动态出版标记": row["动态出版标记"],
            "距离截稿时间(天)": days_left,
            "匹配分数": round(similarity, 4),
            "会议方向": row["会议方向"],
            "论文研究方向": "论文研究方向待提取",  # 这里暂时设置为待提取，后续可以加入从论文中提取主要研究方向的代码
            "细分关键词": row["细分关键词"],
            "匹配分析": f"该会议的【{row['会议方向']}】与论文的研究方向匹配度较高。"  # 可根据实际需要调整匹配描述
        })

    # 排序并筛选前3个推荐会议
    sorted_results = sorted(results, key=lambda x: x["匹配分数"], reverse=True)
    top_results = sorted_results[:3]

    # 显示结果
    for result in top_results:
        st.markdown(f"### {result['会议推荐标题']}")
        st.markdown(f"**官网链接**: [点击访问]({result['官网链接']})")
        st.markdown(f"**动态出版标记**: {result['动态出版标记']}")
        st.markdown(f"**距离截稿时间**: {result['距离截稿时间(天)']} 天")
        st.markdown(f"**匹配分数**: {result['匹配分数']}")
        st.markdown(f"**论文研究方向与会议匹配分析**: {result['匹配分析']}")
        st.markdown(f"**细分关键词**: {result['细分关键词']}")
        st.markdown("---")
