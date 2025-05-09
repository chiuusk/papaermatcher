import streamlit as st
import pandas as pd
import datetime
import io
import time

# 计算剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 文件上传处理函数
def upload_conference_file():
    uploaded_file = st.file_uploader("上传会议文件", type=["xlsx"])
    return uploaded_file

def upload_paper_file():
    uploaded_file = st.file_uploader("上传论文文件", type=["pdf", "docx"])
    return uploaded_file

# 论文文件学科分析
def analyze_paper_subject(paper_file):
    # 模拟学科分析, 实际可使用NLP模型或规则
    paper_text = "Reinforcement Learning-Based PI Control Strategy for Single-Phase Voltage Source PWM Rectifier"
    
    # 模拟返回结果
    subjects = {
        "电力系统": 40,
        "控制理论": 35,
        "计算机科学": 25
    }
    
    st.write("论文学科方向分析：")
    st.write(f"该论文涉及的学科及其比例：")
    for subject, percent in subjects.items():
        st.write(f"{subject}: {percent}%")
    
    return subjects

# 匹配函数
def perform_matching(conference_file, paper_file):
    if conference_file is not None:
        try:
            # 读取上传的会议文件
            conference_data = pd.read_excel(conference_file)  # 直接从上传的文件中读取
            st.write("会议文件加载成功")
            
            # 获取论文分析结果
            paper_subjects = analyze_paper_subject(paper_file)
            
            matching_conferences = []
            for index, row in conference_data.iterrows():
                # 检查会议是否符合条件，假设示例的匹配条件
                if 'Symposium' not in row['会议名']:
                    # 获取匹配的会议方向
                    conference_subjects = row['会议主题方向'].split(',')  # 假设会议的主题方向列是以逗号分隔
                    matching_score = 0
                    for subject in paper_subjects:
                        if subject in conference_subjects:
                            matching_score += paper_subjects[subject]
                    
                    if matching_score > 0:
                        matching_conferences.append({
                            "会议系列名与会议名": f"{row['会议系列名']} - {row['会议名']}",
                            "官网链接": row['官网链接'],
                            "动态出版标记": row['动态出版标记'],
                            "截稿时间": row['截稿时间'],
                            "剩余天数": calculate_days_left(row['截稿时间']),
                            "论文研究方向匹配": f"与{row['会议主题方向']}匹配"
                        })
            
            # 展示匹配的会议
            if matching_conferences:
                for conference in matching_conferences:
                    st.write(f"**会议推荐：{conference['会议系列名与会议名']}**")
                    st.write(f"官网链接: {conference['官网链接']}")
                    st.write(f"动态出版标记: {conference['动态出版标记']}")
                    st.write(f"截稿时间: {conference['截稿时间']} (距离截稿还有 {conference['剩余天数']} 天)")
                    st.write(f"匹配分析: {conference['论文研究方向匹配']}")
            else:
                st.write("没有找到完全匹配的会议，根据您的论文方向，推荐以下学科：")
                st.write("推荐学科: 电力系统工程, 控制理论, 计算机科学")
                st.write("可以参考这些方向的其他会议。")
        except Exception as e:
            st.error(f"加载会议文件时出错: {e}")
    else:
        st.error("请上传有效的会议文件")

# 主函数
def main():
    st.title("论文与会议匹配系统")
    
    # 上传会议文件区
    conference_file = upload_conference_file()
    
    # 上传论文文件区
    paper_file = upload_paper_file()
    
    # 如果论文文件上传了，进行进一步的分析与匹配
    if paper_file:
        st.write("正在进行论文分析...")
        time.sleep(1)  # 模拟分析时间
        perform_matching(conference_file, paper_file)  # 传递上传的会议文件进行匹配
    else:
        st.write("请先上传论文文件进行匹配。")

if __name__ == "__main__":
    main()
