import streamlit as st
import pandas as pd
import datetime
import os
import tempfile

st.set_page_config(layout="wide")

# -------------------- 论文学科方向分析函数 --------------------
def analyze_paper_subject(title, abstract, keywords):
    subject_keywords = {
        "电力": ["电流", "电压", "控制策略", "逆变器", "PWM", "整流"],
        "计算机": ["深度学习", "强化学习", "神经网络", "卷积", "模型", "数据"],
        "自动化": ["控制系统", "PI 控制", "反馈", "仿真"],
        "机械": ["机器人", "伺服", "驱动", "传感"],
        "医学": ["临床", "病理", "生物", "医学图像"],
    }
    combined_text = f"{title} {abstract} {keywords}".lower()
    result = []
    for subject, keys in subject_keywords.items():
        count = sum(1 for k in keys if k.lower() in combined_text)
        if count > 0:
            result.append((subject, round(100 * count / len(keys), 1)))

    if not result:
        return "❌ 未能识别明确的学科方向", [], "未找到任何匹配关键词，可能标题或摘要与常见学科术语差异较大。"

    sorted_result = sorted(result, key=lambda x: -x[1])
    explanation = "\n".join([f"- **{s}**：匹配度 {p}%（因包含关键词）" for s, p in sorted_result])
    return "✅ 学科方向识别结果：", sorted_result, explanation


# -------------------- 展示会议匹配结果 --------------------
def match_paper_to_conference(paper_keywords, conf_df):
    matches = []
    for _, row in conf_df.iterrows():
        if pd.isna(row.get("会议名")) or "symposium" not in str(row["会议名"]).lower():
            continue
        conf_topic = str(row.get("主题方向", "")).lower()
        match_score = sum(1 for kw in paper_keywords if kw.lower() in conf_topic)
        if match_score > 0:
            matches.append((row, match_score))

    if not matches:
        return None

    sorted_matches = sorted(matches, key=lambda x: -x[1])
    return [row for row, _ in sorted_matches[:3]]


# -------------------- 解析上传论文文件内容 --------------------
def extract_paper_content(file):
    if file.type == "application/pdf":
        import fitz
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       "application/msword"]:
        from docx import Document
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        temp.write(file.read())
        temp.close()
        doc = Document(temp.name)
        text = "\n".join(p.text for p in doc.paragraphs)
        os.unlink(temp.name)
    else:
        return "", "", ""

    # 简化示例提取逻辑
    lines = text.strip().splitlines()
    title = lines[0] if lines else ""
    abstract = next((l for l in lines if "abstract" in l.lower()), "")
    keywords_line = next((l for l in lines if "keywords" in l.lower()), "")
    keywords = keywords_line.split(":")[-1] if ":" in keywords_line else keywords_line

    return title.strip(), abstract.strip(), keywords.strip()


# -------------------- 主逻辑 --------------------
def main():
    st.title("📄 论文会议匹配与学科方向分析工具")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📥 上传会议文件（Excel）")
        conf_file = st.file_uploader("上传包含会议信息的 Excel 文件", type=["xlsx"], key="conf", label_visibility="collapsed")
        if conf_file:
            st.success("会议文件已上传")

    with col2:
        st.subheader("📤 上传论文文件（PDF / Word）")
        paper_file = st.file_uploader("上传论文文件", type=["pdf", "doc", "docx"], key="paper", label_visibility="collapsed")
        if paper_file:
            st.success("论文文件已上传")

    # 分析结果区块
    if paper_file:
        st.markdown("---")
        st.subheader("📘 论文内容识别与学科方向分析")
        title, abstract, keywords = extract_paper_content(paper_file)
        st.markdown(f"**📌 标题：** {title}")
        st.markdown(f"**📌 摘要：** {abstract}")
        st.markdown(f"**📌 关键词：** {keywords}")

        heading, subject_result, explanation = analyze_paper_subject(title, abstract, keywords)
        st.markdown(f"### {heading}")
        st.markdown(explanation)

    # 匹配会议展示区块
    if paper_file and conf_file:
        st.markdown("---")
        st.subheader("📅 会议推荐匹配结果")
        conf_df = pd.read_excel(conf_file)

        matches = match_paper_to_conference(keywords.split(","), conf_df)

        if not matches:
            st.warning("⚠️ 未能找到完全匹配的会议，但你可以参考以上学科方向寻找接近领域的会议。")
        else:
            for row in matches:
                st.markdown(f"#### 📍 会议系列：{row.get('会议系列名')} / {row.get('会议名')}")
                st.markdown(f"- **主题方向：** {row.get('主题方向')}")
                st.markdown(f"- **细分关键词：** {row.get('细分关键词')}")
                st.markdown(f"- **截稿日期：** {row.get('截稿时间')}")
                st.markdown(f"- **动态出版标记：** {row.get('动态出版标记')}")
                link = row.get("官网链接")
                if isinstance(link, str) and link.startswith("http"):
                    st.markdown(f"- **会议官网：** [{link}]({link})")
                else:
                    st.markdown(f"- **会议官网：** {link}")
                st.markdown("---")


# -------------------- 启动入口 --------------------
if __name__ == "__main__":
    main()
