import streamlit as st
import pandas as pd
import datetime
import fitz  # PyMuPDF
import docx
import re

# 读取 PDF 内容
def extract_text_from_pdf(file):
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "".join(page.get_text() for page in doc)
    except Exception as e:
        st.error(f"PDF 解析失败: {e}")
        return ""

# 读取 Word 内容
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Word 解析失败: {e}")
        return ""

# 综合提取论文内容
def extract_paper_text(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    return ""

# 提取标题（假设标题位于文本开头）
def extract_title(text):
    title = text.split('\n')[0]  # 假设标题在文本的第一行
    return title.strip()

# 提取关键词（通过正则查找关键词）
def extract_keywords(text):
    keywords = []
    keyword_pattern = r"Keywords?:\s*(.*?)(?:\n|$)"  # 找到关键词字段
    match = re.search(keyword_pattern, text, re.IGNORECASE)
    if match:
        keywords = match.group(1).split(",")  # 关键词之间以逗号分隔
        keywords = [kw.strip() for kw in keywords]
    return keywords


# 论文学科方向分析
def analyze_subjects(text):
    subject_keywords = {
        "电力系统": ["power system", "voltage", "rectifier", "电网", "电力"],
        "控制理论": ["control", "PID", "控制器", "控制系统", "stability"],
        "计算机科学": ["algorithm", "data", "neural", "人工智能", "machine learning"],
        "通信工程": ["network", "5G", "通信", "信道", "wireless"],
        "电子工程": ["信号", "电路", "modulation", "sensor", "嵌入式"]
    }

    counts = {}
    lower_text = text.lower()
    for subject, keywords in subject_keywords.items():
        count = sum(lower_text.count(kw.lower()) for kw in keywords)
        if count > 0:
            counts[subject] = count

    total = sum(counts.values())
    if total == 0:
        return {}

    return {k: round(v / total * 100, 2) for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)}

# 匹配会议
def match_conferences(conference_data, paper_subjects):
    matches = []
    for _, row in conference_data.iterrows():
        conf_subjects = str(row.get("会议主题方向", "")).split(",")
        matched = [s for s in paper_subjects if any(s in c for c in conf_subjects)]
        score = sum(paper_subjects[s] for s in matched)
        if score > 0:
            matches.append({
                "会议系列名与会议名": f"{row.get('会议系列名', '')} - {row.get('会议名', '')}",
                "官网链接": row.get("官网链接", ""),
                "动态出版标记": row.get("动态出版标记", ""),
                "截稿时间": row.get("截稿时间", ""),
                "剩余天数": (pd.to_datetime(row.get("截稿时间")).date() - datetime.date.today()).days,
                "匹配学科": ", ".join(matched)
            })
    return matches

# 主体
def main():
    st.set_page_config(layout="wide")
    st.title("📄 论文与会议智能匹配系统")

    col1, col2 = st.columns([1, 1])

    # 左侧会议文件上传
    with col1:
        st.subheader("📁 上传会议文件")
        conference_file = st.file_uploader("上传 Excel 格式的会议列表", type=["xlsx"], key="conf", label_visibility="collapsed")
        conference_data = None
        if conference_file:
            try:
                conference_data = pd.read_excel(conference_file)
                st.success("会议文件加载成功")
            except Exception as e:
                st.error(f"读取会议文件失败: {e}")

    # 右侧论文上传
    with col2:
        st.subheader("📄 上传论文文件")
        paper_file = st.file_uploader("上传 PDF / Word 论文", type=["pdf", "docx"], key="paper", label_visibility="collapsed")
        if paper_file:
            st.info("已上传论文文件，正在分析中...")
            text = extract_paper_text(paper_file)
            if text:
                # 提取题目和关键词
                title = extract_title(text)
                keywords = extract_keywords(text)

                # 显示论文题目和关键词
                st.markdown("### 📄 论文题目与关键词")
                st.write(f"**中文题目：** {title}")
                st.write(f"**English Title:** {title}")  # 假设英文题目和中文题目一样，你可以根据实际情况调整

                st.write(f"**关键词 (中文 / English Keywords):**")
                for kw in keywords:
                    st.write(f"- **中文:** {kw}")
                    st.write(f"- **English:** {kw}")

                # 学科方向分析
                subjects = analyze_subjects(text)
                if subjects:
                    st.markdown("### 📊 论文学科方向分析")
                    for subject, percent in subjects.items():
                        st.write(f"- {subject}: {percent}%")
                else:
                    st.warning("未识别到明确的学科方向")

                # 会议匹配
                if conference_data is not None:
                    st.markdown("### 📌 正在匹配会议...")
                    matches = match_conferences(conference_data, subjects)
                    if matches:
                        for m in matches:
                            st.markdown(f"#### ✅ 推荐会议：{m['会议系列名与会议名']}")
                            st.markdown(f"- 官网链接: [{m['官网链接']}]({m['官网链接']})")
                            st.markdown(f"- 动态出版标记: {m['动态出版标记']}")
                            st.markdown(f"- 截稿时间: {m['截稿时间']} (剩余 {m['剩余天数']} 天)")
                            st.markdown(f"- 匹配学科方向: {m['匹配学科']}")
                    else:
                        st.info("未找到匹配会议。可根据分析结果尝试其他领域会议。")
            else:
                st.warning("论文内容无法读取，请检查文件格式。")

if __name__ == "__main__":
    main()
