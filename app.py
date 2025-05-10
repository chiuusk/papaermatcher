
import streamlit as st
import pandas as pd
import datetime
import os
import fitz  # PyMuPDF，用于PDF解析
import docx
from io import BytesIO

# 设置页面配置
st.set_page_config(page_title="论文会议匹配系统", layout="wide")

# 页面标题
st.title("📄 论文会议匹配与学科方向分析系统")

# 上传区域布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📁 上传会议文件")
    conf_file = st.file_uploader("上传 Excel 会议文件", type=["xlsx"], key="conf")

with col2:
    st.subheader("📄 上传论文文件")
    paper_file = st.file_uploader("上传 PDF 或 Word 文件", type=["pdf", "docx"], key="paper")

# 显示分割线
st.markdown("---")


def extract_paper_content(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        title = text.split("\n")[0].strip() if text else "未知标题"
        abstract = text[:1500].strip()
        keywords = "暂未提取"
        return title, abstract, keywords
    elif file.name.endswith(".docx"):
        document = docx.Document(file)
        full_text = "\n".join([para.text for para in document.paragraphs])
        title = full_text.split("\n")[0].strip() if full_text else "未知标题"
        abstract = full_text[:1500].strip()
        keywords = "暂未提取"
        return title, abstract, keywords
    else:
        return "未知标题", "", ""

def analyze_paper_subject(title, abstract, keywords):
    # 简单关键词识别逻辑，可替换为ML模型
    combined = " ".join([title, abstract, keywords]).lower()
    subjects = {
        "人工智能": ["reinforcement learning", "neural network", "deep learning"],
        "电力电子": ["PWM", "converter", "voltage source", "rectifier"],
        "控制工程": ["PI control", "controller", "feedback"],
        "通信技术": ["5G", "antenna", "signal"],
        "生物医学": ["gene", "clinical", "medical"]
    }
    matched = {}
    for subject, keywords in subjects.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            matched[subject] = score

    if not matched:
        return "📘 未能识别明确的学科方向", "未能匹配任何学科关键词。", ""

    sorted_subjects = sorted(matched.items(), key=lambda x: x[1], reverse=True)
    result = "，".join([f"{k}（{v}）" for k, v in sorted_subjects])
    explanation = "\n".join([f"- **{k}**：匹配了 {v} 个关键词。" for k, v in sorted_subjects])
    return "📘 识别出的学科方向：", result, explanation


def match_paper_to_conference(title, abstract, keywords, conf_df):
    paper_text = " ".join([title, abstract, keywords]).lower()
    results = []
    for idx, row in conf_df.iterrows():
        conf_name = str(row.get("会议名", ""))
        conf_series = str(row.get("会议系列名", ""))
        topics = str(row.get("会议主题方向", "")).lower()
        website = row.get("官网链接", "")
        deadline = row.get("截稿时间", "")
        is_symp = "symposium" in conf_name.lower()

        if not is_symp:
            continue  # 主会不征收论文，跳过

        match_score = sum(kw in topics or kw in conf_name.lower() for kw in title.lower().split())

        if match_score > 0:
            results.append({
                "会议全名": conf_series + " - " + conf_name,
                "匹配得分": match_score,
                "会议主题方向": topics,
                "截稿时间": deadline,
                "官网链接": website
            })

    if not results:
        return None

    df = pd.DataFrame(results).sort_values(by="匹配得分", ascending=False)
    return df.head(5)


# 如果论文上传了就分析
if paper_file is not None:
    with st.spinner("正在分析论文内容..."):
        title, abstract, keywords = extract_paper_content(paper_file)
        heading, result, explanation = analyze_paper_subject(title, abstract, keywords)

    st.markdown("### 🧠 论文学科方向分析")
    st.markdown(f"**论文标题：** {title}")
    st.markdown(f"**识别关键词：** {keywords}")
    st.markdown(f"**{heading}**")
    st.markdown(f"{result}")
    st.markdown(explanation)

# 如果两个文件都有，执行匹配
if paper_file and conf_file:
    conf_df = pd.read_excel(conf_file)
    st.markdown("---")
    st.subheader("📌 匹配推荐的会议（根据论文内容）")

    match_df = match_paper_to_conference(title, abstract, keywords, conf_df)

    if match_df is not None:
        for i, row in match_df.iterrows():
            st.markdown(f"#### 🔹 {row['会议全名']}")
            st.markdown(f"- **主题方向：** {row['会议主题方向']}")
            st.markdown(f"- **截稿时间：** {row['截稿时间']}")
            st.markdown(f"- **会议链接：** [{row['官网链接']}]({row['官网链接']})")
            st.markdown("---")
    else:
        st.markdown("⚠️ 未找到完全匹配的会议，建议查看大方向相近的会议。")

st.markdown("📌 如需复制会议信息，可右键链接或直接点击访问。")
