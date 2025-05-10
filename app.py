# 这是你所要求的 Streamlit 应用完整代码，满足以下所有条件：
# - 左侧为会议文件上传区，右侧为论文文件上传区
# - 上传论文文件后立即进行学科方向分析
# - 保留上传会议文件后的匹配功能
# - UI清晰，分区域显示，避免混淆
# - 增加上传区域高度以便拖拽
# - 解析PDF或DOCX自动提取内容

app_code = '''
import streamlit as st
import pandas as pd
import datetime
import io
import fitz  # PyMuPDF
import docx
import time

# 显示页面标题
st.set_page_config(layout="wide")
st.title("📄 智能论文会议匹配与学科分析系统")

# 文件上传区域高度
UPLOAD_HEIGHT = 300

# 计算截稿剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 提取 PDF 内容
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return ""

# 提取 DOCX 内容
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return ""

# 提取论文内容
def extract_paper_content(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        return ""

# 简化的学科分析函数（模拟）
def analyze_paper_subject(text):
    subjects = {
        "电力系统": ["voltage", "power", "grid", "电力"],
        "控制理论": ["control", "strategy", "控制", "调节"],
        "计算机科学": ["algorithm", "neural", "学习", "AI", "人工智能"]
    }
    result = {}
    lowered = text.lower()
    total_score = 0

    for subject, keywords in subjects.items():
        score = sum([lowered.count(k.lower()) for k in keywords])
        if score > 0:
            result[subject] = score
            total_score += score

    if not result:
        st.warning("❗未能识别明确的学科方向，请检查论文内容是否为有效文本。")
        return {}

    # 归一化百分比
    for k in result:
        result[k] = round(result[k] / total_score * 100)

    st.subheader("📘 论文学科方向分析")
    for subject, percent in sorted(result.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"- **{subject}**：{percent}%")

    return result

# 匹配函数
def perform_matching(conference_file, paper_subjects):
    try:
        conference_data = pd.read_excel(conference_file)
        st.success("✅ 会议文件加载成功")

        st.subheader("🔍 推荐匹配的会议")

        matching_conferences = []
        for index, row in conference_data.iterrows():
            conference_subjects = str(row.get("会议主题方向", "")).split(',')
            match_score = 0
            for subject in paper_subjects:
                if subject in conference_subjects:
                    match_score += paper_subjects[subject]

            if match_score > 0:
                matching_conferences.append({
                    "会议名": f"{row.get('会议系列名', '')} - {row.get('会议名', '')}",
                    "链接": row.get('官网链接', ''),
                    "出版": row.get('动态出版标记', ''),
                    "截稿": row.get('截稿时间', ''),
                    "剩余天数": calculate_days_left(row.get('截稿时间')) if not pd.isnull(row.get('截稿时间')) else "未知",
                    "匹配方向": row.get('会议主题方向', '')
                })

        if matching_conferences:
            for conf in matching_conferences:
                st.markdown(f"### 🎯 {conf['会议名']}")
                st.markdown(f"- 🔗 [会议官网]({conf['链接']})")
                st.markdown(f"- 📅 截稿时间：{conf['截稿']}（还有 {conf['剩余天数']} 天）")
                st.markdown(f"- 🧩 匹配方向：{conf['匹配方向']}")
                st.markdown(f"- 📤 出版：{conf['出版']}")
        else:
            st.warning("⚠️ 当前论文方向未完全匹配任何会议，可参考推荐方向继续查找。")

    except Exception as e:
        st.error(f"加载会议文件失败：{e}")

# --- UI 分列布局 ---
left, right = st.columns(2)

with left:
    st.markdown("## 📁 上传会议文件")
    conference_file = st.file_uploader("上传会议Excel文件（可选）", type=["xlsx"], label_visibility="collapsed", key="conf", accept_multiple_files=False, help="请上传含有会议主题方向等字段的Excel文件", height=UPLOAD_HEIGHT)

with right:
    st.markdown("## 📝 上传论文文件")
    paper_file = st.file_uploader("上传论文文件（PDF或DOCX）", type=["pdf", "docx"], label_visibility="collapsed", key="paper", accept_multiple_files=False, help="上传后将自动进行论文分析", height=UPLOAD_HEIGHT)

# --- 分析逻辑 ---
if paper_file:
    with st.spinner("正在分析论文内容..."):
        content = extract_paper_content(paper_file)
        if content.strip():
            subjects = analyze_paper_subject(content)
            if conference_file and subjects:
                perform_matching(conference_file, subjects)
        else:
            st.error("论文文件内容无法读取，请上传有效的PDF或Word文档。")
else:
    st.info("📌 请上传论文文件以开始分析")
'''

with open("/mnt/data/app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

"/mnt/data/app.py 已生成，可复制至 GitHub 项目中直接替换部署使用。"
