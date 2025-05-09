import streamlit as st
import pandas as pd
import datetime
import time

# 计算剩余天数
def calculate_days_left(cutoff_date):
    try:
        return (cutoff_date - datetime.datetime.now().date()).days
    except:
        return "未知"

# 上传函数
def upload_conference_file():
    return st.file_uploader("📅 上传会议文件", type=["xlsx"], key="conf_file")

def upload_paper_file():
    return st.file_uploader("📄 上传论文文件", type=["pdf", "docx"], key="paper_file")

# 论文学科方向分析（模拟）
def analyze_paper_subject(paper_file):
    st.subheader("📘 论文学科方向分析")
    st.markdown("通过标题与摘要提取的关键词，系统分析如下学科权重：")

    # 示例结果
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }

    for subject, percent in subjects.items():
        st.markdown(f"- **{subject}**：{percent}%")
    return subjects

# 主匹配函数
def perform_matching(conference_file, paper_file):
    try:
        conference_data = pd.read_excel(conference_file)
    except Exception as e:
        st.error(f"会议文件加载失败: {e}")
        return

    paper_subjects = analyze_paper_subject(paper_file)

    st.subheader("🎯 匹配推荐会议")

    matching_conferences = []
    for _, row in conference_data.iterrows():
        try:
            topics = str(row['会议主题方向']).split(',')
            score = sum([paper_subjects.get(topic.strip(), 0) for topic in topics])
            if score > 0:
                matching_conferences.append({
                    "会议名称": f"{row['会议系列名']} - {row['会议名']}",
                    "官网链接": row.get("官网链接", ""),
                    "主题方向": row.get("会议主题方向", ""),
                    "动态出版": row.get("动态出版标记", ""),
                    "截稿时间": row.get("截稿时间", "未知"),
                    "剩余天数": calculate_days_left(row.get("截稿时间"))
                })
        except:
            continue

    if matching_conferences:
        for i, conf in enumerate(matching_conferences):
            st.markdown(f"##### 🏁 推荐会议 {i+1}: **{conf['会议名称']}**")
            st.markdown(f"- **主题方向**: {conf['主题方向']}")
            st.markdown(f"- **动态出版**: {conf['动态出版']}")
            st.markdown(f"- **官网链接**: [点击访问]({conf['官网链接']})" if conf["官网链接"] else "- 官网链接: 暂无")
            st.markdown(f"- **截稿时间**: {conf['截稿时间']}（还有 **{conf['剩余天数']} 天**）")
            st.markdown("---")
    else:
        st.markdown("⚠️ 未发现完全匹配的会议，以下是基于大方向的推荐：")
        for _, row in conference_data.iterrows():
            if any(subject in row.get("会议主题方向", "") for subject in paper_subjects):
                st.markdown(f"**📌 可能相关会议：{row['会议系列名']} - {row['会议名']}**")
                st.markdown(f"- 主题方向: {row['会议主题方向']}")
                st.markdown("---")

# 主界面
def main():
    st.set_page_config(page_title="论文会议匹配工具", layout="wide")

    st.title("📚 智能论文会议匹配系统")
    st.markdown("根据上传的论文内容，自动识别其研究方向并匹配合适的会议。")

    # 页面分栏
    left, right = st.columns(2)

    with left:
        st.markdown("### 🗂 上传会议文件")
        conference_file = upload_conference_file()

    with right:
        st.markdown("### 📑 上传论文文件")
        paper_file = upload_paper_file()

    if paper_file:
        time.sleep(0.5)
        perform_matching(conference_file, paper_file)
    else:
        st.info("请上传论文文件以开始匹配。")

if __name__ == "__main__":
    main()
