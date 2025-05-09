import streamlit as st
import pandas as pd
import datetime
import time
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document

# 读取会议文件
def read_conference_file(file):
    df = pd.read_excel(file)
    return df

# 读取PDF文件内容
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# 读取Word文件内容
def read_word(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

# 显示进度条
def show_progress_bar():
    for _ in range(100):
        time.sleep(0.05)  # 模拟长时间的处理
        st.progress(_ + 1)

# 直接返回截稿日期
def display_cutoff_date(cutoff_date):
    if pd.notna(cutoff_date):
        return cutoff_date.strftime("%Y-%m-%d")
    else:
        return "未知"

# 论文的学科方向分析
def analyze_paper_subject(text):
    subjects = {
        '电气工程': {
            'keywords': ['PWM Rectifier', 'PI Control', 'Reinforcement Learning', 'Power Electronics', 'Control Theory'],
            'description': '电气工程方向，涉及电力电子、控制理论及其在电力系统中的应用。',
        },
        '计算机科学': {
            'keywords': ['Machine Learning', 'Artificial Intelligence', 'Neural Networks', 'Data Science', 'Reinforcement Learning'],
            'description': '计算机科学方向，主要涉及机器学习、人工智能及其应用于数据分析和决策系统。',
        },
        '医学': {
            'keywords': ['Medical Imaging', 'Healthcare', 'Neuroscience', 'Biology', 'Medical Data'],
            'description': '医学方向，涵盖医疗影像、生物医学研究以及临床数据分析等领域。',
        },
        '机械工程': {
            'keywords': ['Mechanical Systems', 'Robotics', 'Control Systems', 'Automation'],
            'description': '机械工程方向，关注机械系统设计、机器人技术及自动化控制。',
        },
        '材料科学': {
            'keywords': ['Material Science', 'Nanotechnology', 'Semiconductor', 'Polymers'],
            'description': '材料科学方向，涉及纳米技术、半导体以及新型材料的开发与应用。',
        },
        '化学工程': {
            'keywords': ['Chemical Engineering', 'Process Optimization', 'Catalysis', 'Polymerization'],
            'description': '化学工程方向，主要研究化学过程、反应工程和催化技术等领域。',
        },
        # 可以继续添加更多学科
    }
    
    paper_subjects = {}
    
    # 统计每个学科方向与论文中匹配的关键词个数
    for subject, data in subjects.items():
        match_count = sum(keyword in text for keyword in data['keywords'])
        if match_count > 0:
            paper_subjects[subject] = {
                'count': match_count,
                'description': data['description'],
            }
    
    total_matches = sum(subject['count'] for subject in paper_subjects.values())
    
    # 计算每个学科的占比
    subject_percentages = {subject: (data['count'] / total_matches) * 100 for subject, data in paper_subjects.items()}
    
    return paper_subjects, subject_percentages

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
        for subject, data in paper_subjects.items():
            st.write(f"学科方向：{subject}, 匹配关键词个数：{data['count']}")
            st.write(f"描述：{data['description']}")
        
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
                    days_left = display_cutoff_date(cutoff_date)  # 显示截稿日期
                    
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
                            "截稿日期": days_left,
                            "匹配学科方向": matched_subjects,
                        })
            
            # 展示匹配结果
            if match_results:
                st.subheader("匹配的推荐会议")
                for result in match_results[:3]:  # 只展示前3个推荐
                    st.write(f"**推荐会议：** {result['推荐会议']}")
                    st.write(f"官网链接：{result['官网链接']}")
                    st.write(f"动态出版标记：{result['动态出版标记']}")
                    st.write(f"截稿日期：{result['截稿日期']}")
                    st.write(f"匹配学科方向：{', '.join(result['匹配学科方向'])}")
            else:
                st.write("没有找到合适的会议")

if __name__ == "__main__":
    main()
