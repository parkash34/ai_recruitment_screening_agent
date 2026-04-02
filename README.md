# TalentAI — AI Recruitment Screening Agent

An AI-powered recruitment screening agent built with FastAPI and Groq AI.
TalentAI automates the applicant screening process by analyzing candidates
against job requirements, scoring them across 4 categories and generating
a detailed recruitment report with top 3 candidates.

## Features

- Multi-step screening workflow — setup job, add applicants, screen
- AI powered scoring — 4 category evaluation out of 100 points
- Anti-hallucination — only evaluates provided applicant data
- Anti-discrimination guardrails — blocks biased evaluations
- Output validation — checks AI responses before returning
- Professional error handling with logging
- Multi-session support — multiple recruiters simultaneously
- Pydantic validation — invalid requests rejected automatically

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend web framework |
| Groq API | AI language model provider |
| LLaMA 3.3 70B | AI model |
| Pydantic | Data validation with custom validators |
| python-dotenv | Environment variable management |
| logging | Professional error logging |

## Project Structure
```
talentai/
│
├── .venv/               
├── main.py            
├── .env               
└── requirements.txt   
```

## Setup

1. Clone the repository
```
git clone https://github.com/yourusername/talentai
```

2. Create and activate virtual environment
```
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Create `.env` file and add your Groq API key
```
API_KEY=your_groq_api_key_here
```

5. Run the server
```
uvicorn main:app --reload
```

## API Endpoints

### POST /setup-job
Define the job requirements for a screening session.

**Request:**
```json
{
    "session_id": "recruiter_1",
    "job_title": "Python Backend Developer",
    "required_skills": ["Python", "FastAPI", "REST APIs"],
    "experience_years": 3,
    "nice_to_have": ["Docker", "SQL", "AWS"],
    "location": "Budapest, Hungary",
    "language": "English"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Job 'Python Backend Developer' has been set up successfully.",
    "session_id": "recruiter_1"
}
```

---

### POST /add-applicant
Add an applicant to the screening session.

**Request:**
```json
{
    "session_id": "recruiter_1",
    "name": "Ahmed Khan",
    "experience_years": 4,
    "skills": ["Python", "FastAPI", "SQL", "Docker"],
    "education": "BS Computer Science",
    "previous_roles": ["Backend Developer"],
    "location": "Budapest, Hungary",
    "languages": ["English", "Urdu"]
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Applicant 'Ahmed Khan' added successfully.",
    "total_applicants": 1
}
```

---

### POST /screen
Trigger the AI screening process and get the top 3 candidates.

**Request:**
```json
{
    "session_id": "recruiter_1"
}
```

**Response:**
```json
{
    "status": "success",
    "report": "RECRUITMENT REPORT — Python Backend Developer..."
}
```

## Scoring System

| Category | Points |
|---|---|
| Required Skills Match | 40 points |
| Experience Match | 30 points |
| Location Match | 10 points |
| Nice to Have Skills | 20 points |
| **Total** | **100 points** |

## Workflow
```
POST /setup-job
↓
POST /add-applicant (repeat for each applicant)
↓
POST /screen
↓
AI analyzes each applicant individually
↓
AI ranks top 3 by score
↓
AI generates detailed report
↓
Recruiter receives final recommendations
```

## Validation Rules

- Session ID cannot be empty
- Job title cannot be empty
- Required skills cannot be empty
- Applicant name cannot be empty
- Applicant skills cannot be empty
- Job must be set up before adding applicants
- Minimum 2 applicants required before screening

## Guardrails

- Anti-discrimination — forbidden words blocked from AI responses
- Anti-hallucination — AI only evaluates provided data
- Output validation — response structure verified before returning

## Environment Variables
```
API_KEY=your_groq_api_key_here
```

## Notes

- Never commit your .env file to GitHub
- Groq free tier has a daily token limit
- Session data resets when server restarts
- Minimum 2 applicants required per screening session

## 👤 Author

**Ohm Parkash** — [LinkedIn](https://www.linkedin.com/in/om-parkash34/) · [GitHub](https://github.com/parkash34)