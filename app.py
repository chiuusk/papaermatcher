import streamlit as st
import pandas as pd
import re
from docx import Document
import fitz  # PyMuPDF
from googletrans import Translator

# --- 初始化翻译器 ---
translator = Translator()

# --- PDF解析增强版 ---
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        # 优先尝试读取目录中的标题（如果存在）
        toc_title = ""
        if doc.get_toc():
            toc_title = doc.get_toc()[0][1]  # 取第一级目录
        
        # 正文解析策略：结合文本和字体信息
        title_candidates = {}
        
        text = ""
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # Only text blocks
                    for line in block["lines"]:
                        current_text = "".join([span["text"] for span in line["spans"]])
                        font_size = line["spans"][0]["size"] if line["spans"] else 12

                        # Rule: Large font (likely title)                        
                        if font_size > 20 and len(current_text.strip()) > 8:
                            title_candidates[current_text.strip()] = font_size

                        text += current_text + "\n"
        
        # Return the largest font text as title candidate                
        if title_candidates:
            sorted_titles = sorted(title_candidates.items(), key=lambda x: x[1], reverse=True)            
            toc_title = sorted_titles[0][0]

        return toc_title, text.strip()
    
    except Exception as e:
        st.error(f"PDF解析失败: {str(e)}")
        return "", ""

# --- Word解析增强版 --- 
def extract_text_from_word(file):
    try:
        doc = Document(file)
        
         # Check for built-in title style (MS Word specific)
         title_candidate = ""
         for para in doc.paragraphs:
             if para.style.name.lower() == 'title':
                 title_candidate = para.text.strip()
                 break
        
         full_text = "\n".join([para.text for para in doc.paragraphs])
         return title_candidate, full_text
    
     except Exception as e:
         st.error(f"Word解析失败: {str(e)}") 
         return "", "" 

# --- AI增强的标题识别 --- 
def extract_title(text, filename=""):    
     """智能识别标题的三层策略"""
     
     # Rule1: PDF/Word内置标题信息（最高优先级）
     if hasattr(text, 'title') and text.title:  
         return text.title

     # Rule2: Abstract前的第一段非元数据文本  
     abstract_positions = [
         m.start() for m in re.finditer(
             r'(?i)(\babstract\b|摘要|[\n\r]\s*abstract\s*[\n\r])', 
             str(text))
     ]
     
     if abstract_positions:
         pre_abstract = str(text)[:abstract_positions[0]]
         candidates = [
             line.strip() for line in pre_abstract.split('\n') 
             if len(line.strip()) > 10 and not is_metadata(line)
         ]
         if candidates:
             return candidates[-1]

     # Rule3: Heuristic rules + ML fallback (简化为规则)  
     lines = [line.strip() for line in str(text).split('\n') if line.strip()]
     
     metadata_keywords = [
         'author', 'received', 'accepted', 'doi', 'arxiv', '@', 'university',
         'email', 'proceedings', 'volume', 'issue', 'pp.'
     ]
     
     for line in lines:
         conditions = [
             len(line) > len(filename.replace('.pdf','').replace('.docx','')),
             not any(kw in line.lower() for kw in metadata_keywords),
             sum(c.isupper() for c in line)/len(line) <0.3,
             not line.startswith(('©','Copyright','http')),
             not re.match(r'^\W*\d{4}\W*$', line) # Exclude pure year like [2023]
         ]
         
         if all(conditions):
             return re.sub(r'[\r\n\t]+', ' ', line).strip()

     return filename.split('.')[0] + " (自动识别)"

def is_metadata(line):
     """判断是否为作者/机构等元数据行"""
     patterns = [
         r'^\s*\S+@\S+\.\S+\s*$',          # Email格式  
         r'^(\w\.\s+)*\w+(\s+et al\.)?$',   # Author names  
         r'^.*univ\w*,\s*\w+.*$'           # University info  
     ]
     
     return any(re.search(p, line, re.I) for p in patterns)

