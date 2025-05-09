import streamlit as st
import pandas as pd
import datetime

# 设置页面标题和布局
st.set_page_config(page_title="论文与会议匹配系统", layout="wide")

# 上传会议文件区（缩小，放在左上角）
def upload_conference_file():
    with st.sidebar:
        st.subheader("上传会议文件")
        conference_file = st.file_uploader("选择会议文件", type=["xlsx", "csv"], label_visibility="collapsed")
        if conference_file:
            st.sidebar.write("会议文件已上传")
            # 这里可以处理会议文件数据
        else:
            st.sidebar.write("没有上传会议文件")
    return conference_file

# 上传论文文件区
def upload_paper_file():
    st.header("上传论文文件")
    st.write("请上传您的论文文件。支持格式：PDF 或 Word 文件。")
    paper_file = st.file_uploader("选择论文文件", type=["pdf", "docx"])
    return paper_file

# 论文的学科方向分析
def display_paper_analysis():
    st.subheader("论文研究方向分析")
    # 模拟论文分析结果，这里应根据实际论文内容提取分析
    st.write("该论文的研究方向分析：")
    st.write("1. 电力系统工程 60% - 论文涉及了PI控制策略及其在电力系统中的应用")
    st.write("2. 控制理论 30% - 论文讨论了基于强化学习的PI控制策略")
    st.write("3. 计算机科学 10% - 论文使用了计算机仿真来验证控制策略的有效性")

    # 根据学科分析的结果，推荐会议
    st.write("推荐的会议：")
    st.write("1. International Conference on Power Systems and Control (电力系统与控制国际会议) - 官网链接")
    st.write("2. International Conference on AI in Control Systems (人工智能在控制系统中的应用会议) - 官网链接")

# 计算剩余时间
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days if pd.notna(cutoff_date) else "未知"

# 显示进度条
def show_progress_bar():
    st.write("正在匹配论文与会议...")
    for i in range(100):
        st.progress(i + 1)
        time.sleep(0.05)

# 根据论文内容匹配会议
def perform_matching():
    # 论文研究方向分析
    paper_direction = "电力系统工程, 控制理论, 计算机科学"
    
    # 假设从上传的会议文件中获得匹配会议的逻辑
    conference_data = pd.read_excel('conference_file.xlsx')  # 假设上传了一个excel会议数据
    
    matching_conferences = []
    for index, row in conference_data.iterrows():
        # 简化：检查会议名是否包含符合条件的关键词
        if 'Symposium' not in row['会议名']:
            # 假设匹配的会议
            matching_conferences.append({
                "会议系列名与会议名": f"{row['会议系列名']} - {row['会议名']}",
                "官网链接": row['官网链接'],
                "动态出版标记": row['动态出版标记'],
                "截稿时间": row['截稿时间'],
                "剩余天数": calculate_days_left(row['截稿时间']),
                "论文研究方向匹配": f"与{row['会议主题方向']}匹配"
            })
    
    # 如果有匹配的会议，展示推荐的会议
    if matching_conferences:
        for conference in matching_conferences:
            st.write(f"**会议推荐：{conference['会议系列名与会议名']}**")
            st.write(f"官网链接: {conference['官网链接']}")
            st.write(f"动态出版标记: {conference['动态出版标记']}")
            st.write(f"截稿时间: {conference['截稿时间']} (距离截稿还有 {conference['剩余天数']} 天)")
            st.write(f"匹配分析: {conference['论文研究方向匹配']}")
    else:
        st.write("没有找到完全匹配的会议，根据您的论文方向，推荐以下学科：")
        st.write(f"推荐学科: {paper_direction}")
        st.write("可以参考这些方向的其他会议。")

# 主功能区
def main():
    st.title("论文与会议匹配系统")
    
    # 上传会议文件区
    conference_file = upload_conference_file()
    
    # 上传论文文件区
    paper_file = upload_paper_file()
    
    # 如果论文文件上传了，进行进一步的分析与匹配
    if paper_file:
        display_paper_analysis()
        perform_matching()
    else:
        st.write("请先上传论文文件进行匹配。")

# 执行主功能
if __name__ == "__main__":
    main()
