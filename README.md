# 📝 AI-Powered Worksheet Generator
An intelligent worksheet generation system built with CrewAI and Google's Gemini API that creates customized practice worksheets for students across different school boards, classes, and subjects.

## 🌟 Features
- **Multi-Board Support**: Compatible with CBSE, ICSE, and State Board curricula
- **Grade-Specific Content**: Supports classes 1-12 (with stream-specific content for grades 11-12)
- **AI-Powered Generation**: Uses Google's Gemini model for intelligent question creation
- **Multiple Export Options**: Export worksheets as PDF or text files
- **User-Friendly Interface**: Clean Streamlit web interface
- **RESTful API**: FastAPI backend for programmatic access
- **Automatic Formatting**: Professional worksheet formatting with answer keys
- **Error Handling**: Robust error handling with retry mechanisms
- **Cloud Ready**: Docker containerized with GCP deployment support

## 🏗️ Architecture
The project follows a modular architecture using CrewAI framework:
- **Agent**: Worksheet Generator Agent responsible for creating educational content
- **Tool**: Custom WorksheetGeneratorTool that interfaces with Gemini API
- **Task**: Worksheet generation task with specific requirements
- **Crew**: Orchestrates the entire workflow
- **Interfaces**: Both Streamlit web app and FastAPI REST API

## 📋 Requirements
- Python 3.11+
- Google Gemini API Key
- Internet connection for API calls
- Docker (for containerization)
- Google Cloud SDK (for GCP deployment)

## 🚀 Installation

### Local Development

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

## 🐳 Docker Deployment

### Building the Docker Image

The application includes a production-ready Dockerfile optimized for deployment:

```bash
# Build the Docker image
docker build -t worksheet-generator .

# Run the container locally
docker run -p 8080:8080 -e GEMINI_API_KEY=your-api-key-here worksheet-generator
```

### Docker Configuration Details

The Dockerfile is configured with:
- **Base Image**: Python 3.11 slim-bullseye for optimal performance
- **Port**: Exposes port 8080 (standard for GCP Cloud Run)
- **WSGI Server**: Gunicorn with Uvicorn workers for FastAPI
- **Optimization**: Multi-layered build with caching for faster rebuilds
- **Security**: Non-root user execution and minimal attack surface

Key Dockerfile features:
```dockerfile
# Production-ready configuration
CMD ["gunicorn", "-w", "1", "--threads", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "api:app"]
```

## ☁️ Google Cloud Platform Deployment

### Prerequisites

1. **Install Google Cloud SDK**:
   ```bash
   # On macOS
   brew install google-cloud-sdk
   
   # On Ubuntu/Debian
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Authenticate and Setup**:
   ```bash
   gcloud auth login
   gcloud projects list
   gcloud config set project YOUR_PROJECT_ID
   ```

### Enable Required Services

```bash
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com
```

### Step-by-Step GCP Deployment

#### 1. Create Artifact Registry Repository

```bash
# Set variables (customize these)
$REPO_NAME = "worksheet-generator-repo"
$REGION = "us-central1"  # or your preferred region

# Create the repository
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$REGION `
    --description="Docker repository for AI Worksheet Generator"
```

#### 2. Build and Push Docker Image

```bash
# Get project ID and construct image tag
$PROJECT_ID = $(gcloud config get-value project)
$IMAGE_TAG = "$($REGION)-docker.pkg.dev/$($PROJECT_ID)/$($REPO_NAME)/worksheet-generator:latest"

# Build and push to registry
gcloud builds submit --tag $IMAGE_TAG
```

#### 3. Deploy to Cloud Run

```bash
# Set service name
$SERVICE_NAME = "worksheet-generator-api"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --port=8080 `
    --memory=2Gi `
    --cpu=1 `
    --max-instances=10 `
    --set-env-vars="GEMINI_API_KEY=your-gemini-api-key-here"
```

#### 4. Advanced Deployment Options

