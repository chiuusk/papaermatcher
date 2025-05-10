import streamlit as st
import pandas as pd
import re
from docx import Document
import fitz  # PyMuPDF
from googletrans import Translator

# Initialize translator
translator = Translator()

def extract_text_from_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        
        # Try to get title from table of contents first
        toc_title = ""
        if doc.get_toc():
            toc_title = doc.get_toc()[0][1]
        
        title_candidates = {}
        
        text = ""
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # Only process text blocks
                    for line in block["lines"]:
                        current_text = "".join([span["text"] for span in line["spans"]])
                        font_size = line["spans"][0]["size"] if line["spans"] else 12

                        if font_size > 20 and len(current_text.strip()) > 8:
                            title_candidates[current_text.strip()] = font_size

                        text += current_text + "\n"
        
        if title_candidates:
            sorted_titles = sorted(title_candidates.items(), key=lambda x: x[1], reverse=True)            
            toc_title = sorted_titles[0][0]

        return toc_title, text.strip()
    
    except Exception as e:
        st.error(f"PDF parsing failed: {str(e)}")
        return "", "" 

def extract_text_from_word(file):
    try:
        doc = Document(file)
        
        title_candidate = ""
        
		# Check each paragraph style to find the title paragraph	
		for para in doc.paragraphs:
			if para.style.name.lower() == 'title':
				title_candidate += para.text + "\n"
		
		full_text_list=[]
		for para in doc.paragraphs:
			full_text_list.append(para.text)

		full_text="\n".join(full_text_list)

		return title_candidate.strip(), full_text
	
	except Exception as e:
		st.error(f"Word parsing failed:{str(e)}")
		return "", "" 

def is_metadata(line):
	patterns=[
		r'^\s*\S+@\S+\.\S+\s*$',
		r'^(\w\.\s+)*\w+(\s+et al\.)?$',
		r'^.*univ\w*,\s*\w+.*$'
	]
	return any(re.search(p,line,re.I)for p in patterns)

def extract_title(text,filename=""):
	"""Three-level strategy to detect paper title"""
	
	# Rule1:Built-in title info(highest priority)
	if hasattr(text,'title')and text.title.strip():
		return text.title
	
	text=str(text)

	# Rule2:Lines before abstract section	
	abstract_positions=[m.start()for m in re.finditer(r'(?i)(\babstract\b|摘要)',text)]
	
	if abstract_positions and abstract_positions[0]>10:#Ensure there's content before abstract		
		pre_abstract=text[:abstract_positions[0]].strip()
		
		candidates=[line.strip()for line in pre_abstract.split('\n')
					if len(line.strip())>10 and not is_metadata(line)]
		
		if candidates:#Return the last non-empty candidate before abstract			
			return candidates[-1]

	# Rule3:Heuristic rules	
	lines=[line.strip()for line in text.split('\n')if len(line.strip())>5]
	
	for i,line in enumerate(lines):		
		if i>20:#Only check first20 lines to improve performance			
			break		
			
		if(len(line)>15 and not any(kw.lower()in line.lower()
			for kw in['author','university','@','doi','http'])
			and sum(c.isupper()for c in line)/len(line)<0.4			
			and not re.match(r'^\d{4}$|^pp\.|^vol\.|^no\.',line)):
				return re.sub(r'\s+',' ',line).strip()

	return filename.split('.')[0]+"(auto-detected)"

def clean_keywords(raw_str):
	"""Clean and format keyword strings"""
	return';'.join(set(
		kw.strip().capitalize()
		for kw in re.split(r'[;,\•\-–—]|\band\b',raw_str.replace('\n',''))
		if len(kw.strip())>2 and not kw.isdigit()
	))

