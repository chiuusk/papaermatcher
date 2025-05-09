import streamlit as st
import pdfplumber
import docx
import pandas as pd
import datetime
import re
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util

# 下载必要的 NLTK 数据
nltk.download('punkt')

st.set_page_config(page_title="论文会议匹配助手", layout="wide")

st.title("🎯 论文自动匹配推荐会议")

model = SentenceTransformer('all-MiniLM-L6-v2')

# 提取文本函数
def extract_text(file):
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file.name.endswith(".docx"):
        doc =
