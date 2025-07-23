__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
sys.modules["sqlite3.dbapi2"] = sys.modules["pysqlite3.dbapi2"]

import streamlit as st
import os
import pandas as pd
from fpdf import FPDF
from src.worksheet_generator.crew import get_worksheet_crew
import io

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Worksheet Generator", page_icon="📝", layout="wide")

# --- Page Title and Description ---
st.title("📝 AI-Powered Worksheet Generator")
st.markdown("Generate practice worksheets for any subject and grade in seconds! Just enter your details below.")

# --- Sidebar for API Key and About section ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Google Gemini API Key:", type="password", key="api_key_input")
    
    st.header("About")
    st.info(
        "This is an AI-powered worksheet generator that uses CrewAI and Google's Gemini API "
        "to create practice questions for students based on their specific curriculum."
    )

# --- Main Content Area ---
st.header("Worksheet Details")

# Create columns for a cleaner layout
col1, col2 = st.columns(2)

with col1:
    board = st.selectbox("School Board", ["CBSE", "ICSE", "State Board"], key="board_select")
    class_level = st.number_input("Class", min_value=1, max_value=12, step=1, key="class_input")
    grade = st.selectbox("Grade", [
        "Excellent (90-100%)", 
        "Very Good (80-89%)", 
        "Good (70-79%)", 
        "Average (60-69%)", 
        "Below Average (50-59%)"
    ], key="grade_select")
    subject = st.text_input("Subject (e.g., Physics, History)", key="subject_input")

with col2:
    stream = ""
    if class_level >= 11:
        stream = st.selectbox("Stream", ["Science", "Commerce", "Arts/Humanities"], key="stream_select")
    topic = st.text_input("Chapter/Topic (e.g., Thermodynamics, The Mughal Empire)", key="topic_input")

# --- Generate Button and Logic ---
if st.button("✨ Generate Worksheet", use_container_width=True):
    # Input validation
    if not api_key:
        st.error("🚨 Please enter your Gemini API Key in the sidebar.")
    elif not all([board, class_level, subject, topic]):
        st.error("🚨 Please fill in all the required fields.")
    else:
        os.environ["GEMINI_API_KEY"] = api_key
        inputs = {
            'board': board,
            'class_level': str(class_level),
            'subject': subject,
            'topic': topic,
            'stream': stream if stream else "Not specified",
            'grade': grade
        }

        with st.spinner("🤖 The AI crew is assembling your worksheet... Please wait."):
            try:
                worksheet_crew = get_worksheet_crew() 
                result = worksheet_crew.kickoff(inputs=inputs)
                st.session_state.worksheet = str(result)
                st.success("✅ Worksheet generated successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.error(f"Debug - Inputs sent: {inputs}")

# --- Display Generated Worksheet and Export Options ---
if 'worksheet' in st.session_state and st.session_state.worksheet:
    st.header("Generated Worksheet")
    st.markdown(f"---")
    st.text_area("Worksheet Content", st.session_state.worksheet, height=400)
    st.markdown(f"---")

    st.header("Export Options")
    try:
        from fpdf import FPDF
        class WorksheetPDF(FPDF):
            def __init__(self):
                super().__init__()
                self.set_auto_page_break(auto=True, margin=15)
            
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'Practice Worksheet', 0, 1, 'C')
                self.ln(5)
            
            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
            
            def add_worksheet_content(self, subject, topic, class_level, board, stream, worksheet_text):
                # Title section
                self.set_font('Arial', 'B', 14)
                self.cell(0, 10, f"Subject: {subject}", 0, 1, 'L')
                self.cell(0, 10, f"Topic: {topic}", 0, 1, 'L')
                self.cell(0, 10, f"Class: {class_level} ({board})", 0, 1, 'L')
                if stream and stream != "Not specified":
                    self.cell(0, 10, f"Stream: {stream}", 0, 1, 'L')
                self.ln(10)
                self.set_font('Arial', '', 10)
                lines = worksheet_text.replace('\r\n', '\n').split('\n')
                
                for line in lines:
                    clean_line = self.clean_text(line)
                    
                    if not clean_line.strip():
                        self.ln(3)
                        continue
                    self.add_wrapped_text(clean_line)
            
            def clean_text(self, text):
                replacements = {
                    '"': '"', '"': '"', ''': "'", ''': "'",
                    '–': '-', '—': '-', '…': '...',
                    '°': ' degrees', '×': 'x', '÷': '/',
                    '≤': '<=', '≥': '>=', '≠': '!=',
                    'α': 'alpha', 'β': 'beta', 'γ': 'gamma',
                    'δ': 'delta', 'π': 'pi', 'θ': 'theta'
                }
                
                for old, new in replacements.items():
                    text = text.replace(old, new)
                
                # Keep only ASCII characters and basic symbols
                cleaned = ''.join(char if ord(char) < 128 else '?' for char in text)
                return cleaned
            
            def add_wrapped_text(self, text, max_width=180):
                if not text.strip():
                    return
                
                self.set_font('Arial', '', 10)
                if self.get_string_width(text) <= max_width:
                    self.cell(0, 6, text, 0, 1, 'L')
                    return
                
                words = text.split(' ')
                current_line = ''
                
                for word in words:
                    test_line = current_line + (' ' if current_line else '') + word
                    if self.get_string_width(test_line) <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            self.cell(0, 6, current_line, 0, 1, 'L')
                        current_line = word
                if current_line:
                    self.cell(0, 6, current_line, 0, 1, 'L')
        
        pdf = WorksheetPDF()
        pdf.add_page()
        pdf.add_worksheet_content(subject, topic, class_level, board, stream, st.session_state.worksheet)
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_subject.replace(' ','_')}_{safe_topic.replace(' ','_')}_worksheet.pdf"
        
        st.download_button(
            label="📄 Export as PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        st.info("💡 Tip: If you continue to have issues, try using the Text export option instead.")

    st.download_button(
        label="📝 Export as Text File",
        data=st.session_state.worksheet.encode('utf-8'),
        file_name=f"{subject.replace(' ','_')}_{topic.replace(' ','_')}_worksheet.txt",
        mime="text/plain",
        use_container_width=True
    )

# --- Footer ---
st.markdown("---")
st.markdown("**Note:** Make sure your Gemini API key has sufficient quota and permissions for generating content.")