# AI-Powered Job Application Assistant

A sophisticated AI-powered application that helps users analyze job descriptions, tailor their resumes, and generate optimized answers for job application questions. 
The system uses Azure OpenAI for intelligent processing and Apify for job data scraping.

## 🚀 Features

- **Resume Analysis**: Analyzes resumes against job descriptions to provide match scores and improvement suggestions
- **Answer Generation**: Creates tailored responses to job application questions
- **Job Scraping**: Integrates with Apify to scrape job postings from Indeed
- **Profile Management**: Handles user profile creation and validation
- **FastAPI Backend**: Provides a robust REST API interface

## 🛠 Technology Stack

### Core Technologies
- **Python 3.8+**: Main programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Azure OpenAI**: AI/ML processing for resume analysis and answer generation
- **Apify**: Web scraping platform for job data collection

### Key Dependencies
- `azure-ai-inference`: Azure AI services integration
- `azure-core`: Azure core functionality
- `pydantic`: Data validation and settings management
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for API interactions

## 📁 Project Structure

```
job-assistant/
├── agents/                 # AI agent implementations
│   ├── answer_generator.py # Generates application answers
│   ├── fill_agent.py      # Manages user profile data
│   └── resume_agent.py    # Analyzes resumes against jobs
├── data_schema/           # JSON schemas for data validation
├── models/                # Pydantic models
│   └── user_profile.py    # Data models for user information
├── scraper/              # Job scraping functionality
│   └── apify_scrape.py   # Apify integration for Indeed scraping
├── utils/                # Utility functions
│   └── prompt_templates.py # LLM prompt templates
├── tests/                # Test suite
└── app.py               # FastAPI application entry point
```

## 💡 Key Components

### 1. Data Models (Pydantic)
The application uses Pydantic models for data validation and serialization:
- `UserProfile`: Contains personal info, work history, education, skills, and projects
- `JobSearchParams`: Job search criteria and parameters
- `ApplicationQuestion`: Structure for job application questions
- `GeneratedAnswer`: Format for AI-generated answers
- `ResumeAnalysisResult`: Analysis output format

### 2. AI Agents

#### Resume Analyzer
- Analyzes resumes against job descriptions
- Provides match scores and improvement suggestions
- Identifies key matches and gaps

#### Answer Generator
- Generates optimized answers for application questions
- Validates and improves responses
- Incorporates resume analysis for tailored answers

#### Profile Manager
- Handles user profile creation and validation
- Ensures data quality and completeness

### 3. Job Scraping (Apify Integration)
- Scrapes job postings from Indeed
- Supports both direct URL and search parameter-based scraping
- Configurable result limits and proxy settings

### 4. API Endpoints

The FastAPI application provides the following main endpoints:

```python
POST /analyze
- Analyzes resume against job requirements
- Takes UserProfile and JobSearchParams as input
- Returns ResumeAnalysisResult

POST /generate_answer
- Generates optimized application answers
- Takes UserProfile, JobSearchParams, and ApplicationQuestion
- Returns GeneratedAnswer
```

## ⚙️ Environment Setup

Required environment variables:
- `AZURE_KEY`: Azure OpenAI API key
- `AZURE_ENDPOINT`: Azure OpenAI endpoint
- `model_name`: Azure OpenAI model name
- `APIFY_TOKEN`: Apify API token

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file
4. Run the application:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🧪 Testing

Run the test suite to verify components:
```bash
python -m pytest tests/
```

The test suite includes:
- Environment setup validation
- Data loading verification
- Agent initialization testing
- Full workflow testing

## 📝 Usage Example

```python
# Example: Analyze a resume against a job posting
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/analyze",
        json={
            "user_profile": user_profile_data,
            "job_params": job_search_params
        }
    )
    analysis_result = response.json()
```

## 🔒 Security Notes

- API keys and sensitive data should be properly secured
- CORS settings should be configured for production
- Input validation is handled through Pydantic models
- Rate limiting should be implemented for production use

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
