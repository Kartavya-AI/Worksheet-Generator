# 📝 AI-Powered Worksheet Generator
An intelligent worksheet generation system built with CrewAI and Google's Gemini API that creates customized practice worksheets for students across different school boards, classes, and subjects.

## 🌟 Features
- **Multi-Board Support**: Compatible with CBSE, ICSE, and State Board curricula
- **Grade-Specific Content**: Supports classes 1-12 (with stream-specific content for grades 11-12)
- **AI-Powered Generation**: Uses Google's Gemini model for intelligent question creation
- **Multiple Export Options**: Export worksheets as PDF or text files
- **User-Friendly Interface**: Clean Streamlit web interface
- **Automatic Formatting**: Professional worksheet formatting with answer keys
- **Error Handling**: Robust error handling with retry mechanisms

## 🏗️ Architecture
The project follows a modular architecture using CrewAI framework:
- **Agent**: Worksheet Generator Agent responsible for creating educational content
- **Tool**: Custom WorksheetGeneratorTool that interfaces with Gemini API
- **Task**: Worksheet generation task with specific requirements
- **Crew**: Orchestrates the entire workflow

## 📋 Requirements
- Python 3.10+
- Google Gemini API Key
- Internet connection for API calls

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Kartavya-AI/Worksheet-Generator.git
   cd Worksheet-Generator
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

   Or install manually:
   ```bash
   pip install crewai[tools]>=0.134.0 streamlit>=1.28.0 pandas>=2.0.0 fpdf2>=2.7.0 pydantic>=2.0.0 tenacity>=8.0.0 pyyaml>=6.0 pysqlite3-binary==0.5.4
   ```

3. **Get your Gemini API Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
   - Keep it secure for later use

## 🖥️ Usage

### Web Interface (Recommended)

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Access the application**:
   - Open your browser and go to `http://localhost:8501`

3. **Generate a worksheet**:
   - Enter your Gemini API key in the sidebar
   - Fill in the worksheet details:
     - School Board (CBSE/ICSE/State Board)
     - Class (1-12)
     - Subject (e.g., Physics, History)
     - Topic/Chapter (e.g., Electromagnetic Induction)
     - Stream (for classes 11-12: Science/Commerce/Arts)
     - Grade level (performance expectation)
   - Click "Generate Worksheet"
   - Export as PDF or text file

### Command Line Interface

1. **Set environment variable**:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Run the crew**:
   ```bash
   python -m src.worksheet_generator.main
   ```

## 📂 Project Structure

```
worksheet-generator/
├── app.py                                    # Streamlit web application
├── pyproject.toml                           # Project configuration
├── src/
│   └── worksheet_generator/
│       ├── __init__.py
│       ├── main.py                          # CLI entry point
│       ├── crew.py                          # CrewAI crew configuration
│       ├── config/
│       │   ├── agents.yaml                  # Agent configurations
│       │   └── tasks.yaml                   # Task definitions
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py               # Worksheet generation tool
```


### Tool Configuration
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Handling**: Comprehensive error messages and fallbacks
- **Format Validation**: Ensures proper MCQ format with answer keys

## 🎯 Output Format
Generated worksheets include:

1. **Header Section**:
   - Subject name
   - Class and board information
   - Topic/chapter name
   - Stream (if applicable)

2. **Questions Section**:
   - 10 multiple-choice questions
   - 4 options each (A, B, C, D)
   - Clear numbering and formatting

3. **Answer Key**:
   - Separate section with correct answers
   - Easy reference for teachers/students



## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 🙏 Acknowledgments

- **CrewAI**: For the multi-agent framework
- **Google Gemini**: For the powerful language model
- **Streamlit**: For the beautiful web interface
- **FPDF2**: For PDF generation capabilities

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the configuration files for customization options