def extract_keywords(text,max_keywords=8):
	"""Multi-strategy keyword extraction"""
	
	if not isinstance(text,str):
		return"(no keywords detected)"
	
	text=str(text).replace('\r','')
	
	# Strategy1:Explicit keyword sections	
	for pattern in[
		r'(?i)(keywords?\s*[:;\-—]\s*)(.*?)(?=\n[A-Z][a-z]{3,}|$)',
		r'(?i)(index terms?\s*[:;\-—]\s*)(.*?)(?=\n[A-Z][a-z]{3,}|$)',
		r'(关键[词字]\s*[:;\-—]\s*)(.*?)(?=\n[A-Za-z]{4,}|$)'
	]:
		match=re.search(pattern,text,re.DOTALL)
		if match and len(match.group(2).strip())>3:
			return clean_keywords(match.group(2))
	
	# Strategy2:Bullet-point lists near abstract	
	match=re.search(r'(?:abstract|摘要).*?([•▪■‣⦿➢➣➤⦾]\s*.+?)(?:\n{2}|\Z)',text,re.I|re.DOTALL)
	if match and len(match.group(1))>10:
		return clean_keywords(match.group(1))
	
	return"(no keywords detected)"

def main():
	st.set_page_config(layout="wide",page_title="Academic Paper Analyzer")

	st.sidebar.title("Settings")
	target_lang=st.sidebar.selectbox(
		"Translation Target",
		options=["zh","en","ja","fr"],
		index=0,
		help="Select target language for translations"
	)

	st.title("📄 Academic Paper Analyzer")

	uploaded_file=st.file_uploader(
		"Upload your research paper(PDF/DOCX)",
		type=["pdf","docx"],
		help="Supports both PDF and Word documents"
	)

	if uploaded_file is not None:

		st.subheader("Analysis Results")

		try:

			if uploaded_file.type=="application/pdf":
				pdf_title,pdf_content=extract_text_from_pdf(uploaded_file)

				st.success(f"Successfully parsed PDF:{uploaded_file.name}")
				
				final_title=extract_title(pdf_content or pdf_title,
										filename=uploaded_file.name)

				final_keywords=extract_keywords(pdf_content)

			elif uploaded_file.type=="application/vnd.openxmlformats-officedocument.wordprocessingml.document":
				word_title,word_content=extract_text_from_word(uploaded_file)

				st.success(f"Successfully parsed Word document:{uploaded_file.name}")

				final_title=extract_title(word_content or word_title,
										filename=uploaded_file.name)

				final_keywords=extract_keywords(word_content)

			else:

				st.error("Unsupported file format")

				return

			try:

				target_language={'zh':'Chinese','en':'English',
							   'ja':'Japanese','fr':'French'}[target_lang]

				st.markdown(f"""

				### Title Analysis

				- **Original Title**:`{final_title}`

				- **{target_language} Translation**:`{translator.translate(final_title,dest=target_lang).text}`

				### Keywords Analysis

				- **Original Keywords**:`{final_keywords}`

				- **{target_language} Translation**:`{translator.translate(final_keywords,dest=target_lang).text}`

				""")

			except Exception as e:

				st.warning(f"Translation service error:{str(e)}")

				st.markdown(f"""

				### Title Analysis

				`{final_title}`

				### Keywords Analysis

				`{final_keywords}`

				""")

			if uploaded_file.type=="application/pdf":

				st.download_button(

					label="Download Extracted Text",

					data=(final_title+"\n\n"+final_keywords+"\n\n"+pdf_content[:50000]),

					file_name=f"{uploaded_file.name}_extracted.txt",

					mime="text/plain"

				)

			else:

				st.download_button(

					label="Download Extracted Text",

					data=(final_title+"\n\n"+final_keywords+"\n\n"+word_content[:50000]),

					file_name=f"{uploaded_file.name}_extracted.txt",

					mime="text/plain"

				)

			st.success("Analysis completed successfully!")

			st.balloons()

		except Exception as e:

			st.error(f"A critical error occurred:{str(e)}")

if __name__=="__main__":
	
	try:

		main()

	except Exception as e:

		st.error(f"Application crashed:{str(e)}")

