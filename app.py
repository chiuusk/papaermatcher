import streamlit as st
import pandas as pd
import datetime
import io
import time
import re
from docx import Document
import fitz  # PyMuPDF，用于PDF解析
import requests
from collections import Counter

# 使用第三方API翻译（无需安装库）
def translate_text(text, target_lang="zh"):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        response = requests.get(url, params=params)
        result = response.json()
        return "".join([item[0] for item in result[0]])
    except:
        return "(翻译失败)"

# 提取 PDF 文本
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF解析失败: {e}")
        return ""

# 提取 Word 文本
def extract_text_from_word(file):
    try:
        document = Document(file)
        text = "\n".join([para.text for para in document.paragraphs])
        return text
    except Exception as e:
        st.error(f"Word解析失败: {e}")
        return ""

# 提取论文题目（更智能的识别）
def extract_title(text):
    lines = text.split('\n')
    title_candidates = []
    for i, line in enumerate(lines):
        cleaned_line = line.strip()
        if 15 < len(cleaned_line) < 250:  # 更严格的长度限制
            # 检查是否全部大写或首字母大写比例高
            upper_ratio = sum(1 for c in cleaned_line if c.isupper()) / len(cleaned_line)
            if upper_ratio > 0.6 or (cleaned_line and cleaned_line[0].isupper() and not cleaned_line[0].isdigit() and upper_ratio > 0.3):
                title_candidates.append((i, cleaned_line))
            # 查找可能包含标题的常见短语后的行
            elif i > 0 and re.search(r"(title|论文题目)[:：]", lines[i-1], re.IGNORECASE) and cleaned_line:
                title_candidates.append((i, cleaned_line))

    if title_candidates:
        # 返回第一个看起来最像标题且位置靠前的
        return min(title_candidates, key=lambda x: x[0])[1]
    elif lines:
        return lines[0].strip()
    else:
        return "无法识别题目"

