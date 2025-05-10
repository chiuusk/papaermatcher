import streamlit as st
import pandas as pd
import datetime
import os
import tempfile

# 用于展示分析进度
def show_progress_bar():
    progress_bar = st.progress(0)
    for percent_complete in range(1, 101):
        progress_bar.progress(percent_complete)

# 学科方向分析（简化示例）
def analyze_paper_subject(title, abstract, keywords):
    subject_keywords = {
        "电力": ["电流", "电压", "控制策略", "逆变器", "PWM", "整流"],
        "计算机": ["深度学习", "强化学习", "神经网络", "卷积", "模型", "数据"],
        "自动化": ["控制系统", "PI 控制", "反馈", "仿真"],
    }
    combined_text = f"{title} {abstract} {keywords}".lower()
    result = []
    for subject, keys in subject_keywords.items():
        count = sum(1 for k in keys if k in combined_text)
        if count > 0:
            result.append((subject, round(100 * count / len(keys), 1)))

    if not result:
        return "❌ 未能识别明确的学科方向", []
    sorted_result = sorted(result, key=lambda x: -x[1])
    explanation = "\n".join([f"- **{s}**：匹配度 {p}%（因包含关键词）" for s, p in sorted_result])
    return "✅ 学科方向识别结果：", sorted_result, explanation

# UI 设置
st.set_page_config(layout="wide")
st.title("📄 论文匹配会议推荐工具")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📁 上传会议文件（Excel）")
    conference_file = st.file_uploader("上传会议文件", type=["xlsx"])
    if conference_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(conference_file.read())
            conference_path = tmp.name
        conference_data = pd.read_excel(conference_path)

with col2:
    st.subheader("📄 上传论文文件（PDF或Word）")
    paper_file = st.file_uploader("上传论文文件", type=["pdf", "docx"])
    if paper_file:
        # 假设这里你有自己的论文解析函数 parse_paper()
        title = "Reinforcement Learning-Based PI Control Strategy for Single-Phase Voltage Source PWM Rectifier"
        abstract = "This paper proposes a PI control strategy based on reinforcement learning for a PWM rectifier..."
        keywords = "Reinforcement Learning, PI Control, PWM Rectifier"

        st.markdown("### 🧠 论文学科方向分析")
        heading, result, explanation = analyze_paper_subject(title, abstract, keywords)
        st.info(heading)
        st.markdown(explanation)

        if conference_file:
            st.markdown("### 🔍 匹配推荐会议")
            show_progress_bar()

            recommendations = []
            for idx, row in conference_data.iterrows():
                if "Symposium" not in row.get("会议名", ""):
                    continue  # 跳过主会
                if any(s in row.get("会议主题方向", "") for s, _ in result):
                    days_left = "未知"
                    if pd.notna(row.get("截稿时间")):
                        try:
                            days_left = (row["截稿时间"] - datetime.datetime.now().date()).days
                        except:
                            days_left = "未知"

                    recommendations.append({
                        "会议全称": f"{row.get('会议系列名', '')} - {row.get('会议名', '')}",
                        "主题方向": row.get("会议主题方向", ""),
                        "细分关键词": row.get("细分关键词", ""),
                        "动态出版标记": row.get("动态出版标记", ""),
                        "截稿时间": str(row.get("截稿时间", "")),
                        "距离截稿还有": f"{days_left} 天" if isinstance(days_left, int) else "未知",
                        "会议官网": row.get("官网链接", "#")
                    })

            if recommendations:
                for conf in recommendations[:3]:
                    st.markdown(f"""
                    ---
                    #### 🏛 {conf['会议全称']}
                    - **主题方向**：{conf['主题方向']}
                    - **细分关键词**：{conf['细分关键词']}
                    - **动态出版标记**：{conf['动态出版标记']}
                    - **截稿时间**：{conf['截稿时间']} （距离截稿还有：{conf['距离截稿还有']}）
                    - **会议官网**：[点击访问]({conf['会议官网']}) （可复制）
                    """)
            else:
                st.warning("⚠️ 未找到完全匹配的会议，以下为相关学科方向下的模糊推荐（功能待扩展）")

# 拖动区域样式扩展（拖动区域变大）
st.markdown("""
    <style>
        section[data-testid="stFileUploader"] {
            border: 2px dashed #ccc;
            padding: 30px;
            height: 200px;
        }
    </style>
""", unsafe_allow_html=True)
