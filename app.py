import streamlit as st
import pandas as pd
import datetime
import time  # 添加 time 模块
from PyPDF2 import PdfReader
import docx

# 读取会议文件
def read_conference_file(file):
    return pd.read_excel(file)

# 读取PDF文件内容
def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# 读取Word文件内容
def read_word(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

# 判断论文学科方向
def analyze_paper_subject(text):
    subjects = {
        '电气工程': ['PWM Rectifier', 'PI Control', 'Reinforcement Learning', 'Power Electronics', 'Control Theory'],
        '计算机科学': ['Machine Learning', 'Artificial Intelligence', 'Neural Networks', 'Data Science'],
        '医学': ['Biology', 'Medical Imaging', 'Neuroscience', 'Healthcare'],
        '机械工程': ['Mechanical Systems', 'Robotics', 'Control Systems', 'Automation'],
    }
    
    paper_subjects = {}
    
    for subject, keywords in subjects.items():
        match_count = sum(keyword in text for keyword in keywords)
        if match_count > 0:
            paper_subjects[subject] = match_count
    
    total_matches = sum(paper_subjects.values())
    subject_percentages = {subject: (matches / total_matches) * 100 for subject, matches in paper_subjects.items()}
    
    return paper_subjects, subject_percentages

# 计算截稿时间剩余天数
def calculate_days_left(cutoff_date):
    if pd.notna(cutoff_date):
        return (cutoff_date - datetime.datetime.now().date()).days
    return "未知"

# 显示进度条
def show_progress_bar():
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.05)

# 主程序
def main():
    st.title("论文匹配工具")
    
    # 上传会议文件
    conference_file = st.file_uploader("上传会议文件", type=["xlsx"])
    if conference_file is not None:
        st.session_state.conference_file = read_conference_file(conference_file)
        st.success("会议文件上传成功")
    
    # 上传论文文件
    paper_file = st.file_uploader("上传论文文件", type=["pdf", "docx"])
    if paper_file is not None:
        # 读取论文内容
        if paper_file.type == "application/pdf":
            paper_text = read_pdf(paper_file)
        elif paper_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            paper_text = read_word(paper_file)
        
        # 分析学科方向
        paper_subjects, subject_percentages = analyze_paper_subject(paper_text)
        
        # 显示学科方向分析
        st.subheader("论文学科方向分析")
        for subject, percentage in subject_percentages.items():
            st.write(f"{subject}: {percentage:.2f}%")
        
        # 显示学科分析详情
        st.subheader("学科分析详细信息")
        for subject, count in paper_subjects.items():
            st.write(f"学科方向：{subject}, 匹配关键词个数：{count}")
        
        # 显示匹配结果
        if 'conference_file' in st.session_state:
            show_progress_bar()  # 展示进度条
            match_results = []
            
            # 获取会议文件
            conference_data = st.session_state.conference_file
            
            # 遍历会议文件中的每一行
            for _, row in conference_data.iterrows():
                if "Symposium" in row["会议名"]:
                    # 忽略不包含Symposium的行
                    conference_title = f"{row['会议系列名']} - {row['会议名']}"
                    conference_url = row["官网链接"]
                    cutoff_date = row["截稿时间"]
                    dynamic_publish = row["动态出版标记"]
                    days_left = calculate_days_left(cutoff_date)  # 使用新的函数
                    
                    # 匹配分析
                    matched_subjects = []
                    for subject in paper_subjects.keys():
                        if subject in row["会议主题方向"] or subject in row["细分关键词"]:
                            matched_subjects.append(subject)
                    
                    if matched_subjects:
                        match_results.append({
                            "推荐会议": conference_title,
                            "官网链接": conference_url,
                            "动态出版标记": dynamic_publish,
                            "截稿时间剩余": f"{days_left}天",
                            "匹配学科方向": matched_subjects,
                        })
            
            # 展示匹配结果
            if match_results:
                st.subheader("匹配的推荐会议")
                for result in match_results[:3]:  # 只展示前3个推荐
                    st.write(f"**推荐会议：** {result['推荐会议']}")
                    st.write(f"官网链接：{result['官网链接']}")
                    st.write(f"动态出版标记：{result['动态出版标记']}")
                    st.write(f"距离截稿还有：{result['截稿时间剩余']}")
                    st.write(f"匹配学科方向：{', '.join(result['匹配学科方向'])}")
            else:
                st.write("没有找到合适的会议")

if __name__ == "__main__":
    main()
