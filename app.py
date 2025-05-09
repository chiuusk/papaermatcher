import streamlit as st
import pandas as pd
import datetime
import re
from PyPDF2 import PdfReader
import docx
from sentence_transformers import SentenceTransformer, util

st.set_page_config(layout="wide")
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

st.title("📚 论文匹配会议助手")

# 上传会议文件（固定一次）
st.sidebar.header("会议文件")
conference_file = st.sidebar.file_uploader("上传会议文件（只需一次）", type=["xlsx"], key="conf")

if conference_file:
    try:
        df_conf = pd.read_excel(conference_file)
        df_conf.columns = df_conf.columns.str.strip()
        df_conf.rename(columns={
            "会议名称": "会议名",
            "会议系列名": "会议系列名",
            "会议主题方向": "会议主题方向",
            "细分方向": "细分关键词",
            "是否动态出版": "动态出版标记",
            "截稿日期": "截稿时间"
        }, inplace=True)
        st.session_state.conference_df = df_conf
        st.success("✅ 会议文件已上传成功")
    except Exception as e:
        st.error(f"❌ 会议文件读取失败：{e}")

# 上传论文文件
st.header("上传论文文件")
paper_file = st.file_uploader("上传论文文件（PDF 或 Word）", type=["pdf", "docx"], key="paper")

# 文本提取
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "\n".join([p.extract_text() for p in reader.pages[:3] if p.extract_text()])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# 提取论文信息
def extract_paper_info(text):
    lines = text.strip().split("\n")
    title = lines[0] if lines else "未知标题"
    abstract_match = re.search(r"(Abstract|摘要)[\s:：]*(.+?)(\n|Keywords|关键词)", text, re.DOTALL | re.IGNORECASE)
    keywords_match = re.search(r"(Keywords|关键词)[\s:：]*(.+)", text, re.IGNORECASE)
    abstract = abstract_match.group(2).strip() if abstract_match else ""
    keywords = keywords_match.group(2).strip() if keywords_match else ""
    return title, abstract, keywords

# 学科方向标签
directions = {
    "电力电子": ["PWM", "inverter", "rectifier", "电源控制"],
    "控制工程": ["PI control", "闭环", "控制系统", "reinforcement learning"],
    "人工智能": ["深度学习", "神经网络", "机器学习"],
    "通信技术": ["信道", "调制", "通信协议"],
    "材料科学": ["材料性能", "微观结构", "合成"],
    "心理学": ["认知", "行为", "心理测量"],
    "社会学": ["人口", "社会行为", "城市化"],
    "医学": ["疾病", "治疗", "病例"]
}

if paper_file and "conference_df" in st.session_state:
    with st.spinner("正在分析论文..."):
        # 提取文本
        if paper_file.type == "application/pdf":
            text = extract_text_from_pdf(paper_file)
        else:
            text = extract_text_from_docx(paper_file)

        title, abstract, keywords = extract_paper_info(text)
        full_text = f"{title} {abstract} {keywords}"
        embedding = model.encode(full_text, convert_to_tensor=True)

        # 学科方向分析
        st.subheader("🔍 学科方向识别")
        direction_names = list(directions.keys())
        dir_embeddings = model.encode(direction_names, convert_to_tensor=True)
        sims = util.cos_sim(embedding, dir_embeddings)[0]
        top_indices = sims.argsort(descending=True)[:3]
        for idx in top_indices:
            dname = direction_names[idx]
            reason = ", ".join([kw for kw in directions[dname] if kw.lower() in full_text.lower()])
            reason = reason if reason else "关键词匹配度高"
            st.markdown(f"- **{dname}**：相关词 - {reason}")

        # 匹配会议
        st.subheader("🎯 匹配结果（含 Symposium 的会议）")
        results = []
        for _, row in st.session_state.conference_df.iterrows():
            if "Symposium" not in str(row["会议名"]):
                continue
            conf_text = f"{row['会议名']} {row.get('会议主题方向','')} {row.get('细分关键词','')}"
            conf_embedding = model.encode(conf_text, convert_to_tensor=True)
            score = util.cos_sim(embedding, conf_embedding).item()
            results.append({
                "匹配度": score,
                "推荐会议": f"{row['会议系列名']} - {row['会议名']}",
                "会议主题方向": row.get("会议主题方向", ""),
                "细分关键词": row.get("细分关键词", ""),
                "动态出版标记": row.get("动态出版标记", ""),
                "官网链接": row.get("官网链接", ""),
                "距离截稿还有": (row["截稿时间"] - datetime.datetime.now().date()).days if pd.notna(row.get("截稿时间")) else "未知",
                "匹配理由": f"论文与关键词【{row.get('细分关键词', '')}】和方向【{row.get('会议主题方向', '')}】相符"
            })

        top_matches = sorted(results, key=lambda x: x["匹配度"], reverse=True)[:3]
        for match in top_matches:
            st.markdown(f"### 📌 {match['推荐会议']}")
            st.markdown(f"- **会议主题方向**：{match['会议主题方向']}")
            st.markdown(f"- **细分关键词**：{match['细分关键词']}")
            st.markdown(f"- **动态出版标记**：{match['动态出版标记']}")
            st.markdown(f"- **官网链接**：[点此查看]({match['官网链接']})")
            st.markdown(f"- **距离截稿还有**：{match['距离截稿还有']} 天")
            st.markdown(f"- **匹配理由**：{match['匹配理由']}")
            st.markdown("---")
