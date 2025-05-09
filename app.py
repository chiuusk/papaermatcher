import streamlit as st
import pandas as pd
import datetime
from sentence_transformers import SentenceTransformer, util

st.set_page_config(layout="wide")
st.title("📄 论文智能匹配推荐会议系统")

# 初始化模型和会话状态
model = SentenceTransformer('all-MiniLM-L6-v2')

if 'conference_df' not in st.session_state:
    st.session_state.conference_df = None

# 左：上传会议文件
with st.sidebar:
    st.subheader("📥 上传会议文件（仅需一次）")
    conference_file = st.file_uploader("会议文件（Excel）", type=["xlsx"], key="conf_file")
    if st.button("🗑 清除会议文件"):
        st.session_state.conference_df = None
        conference_file = None

# 主体：上传论文文件
col1, col2 = st.columns(2)
with col1:
    st.subheader("📁 上传论文文件（可多次匹配）")
    paper_file = st.file_uploader("论文文件（Excel）", type=["xlsx"], key="paper_file")
with col2:
    if st.button("🗑 清除论文文件"):
        paper_file = None

# 加载会议数据
if conference_file and st.session_state.conference_df is None:
    try:
        conf_df = pd.read_excel(conference_file)
        conf_df.columns = conf_df.columns.str.strip()
        # 字段标准化
        conf_df.rename(columns=lambda x: x.strip().replace("会议名称", "会议名").replace("截稿日期", "截稿时间").replace("细分方向", "细分关键词").replace("是否动态出版", "动态出版标记"), inplace=True)
        required_fields = {"会议系列名", "会议名", "会议方向", "会议主题方向", "细分关键词", "官网链接", "截稿时间", "动态出版标记"}
        if not required_fields.issubset(conf_df.columns):
            st.warning(f"❌ 缺少必要字段：{required_fields - set(conf_df.columns)}")
        else:
            # 只保留包含Symposium的会议（过滤掉主会）
            conf_df = conf_df[conf_df["会议名"].str.contains("Symposium", case=False, na=False)]
            st.session_state.conference_df = conf_df
            st.success("✅ 会议文件已成功读取并过滤")
    except Exception as e:
        st.error(f"❌ 加载会议文件失败：{e}")

# 如果论文上传了
if paper_file and st.session_state.conference_df is not None:
    try:
        paper_df = pd.read_excel(paper_file)
        st.info("🔍 正在分析论文研究方向...")
        progress = st.progress(0)

        # 论文信息提取
        paper_info_list = []
        for i, row in paper_df.iterrows():
            title = str(row.get("标题", "")).strip()
            abstract = str(row.get("摘要", "")).strip()
            keywords = str(row.get("关键词", "")).strip()
            full_text = " ".join([title, abstract, keywords])
            if not full_text.strip():
                continue
            embedding = model.encode(full_text, convert_to_tensor=True)
            paper_info_list.append({"text": full_text, "embedding": embedding, "title": title})

        if not paper_info_list:
            st.warning("⚠️ 论文文件中缺乏有效信息")
        else:
            progress.progress(25)
            st.success("✅ 论文研究方向识别中...")

            for paper in paper_info_list:
                text = paper["text"].lower()

                def match_weight(keywords):
                    return sum([text.count(k.lower()) for k in keywords])

                # 示例学科方向关键词
                subjects = {
                    "电力电子": ["PWM", "整流器", "控制策略", "PI 控制", "电压源"],
                    "人工智能": ["reinforcement learning", "深度学习", "智能控制", "神经网络"],
                    "控制工程": ["控制系统", "反馈", "PI", "建模", "调节器"]
                }

                subject_result = []
                total = 0
                for subject, keys in subjects.items():
                    w = match_weight(keys)
                    total += w
                    subject_result.append((subject, w))
                subject_result = [(k, round(v / total * 100, 1)) for k, v in subject_result if total > 0 and v > 0]

                st.markdown("### 📚 学科专业分析")
                st.markdown(f"**论文标题：** {paper['title']}")
                if subject_result:
                    for sub, p in subject_result:
                        explain = f"- 该论文涉及 **{sub}**，关键词匹配度为 {p}%。"
                        st.markdown(explain)
                else:
                    st.markdown("未能有效识别论文所属学科方向。")

                st.divider()
                st.markdown("### 🎯 匹配推荐会议（最多3个）")

                # 匹配会议
                conf_df = st.session_state.conference_df
                results = []
                for _, conf in conf_df.iterrows():
                    conf_text = f"{conf['会议系列名']} {conf['会议名']} {conf['会议方向']} {conf['会议主题方向']} {conf['细分关键词']}"
                    conf_embedding = model.encode(conf_text, convert_to_tensor=True)
                    score = util.cos_sim(paper["embedding"], conf_embedding).item()
                    results.append((score, conf))
                results = sorted(results, key=lambda x: x[0], reverse=True)[:3]

                for score, conf in results:
                    days_left = ""
                    if isinstance(conf['截稿时间'], datetime.datetime):
                        diff = (conf['截稿时间'] - datetime.datetime.now()).days
                        days_left = f"{diff} 天后截稿" if diff > 0 else "已过截稿"

                    st.markdown(f"#### 🏷️ {conf['会议系列名']} {conf['会议名']}")
                    st.markdown(f"- 📌 **主题方向：** {conf['会议主题方向']}")
                    st.markdown(f"- 🧩 **细分关键词：** {conf['细分关键词']}")
                    st.markdown(f"- 🌍 **会议官网：** [{conf['官网链接']}]({conf['官网链接']})")
                    st.markdown(f"- 🕒 **截稿时间：** {conf['截稿时间'].strftime('%Y-%m-%d')}（{days_left}）")
                    st.markdown(f"- 📦 **动态出版：** {'是' if conf['动态出版标记']=='是' else '否'}")
                    st.markdown(f"- ✅ **匹配说明：** 此会议主题与论文在 `{subject_result[0][0]}` 方向高度相关。关键词“{subject_result[0][0]}”在论文内容中频繁出现，匹配度高。")

                progress.progress(100)

    except Exception as e:
        st.error(f"❌ 处理论文文件失败：{e}")
elif not conference_file:
    st.warning("📄 请先上传会议文件")