# --- AI增强的关键词提取 ---  
def extract_keywords(text):    
     """四层关键词抽取策略"""
     
     # Rule1: Explicit keyword sections (多语言支持)  
     keyword_labels_en = [
         r'keywords?\s*[:;\-\—]', 
         r'index terms\s*[:;\-\—]',
         r'key\s*words?\s*[:;\-\—]'
     ]
     
     keyword_labels_zh = [
         r'关键[词字]\s*[:;\-\—]',
         r'索引术语\s*[:;\-\—]'
     ]
     
     all_labels = keyword_labels_en + keyword_labels_zh
    
     for pattern in all_labels:
         match = re.search(
             pattern + r'\s*(.*?)(?:\n|$)', 
             str(text), re.I | re.DOTALL)
         
         if match and len(match.group(1).strip()) >3:
             keywords_str = clean_keywords(match.group(1))
             if keywords_str: 
                 return keywords_str

     # Rule2: Bullet-point lists near abstract  
     bullet_section = re.search(
         r'(?:abstract|摘要).*?([•▪■‣⦿➢➣➤⦾]\s*.+?)(?:\n{2}|\Z)', 
         str(text), re.I | re.DOTALL)  
     
     if bullet_section:  
         keywords_str = clean_keywords(bullet_section.group(1))
         if keywords_str: 
             return keywords_str

     # Rule3: High-frequency nouns (简化为规则实现)  
     nouns_found = re.findall(
         r'\b[A-Z][a-z]{3,}\b(?![\.\d])', str(text))  
     
     if nouns_found:  
         from collections import Counter  
         top_nouns = [w for w,cnt in Counter(nouns_found).most_common(5)]
         return "; ".join(top_nouns)

     # Rule4: Fallback to manual selection UI  
     st.warning("⚠️未能自动识别关键词")  
     manual_keywords = st.text_input(
         "请手动输入关键词（用分号分隔）:", 
         key="manual_kws")  
     
     return manual_keywords or "无关键词"

def clean_keywords(raw_str):    
     """清洗关键词字符串"""    
     cleaned_str=re.sub(
         r'[\r\n\t]+', ' ', raw_str).strip(';,. ')  
     
      # Split by common separators  
      separators_regex=r'[;,\•\▪\■‣⦿➢➣➤⦾]\s*|\band\b|\b与\b|\bor\b|\b或\b'
      split_kws=filter(None, [
          kw.strip().capitalize() 
          for kw in re.split(separators_regex, cleaned_str) 
          if len(kw.strip())>2 and not kw.isdigit()
      ])  
      
      return "; ".join(sorted(set(split_kws), key=len, reverse=True))

# --- Streamlit UI ---  
def main():    
      st.set_page_config(layout="wide", page_title="学术论文智能解析")  

      with st.sidebar.expander("⚙️高级设置"):
          trans_lang=st.selectbox(
              "翻译目标语言:", ["zh","en","ja","fr"],
              index=0)  

      uploaded_file=st.file_uploader(
          "📤上传学术论文(PDF/Word)", 
          type=["pdf","docx"])  

      if uploaded_file:        
          with st.spinner(f"正在解析 {uploaded_file.name}..."):            
              file_ext=uploaded_file.name.split('.')[-1].lower()  

              try:                
                  if file_ext=="pdf":
                      detected_title, full_text=extract_text_from_pdf(uploaded_file)                
                  else:                    
                      detected_title, full_text=extract_text_from_word(uploaded_file)  

                  final_title=extract_title(
                      full_text or detected_title,
                      filename=uploaded_file.name)  

                  keywords=extract_keywords(full_text)  

                  trans_title=translator.translate(
                      final_title, dest=trans_lang).text  

                  trans_kws=translator.translate(
                      keywords, dest=trans_lang).text  

              except Exception as e:                
                  st.error(f"解析错误:{str(e)}")                
                  st.stop()  

          # ---结果显示---          
          col1,col2=st.columns([1,2])  

          with col1:            
              st.subheader("🔍元数据提取")            
              with st.expander("📝标题分析", expanded=True):                
                  st.write(f"**原始标题**:\n\n`{final_title}`")                
                  st.write(f"**翻译结果**:\n\n`{trans_title}`")  

              with st.expander("🔑关键词分析"):                
                  st.write(f"**原始关键词**:\n\n`{keywords}`")                
                  st.write(f"**翻译结果**:\n\n`{trans_kws}`")  

          with col2:            
              tab1,tab2=st.tabs(["📜全文预览","📊智能分析"])  

              with tab1:                
                  st.text_area(
                      label="全文内容（前1000字符）:",                      
                      value=full_text[:1000]+"...",
                      height=300)  

              with tab2:                
                  analyze_button=st.button(
                      "✨执行深度分析",                    
                      help="使用AI模型分析研究方法和创新点")  

if __name__=="__main__":    
      main()
