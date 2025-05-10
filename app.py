# 生成完整的 app.py 文件内容，满足用户所有功能与UI要求

app_code = '''
import streamlit as st
import pandas as pd
import datetime
import fitz  # PyMuPDF
import docx
import io

# ---------------- 文件解析函数 ----------------

def extract_text_from_pdf(file):
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF 解析失败: {e}")
        return ""

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\\n"
        return text
    except Exception as e:
        st.error(f"Word 解析失败: {e}")
        return ""

def extract_paper_text(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    else:
        return ""

# ---------------- 学科分析函数 ----------------

def analyze_subjects(text):
    subjects_keywords = {
        "电力系统": ["power system", "voltage", "rectifier", "电网", "电力"],
        "控制理论": ["control", "PID", "稳定性", "控制器", "控制理论"],
        "计算机科学": ["algorithm", "data", "神经网络", "machine learning", "人工智能"],
        "电子工程": ["信号", "电路", "调制", "嵌入式", "sensor"],
        "通信工程": ["network", "无线", "通信", "5G", "信道"]
    }

    counts = {}
    lower_text = text.lower()
    for subject, keywords in subjects_keywords.items():
        count = sum(lower_text.count(keyword.lower()) for keyword in keywords)
        if count > 0:
            counts[subject] = count

    total = sum(counts.values())
    if total == 0:
        return {}

    percentages = {subject: round(count / total * 100, 2) for subject, count in counts.items()}
    sorted_subjects = dict(sorted(percentages.items(), key=lambda x: x[1], reverse=True))
    return sorted_subjects

# ---------------- 匹配函数 ----------------

def calculate_days_left(cutoff_date):
    if isinstance(cutoff_date, str):
        cutoff_date = pd.to_datetime(cutoff_date).date()
    return (cutoff_date - datetime.datetime.now().date()).days

def match_conferences(conference_data, paper_subjects):
    matches = []
    for _, row in conference_data.iterrows():
        conference_subjects = str(row.get("会议主题方向", "")).split(",")
        match_score = 0
        matched = []

        for subject, score in paper_subjects.items():
            for conf_sub in conference_subjects:
                if subject.strip() in conf_sub:
                    match_score += score
                    matched.append(subject)

        if match_score > 0:
            matches.append({
                "会议系列名与会议名": f"{row.get('会议系列名', '')} - {row.get('会议名', '')}",
                "官网链接": row.get("官网链接", ""),
                "动态出版标记": row.get("动态出版标记", ""),
                "截稿时间": row.get("截稿时间", ""),
                "剩余天数": calculate_days_left(row.get("截稿时间", "")),
                "匹配学科": ", ".join(set(matched))
            })
    return matches

# ---------------- 主应用函数 ----------------

def main():
    st.set_page_config(layout="wide")
    st.title("📚 论文与会议匹配系统")

    # 两列布局，左会议右论文
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📁 上传会议文件")
        conference_file = st.file_uploader("上传 Excel 格式的会议列表", type=["xlsx"], key="conf", label_visibility="collapsed")
        conference_data = None
        if conference_file:
            try:
                conference_data = pd.read_excel(conference_file)
                st.success("会议文件加载成功")
            except Exception as e:
                st.error(f"会议文件读取失败: {e}")

    with col2:
        st.subheader("📄 上传论文文件")
        paper_file = st.file_uploader("上传论文文件 (PDF / Word)", type=["pdf", "docx"], key="paper", label_visibility="collapsed")
        if paper_file:
            st.info("已上传论文文件，正在分析中...")
            text = extract_paper_text(paper_file)
            if text:
                subjects = analyze_subjects(text)
                if subjects:
                    st.markdown("### 📊 论文学科方向分析")
                    for subject, percent in subjects.items():
                        st.write(f"- {subject}: {percent}%")
                else:
                    st.warning("未能识别明确的学科方向")
            else:
                st.warning("无法解析论文内容")

            if conference_file and text and subjects:
                st.markdown("### 🧠 正在匹配会议...")
                matches = match_conferences(conference_data, subjects)
                if matches:
                    for match in matches:
                        st.markdown(f"#### 🎯 推荐会议：{match['会议系列名与会议名']}")
                        st.markdown(f"- 官网链接: [{match['官网链接']}]({match['官网链接']})")
                        st.markdown(f"- 动态出版标记: {match['动态出版标记']}")
                        st.markdown(f"- 截稿时间: {match['截稿时间']} (剩余 {match['剩余天数']} 天)")
                        st.markdown(f"- 匹配学科: {match['匹配学科']}")
                else:
                    st.info("未找到匹配的会议，请参考学科方向寻找更多会议。")

if __name__ == "__main__":
    main()
'''

# 保存成 app.py 文件
with open("/mnt/data/app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

"/mnt/data/app.py"