For production deployments, consider these additional configurations:

```bash
# Deploy with custom domain and HTTPS
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --port=8080 `
    --memory=4Gi `
    --cpu=2 `
    --max-instances=20 `
    --min-instances=1 `
    --concurrency=80 `
    --timeout=300 `
    --set-env-vars="GEMINI_API_KEY=your-gemini-api-key-here,ENVIRONMENT=production" `
    --labels="app=worksheet-generator,environment=production"
```

### Environment Variables for GCP

Set these environment variables in Cloud Run:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `ENVIRONMENT`: Set to "production" for production deployments

### Monitoring and Scaling

```bash
# View service details
gcloud run services describe $SERVICE_NAME --region=$REGION

# View logs
gcloud logs read --service=$SERVICE_NAME --region=$REGION

# Update traffic allocation
gcloud run services update-traffic $SERVICE_NAME --to-latest --region=$REGION
```

## 🖥️ Usage

### Web Interface (Streamlit - Local)

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Access the application**:
   - Open your browser and go to `http://localhost:8501`

### REST API (FastAPI)

#### Local Development
```bash
# Run FastAPI server locally
uvicorn api:app --reload --port 8000
```

#### API Endpoints
- **Health Check**: `GET /` - Returns service status
- **Generate Worksheet**: `POST /generate-worksheet/` - Creates a new worksheet

#### Example API Usage
```bash
# Test the API
curl -X POST "https://your-cloud-run-url/generate-worksheet/" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "Electromagnetic Induction",
       "grade": "12",
       "num_questions": 10
     }'
```

### Using the Web Interface

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
├── Dockerfile                               # Docker configuration
├── .dockerignore                           # Docker ignore rules
├── requirements.txt                        # Python dependencies
├── app.py                                  # Streamlit web application
├── api.py                                  # FastAPI REST API
├── pyproject.toml                         # Project configuration
├── GCP Deployment Commands.txt            # GCP deployment reference
├── src/
│   └── worksheet_generator/
│       ├── __init__.py
│       ├── main.py                        # CLI entry point
│       ├── crew.py                        # CrewAI crew configuration
│       ├── config/
│       │   ├── agents.yaml               # Agent configurations
│       │   └── tasks.yaml                # Task definitions
│       └── tools/
│           ├── __init__.py
│           └── custom_tool.py            # Worksheet generation tool
└── knowledge/
    └── user_preference.txt               # User preferences
```

## 🔧 Configuration

### Docker Environment Variables
- `GEMINI_API_KEY`: Required for API access
- `PYTHONDONTWRITEBYTECODE`: Prevents .pyc file creation
- `PYTHONUNBUFFERED`: Ensures immediate output

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

## 🚨 Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Ensure your Gemini API key is valid and has sufficient quota
   - Check that the key is properly set in environment variables

2. **Docker Build Issues**:
   - Ensure Docker is running and you have sufficient disk space
   - Check .dockerignore for any accidentally ignored files

3. **GCP Deployment Issues**:
   - Verify all required services are enabled
   - Check IAM permissions for your account
   - Ensure the image was pushed successfully to Artifact Registry

4. **Memory Issues**:
   - Increase Cloud Run memory allocation if needed
   - Monitor resource usage in GCP Console

### Performance Optimization
- Use Cloud Run's minimum instances for faster cold starts
- Implement request caching for frequently generated worksheets
- Monitor and adjust CPU/memory allocations based on usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Test Docker build: `docker build -t test-worksheet-generator .`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 🙏 Acknowledgments

- **CrewAI**: For the multi-agent framework
- **Google Gemini**: For the powerful language model
- **Streamlit**: For the beautiful web interface
- **FastAPI**: For the high-performance REST API
- **FPDF2**: For PDF generation capabilities
- **Google Cloud Platform**: For scalable cloud deployment

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the configuration files for customization options
- Check GCP documentation for deployment issues