# 提取关键词（更全面的识别）
def extract_keywords(text):
    keywords = set()
    patterns = [
        r"(?i)(Keywords|Index Terms)[:：]\s*([^\n]+)",
        r"(?i)关键词[:：]\s*([^\n]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            keyword_str = match.group(2).strip()
            # 按照逗号、分号或换行符分割关键词
            split_keywords = re.split(r'[;,，\n]\s*', keyword_str)
            keywords.update(split_keywords)
    return ", ".join(filter(None, keywords)) # 过滤空字符串并用逗号连接

# 学科方向分析（基于更全面的关键词）
def analyze_paper_subject(text):
    text = text.lower()
    subject_keywords = {
        "人力资源管理": ["人力资源管理", "员工招聘", "绩效考核", "薪酬福利", "人才发展", "劳动关系", "组织行为学", "human resource management", "employee recruitment", "performance appraisal", "compensation and benefits", "talent development", "labor relations", "organizational behavior"],
        "数字化转型": ["数字化", "数字化转型", "数字经济", "产业数字化", "企业数字化", "智能制造", "大数据分析", "云计算应用", "人工智能赋能", "物联网技术", "digitalization", "digital transformation", "digital economy", "industrial digitalization", "enterprise digitalization", "smart manufacturing", "big data analytics", "cloud computing applications", "ai empowerment", "iot technology"],
        "会计学": ["会计学", "财务会计", "管理会计", "审计", "税务", "会计准则", "财务报表分析", "成本会计", "内部控制", "会计信息系统", "accounting", "financial accounting", "management accounting", "auditing", "taxation", "accounting standards", "financial statement analysis", "cost accounting", "internal control", "accounting information systems"],
        "商业统计学": ["商业统计学", "统计分析", "数据分析", "回归分析", "时间序列分析", "多元统计分析", "市场调查", "预测方法", "商务统计", "statistical analysis", "data analysis", "regression analysis", "time series analysis", "multivariate statistical analysis", "market research", "forecasting methods", "business statistics"],
        "经济学": ["经济学", "宏观经济学", "微观经济学", "国际经济学", "发展经济学", "政治经济学", "计量经济学", "行为经济学", "产业经济学", "区域经济学", "economics", "macroeconomics", "microeconomics", "international economics", "development economics", "political economy", "econometrics", "behavioral economics", "industrial economics", "regional economics"],
        "管理学": ["管理学", "战略管理", "运营管理", "市场营销", "组织管理", "项目管理", "创新管理", "质量管理", "供应链管理", "人力资源管理", "management", "strategic management", "operations management", "marketing", "organizational management", "project management", "innovation management", "quality management", "supply chain management", "human resource management"],
        "经济与管理": ["经济与管理", "经济管理", "工商管理", "技术经济与管理", "农业经济管理", "旅游经济管理", "项目经济管理", "economic and management", "business administration", "technical economics and management", "agricultural economics and management", "tourism economics and management", "project economics and management"],
        "金融学": ["金融学", "货币银行学", "国际金融", "投资学", "公司金融", "金融市场", "金融工程", "风险管理", "保险学", "证券投资", "finance", "monetary economics", "international finance", "investment", "corporate finance", "financial markets", "financial engineering", "risk management", "insurance", "securities investment"],
        "管理科学与工程": ["管理科学与工程", "系统工程", "运筹学", "决策分析", "信息管理", "工业工程", "物流工程", "项目管理", "技术管理", "创新管理", "management science and engineering", "systems engineering", "operations research", "decision analysis", "information management", "industrial engineering", "logistics engineering", "project management", "technology management", "innovation management"],
        "会计与金融": ["会计与金融", "财务与金融", "会计金融", "金融会计", "accounting and finance", "finance and accounting", "financial accounting and finance"],
        "金融科技": ["金融科技", "FinTech", "区块链", "人工智能金融", "大数据金融", "移动支付", "数字货币", "智能投顾", "监管科技", "金融数字化", "blockchain", "ai finance", "big data finance", "mobile payment", "digital currency", "robo-advisor", "regtech", "digital finance"],
        "商业智能": ["商业智能", "BI", "数据可视化", "数据仓库", "OLAP", "商业分析", "决策支持系统", "数据挖掘", "预测分析", "绩效管理", "business intelligence", "data visualization", "data warehouse", "online analytical processing", "business analytics", "decision support systems", "data mining", "predictive analytics", "performance management"],
        "科技金融": ["科技金融", "技术驱动金融", "金融创新", "互联网金融", "数字普惠金融", "开放银行", "tech finance", "technology-driven finance", "financial innovation", "internet finance", "digital inclusive finance", "open banking"],
        "管理科学": ["管理科学", "决策科学", "行为科学", "组织科学", "公共管理", "教育管理", "医疗管理", "科学管理", "management science", "decision science", "behavioral science", "organizational science", "public administration", "educational management", "healthcare management", "scientific management"],
        "经济发展": ["经济发展", "可持续发展", "区域发展", "农村发展", "产业发展", "创新驱动发展", "绿色发展", "包容性发展", "高质量发展", "economic development", "sustainable development", "regional development", "rural development", "industrial development", "innovation-driven development", "green development", "inclusive development", "high-quality development"],
        "经济体系": ["经济体系", "市场经济体系", "社会主义市场经济", "宏观调控体系", "开放型经济体系", "现代化经济体系", "economic system", "market economy system", "socialist market economy", "macro-control system", "open economic system", "modern economic system"],
        "产业经济": ["产业经济", "工业经济", "农业经济", "服务业经济", "数字经济", "平台经济", "知识经济", "绿色经济", "创意经济", "产业结构", "industrial economics", "agricultural economics", "service industry economics", "digital economy", "platform economy", "knowledge economy", "green economy", "creative economy", "industrial structure"],
        "数据分析": ["数据分析", "数据挖掘", "统计分析", "商业分析", "文本分析", "社交网络分析", "用户行为分析", "预测分析", "数据可视化", "数据建模", "data analysis", "data mining", "statistical analysis", "business analytics", "text analysis", "social network analysis", "user behavior analysis", "predictive analytics", "data visualization", "data modeling"],
        "数据科学": ["数据科学", "数据科学家", "大数据分析", "机器学习", "人工智能", "数据工程", "数据管理", "数据伦理", "数据治理", "数据产品", "data science", "data scientist", "big data analytics", "machine learning", "artificial intelligence", "data engineering", "data management", "data ethics", "data governance", "data products"],
        "可视化": ["可视化", "数据可视化", "信息可视化", "科学可视化", "交互式可视化", "可视化分析", "可视化工具", "可视化设计", "可视化方法", "可视化技术", "visualization", "data visualization", "information visualization", "scientific visualization", "interactive visualization", "visual analytics", "visualization tools", "visualization design", "visualization methods", "visualization technology"],
        "机器学习": ["机器学习", "深度学习", "强化学习", "监督学习", "无监督学习", "模型训练", "特征工程", "神经网络", "卷积神经网络", "循环神经网络", "machine learning", "deep learning", "reinforcement learning", "supervised learning", "unsupervised learning", "model training", "feature engineering", "neural networks", "convolutional neural networks", "recurrent neural networks"],
        "石油工程": ["石油工程", "油气勘探", "油气钻井", "油气开采", "油藏工程", "石油地质", "油田化学", "采油工程", "天然气工程", "管道输送", "petroleum engineering", "oil and gas exploration", "oil and gas drilling", "oil and gas production", "reservoir engineering", "petroleum geology", "oilfield chemistry", "production engineering", "natural gas engineering", "pipeline transportation"],
        "计算机": ["计算机", "计算机科学", "计算机技术", "计算机应用", "计算机系统", "计算机网络", "计算机组成", "计算机体系结构", "计算机图形学", "计算机视觉", "computer", "computer science", "computer technology", "computer applications", "computer systems", "computer networks", "computer organization", "computer architecture", "computer graphics", "computer vision"],
        "自动化": ["自动化", "工业自动化", "智能自动化", "机器人技术", "控制系统", "过程控制", "运动控制", "自动化仪表", "自动化设备", "自动化生产线", "automation", "industrial automation", "intelligent automation", "robotics", "control systems", "process control", "motion control", "automation instruments", "automation equipment", "automated production lines"],
        "AI模型": ["AI模型", "人工智能模型", "机器学习模型", "深度学习模型", "自然语言处理模型", "计算机视觉模型", "生成对抗网络", "Transformer模型", "预训练模型", "模型部署", "ai model", "artificial intelligence model", "machine learning model", "deep learning model", "natural language processing model", "computer vision model", "generative adversarial network", "transformer model", "pre-trained model", "model deployment"],
        "人工智能": ["人工智能", "AI", "机器学习", "深度学习", "自然语言处理", "计算机视觉", "知识图谱", "智能Agent", "专家系统", "推理", "artificial intelligence", "machine learning", "deep learning", "natural language processing", "computer vision", "knowledge graph", "intelligent agent", "expert system", "reasoning"],
        "自然语言处理": ["自然语言处理", "NLP", "文本挖掘", "语义分析", "机器翻译", "情感分析", "问答系统", "信息抽取", "文本生成", "语言模型", "natural language processing", "text mining", "semantic analysis", "machine translation", "sentiment analysis", "question answering system", "information extraction", "text generation", "language model"],
        "计算机视觉": ["计算机视觉", "CV", "图像识别", "目标检测", "图像分割", "视频分析", "人脸识别", "三维视觉", "图像处理", "视觉SLAM", "computer vision", "image recognition", "object detection", "image segmentation", "video analysis", "face recognition", "3d vision", "image processing", "visual slam"],
        "推荐系统": ["推荐系统", "协同过滤", "内容推荐", "知识图谱推荐", "深度学习推荐", "个性化推荐", "推荐算法", "用户画像", "物品画像", "推荐解释", "recommender system", "collaborative filtering", "content-based recommendation", "knowledge graph recommendation", "deep learning recommendation", "personalized recommendation", "recommendation algorithm", "user profile", "item profile", "recommendation explanation"],
        "教育政策": ["教育政策"], "社会学": ["社会学"], "教育管理": ["教育管理"], "心理学": ["心理学"],
        "学科教育": ["学科教育", "初中", "高中", "高等教育"],
        "国际关系": ["国际关系", "政治学", "法", "国际组织"],
        "国际法": ["国际法", "劳动法", "刑法"],
        "生物学": ["生物学", "动物学", "昆虫学", "医学", "生态学", "微生物学"],
        "环境": ["环境", "生态", "地理学", "环境科学"],
        "传感器": ["传感器", "数据分析", "地球物理学"],
        "算法": ["算法", "数学", "物理", "建模", "控制"],
        "机械": ["机械", "电子", "电气", "材料"],
        "通信": ["通信", "物联网", "互联网", "无线", "光纤"],
        "语言": ["语言", "文学", "传媒", "艺术"]
    }
    subject_scores = Counter()
    for subject, keywords in subject_keywords.items():
        for keyword in keywords:
            subject_scores[subject] += text.lower().count(keyword.lower()) # 忽略大小写匹配

    total_score = sum(subject_scores.values())
    if total_score > 0:
        normalized_scores = {k: v / total_score * 100 for k, v in subject_scores.items()}
        return dict(normalized_scores.most_common())
    else:
        return {"无法识别学科方向": 100}

# 计算剩余天数
def calculate_days_left(cutoff_date):
    return (cutoff_date - datetime.datetime.now().date()).days

# 主函数
def main():
    st.set_page_config(layout="wide")
    st.title("论文与会议匹配系统")
    col1, col2 = st.columns(2)
    with col1:
        st.header("上传会议文件")
        conference_file = st.file_uploader("上传会议 Excel 文件", type=["xlsx"], key="conf")
    with col2:
        st.header("上传论文文件")
        paper_file = st.file_uploader("上传论文文件 (PDF 或 Word)", type=["pdf", "docx"], key="paper")

    # 如果上传了论文文件，立即分析
    if paper_file:
        st.markdown("## 📄 论文内容解析结果")
        file_text = ""
        if paper_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(paper_file)
        elif paper_file.name.endswith(".docx"):
            file_text = extract_text_from_word(paper_file)
        if not file_text.strip():
            st.error("未能成功提取论文内容")
            return
        # 提取题目与关键词
        title = extract_title(file_text)
        keywords = extract_keywords(file_text)
        # 翻译结果
        title_zh = translate_text
