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
        class UTF8FPDF(FPDF):
            def __init__(self):
                super().__init__()
                self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        
            def write_utf8_text(self, text):
                lines = text.split('\n')
                for line in lines:
                    if len(line) > 80:
                        words = line.split(' ')
                        current_line = ''
                        for word in words:
                            if len(current_line + word) < 80:
                                current_line += word + ' '
                            else:
                                if current_line:
                                    self.cell(0, 10, current_line.strip(), ln=True)
                                current_line = word + ' '
                        if current_line:
                            self.cell(0, 10, current_line.strip(), ln=True)
                    else:
                        self.cell(0, 10, line, ln=True)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"{subject} - {topic}", ln=True, align='C')
        pdf.cell(0, 10, f"Class {class_level} ({board})", ln=True, align='C')
        if stream:
            pdf.cell(0, 10, f"Stream: {stream}", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        
        worksheet_lines = st.session_state.worksheet.replace('\r\n', '\n').split('\n')
        
        for line in worksheet_lines:
            clean_line = line.encode('ascii', 'replace').decode('ascii')
            if len(clean_line) > 90:
                words = clean_line.split(' ')
                current_line = ''
                for word in words:
                    if len(current_line + word) < 85:
                        current_line += word + ' '
                    else:
                        if current_line.strip():
                            pdf.multi_cell(0, 5, current_line.strip())
                        current_line = word + ' '
                if current_line.strip():
                    pdf.multi_cell(0, 5, current_line.strip())
            else:
                pdf.multi_cell(0, 5, clean_line)
        
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
        st.info("💡 Tip: If you're getting encoding errors, try simplifying the worksheet content or removing special characters.")

    try:
        worksheet_lines = st.session_state.worksheet.split('\n')
        questions = []
        current_question = ""
        question_num = 1
        
        for line in worksheet_lines:
            line = line.strip()
            if not line:
                continue
            if (line.startswith(f"{question_num}.") or 
                line.startswith(f"Q{question_num}") or 
                line.startswith(f"Question {question_num}") or
                line.lower().startswith("q") and any(char.isdigit() for char in line[:5])):
                
                if current_question:
                    questions.append({
                        "Question_Number": question_num - 1,
                        "Question_Text": current_question.strip(),
                        "Board": board,
                        "Class": class_level,
                        "Stream": stream if stream else "N/A",
                        "Subject": subject,
                        "Topic": topic,
                        "Grade_Level": grade
                    })
                
                current_question = line
                question_num += 1
            else:
                current_question += " " + line
        
        if current_question:
            questions.append({
                "Question_Number": question_num - 1,
                "Question_Text": current_question.strip(),
                "Board": board,
                "Class": class_level,
                "Stream": stream if stream else "N/A",
                "Subject": subject,
                "Topic": topic,
                "Grade_Level": grade
            })
        
        if not questions:
            questions = [{
                "Question_Number": 1,
                "Question_Text": st.session_state.worksheet,
                "Board": board,
                "Class": class_level,
                "Stream": stream if stream else "N/A",
                "Subject": subject,
                "Topic": topic,
                "Grade_Level": grade
            }]
        
        df = pd.DataFrame(questions)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_data = csv_buffer.getvalue().encode('utf-8-sig')
        safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_subject.replace(' ','_')}_{safe_topic.replace(' ','_')}_worksheet.csv"

        st.download_button(
            label="📊 Export as CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
        with st.expander("📋 Preview CSV Structure"):
            st.dataframe(df.head(), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error creating CSV: {e}")
        st.info("💡 Tip: The CSV export attempts to parse individual questions. If parsing fails, the entire worksheet will be saved as one entry.")

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