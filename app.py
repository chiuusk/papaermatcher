import streamlit as st
import pandas as pd
import re
from docx import Document
import fitz  # PyMuPDF
from googletrans import Translator

# --- Initialize translator ---
translator = Translator()

# --- Enhanced PDF parsing ---
def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        # Try to get title from table of contents first
        toc_title = ""
        if doc.get_toc():
            toc_title = doc.get_toc()[0][1]  # Get first level title
        
        # Main parsing strategy combining text and font info
        title_candidates = {}
        
        text = ""
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # Only process text blocks
                    for line in block["lines"]:
                        current_text = "".join([span["text"] for span in line["spans"]])
                        font_size = line["spans"][0]["size"] if line["spans"] else 12

                        # Rule: Large font likely indicates title                        
                        if font_size > 20 and len(current_text.strip()) > 8:
                            title_candidates[current_text.strip()] = font_size

                        text += current_text + "\n"
        
        # Return the largest font text as title candidate                
        if title_candidates:
            sorted_titles = sorted(title_candidates.items(), key=lambda x: x[1], reverse=True)            
            toc_title = sorted_titles[0][0]

        return toc_title, text.strip()
    
    except Exception as e:
        st.error(f"PDF parsing failed: {str(e)}")
        return "", ""

# --- Enhanced Word parsing --- 
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
        st.error(f"Word parsing failed: {str(e)}") 
        return "", "" 

# --- AI-enhanced title detection --- 
def extract_title(text, filename=""):    
    """Three-level strategy for intelligent title detection"""
     
    # Rule1: PDF/Word built-in title info (highest priority)
    if hasattr(text, 'title') and text.title:  
         return text.title

    # Rule2: First non-metadata text before abstract  
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

    # Rule3: Heuristic rules + ML fallback (simplified to rules)  
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

     return filename.split('.')[0] + " (auto-detected)"

def is_metadata(line):
    """Check if a line contains author/institution metadata"""
    patterns = [
         r'^\s*\S+@\S+\.\S+\s*$',          # Email format  
         r'^(\w\.\s+)*\w+(\s+et al\.)?$',   # Author names  
         r'^.*univ\w*,\s*\w+.*$'           # University info  
     ]
     
     return any(re.search(p, line, re.I) for p in patterns)

# --- Main Streamlit App ---  
def main():    
    st.set_page_config(layout="wide", page_title="Academic Paper Analyzer")  

    with st.sidebar.expander("⚙️Settings"):
         trans_lang=st.selectbox(
             "Translation language:", ["zh","en","ja","fr"],
             index=0)  

    uploaded_file=st.file_uploader(
         "📤Upload academic paper (PDF/Word)", 
         type=["pdf","docx"])  

    if uploaded_file:        
         with st.spinner(f"Analyzing {uploaded_file.name}..."):            
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
                 st.error(f"Analysis error:{str(e)}")                
                 st.stop()  

          # Display results          
          col1,col2=st.columns([1,2])  

          with col1:            
              st.subheader("🔍Metadata")            
              with st.expander("📝Title", expanded=True):                
                  st.write(f"**Original**:\n\n`{final_title}`")                
                  st.write(f"**Translated**:\n\n`{trans_title}`")  

              with st.expander("🔑Keywords"):                
                  st.write(f"**Original**:\n\n`{keywords}`")                
                  st.write(f"**Translated**:\n\n`{trans_kws}`")  

          with col2:            
              tab1,tab2=st.tabs(["📜Full Text","📊Analysis"])  

              with tab1:                
                  st.text_area(
                      label="Text preview (first 1000 chars):",                      
                      value=full_text[:1000]+"...",
                      height=300)  

              with tab2:                
                  analyze_button=st.button(
                      "✨Deep Analysis",                    
                      help="Use AI models to analyze methodology and innovations")  

if __name__=="__main__":    
      main()
