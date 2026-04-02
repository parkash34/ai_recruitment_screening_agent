import os
import requests
import json
import logging
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from fastapi import FastAPI
import time


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key: 
    raise ValueError("API Key is missing in .env file")

app = FastAPI()
sessions = {}
current_session = None

class JobRequirement(BaseModel):
    session_id : str
    job_title : str
    required_skills : list
    experience_years : int
    nice_to_have : list
    location : str
    language : str

    @validator("session_id")
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v
    
    @validator("job_title")
    def job_title_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Job title cannot be empty")
        return v
    
    @validator("required_skills")
    def skills_not_empty(cls, v):
        if not v:
            raise ValueError("Required skills cannot be empty")
        return v

class Applicant(BaseModel):
    session_id : str
    name : str
    experience_years : int
    skills : list
    education : str
    previous_roles : list
    location : str
    languages: list

    @validator("session_id")
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v
    
    @validator("skills")
    def skills_not_empty(cls, v):
        if not v:
            raise ValueError("Skills cannot be empty")
        return v
    
    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Applicant name cannot be empty")
        return v

class ScreenRequest(BaseModel):
    session_id : str

    @validator("session_id")
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v
    

def system_prompt(job=None, applicants=None):
    job_info = ""
    applicants_info = ""

    if job:
        job_info = f"""
    JOB REQUIREMENTS:
    - Job Title: {job["job_title"]}
    - Required Skills: {", ".join(job["required_skills"])}
    - Experience Required: {job["experience_years"]} years
    - Nice to Have: {", ".join(job["nice_to_have"])}
    - Location: {job["location"]}
    - Language: {job["language"]}
    """

    if applicants:
        applicants_info = "APPLICANT PROFILES:\n"
        for i, a in enumerate(applicants, 1):
            applicants_info += f"""
    Applicant {i}: {a["name"]}
    - Experience: {a["experience_years"]} years
    - Skills: {", ".join(a["skills"])}
    - Education: {a["education"]}
    - Previous Roles: {", ".join(a["previous_roles"])}
    - Location: {a["location"]}
    - Languages: {", ".join(a["languages"])}
    """

    return f"""
    You are an expert recruitment analyst for TalentAI.
    Your goal is to fairly and accurately screen applicants
    based on job requirements.

    {job_info}

    {applicants_info}

    SCORING RULES:
    Score each applicant out of 100 using these categories:

    1. Required Skills Match — 40 points
       - Full match: 40 points
       - Partial match: proportional points
       - No match: 0 points

    2. Experience Match — 30 points
       - Meets or exceeds requirement: 30 points
       - One year short: 20 points
       - Two years short: 10 points
       - Three or more years short: 0 points

    3. Location Match — 10 points
       - Same location: 10 points
       - Different location: 0 points

    4. Nice to Have Skills — 20 points
       - Each nice to have skill matched: proportional points

    ANTI-HALLUCINATION RULES:
    - Only evaluate based on the applicant data provided above
    - Never assume skills or experience not listed
    - Never make up qualifications
    - If information is missing mark it as unknown
    - Only use the job requirements provided above

    ANTI-DISCRIMINATION RULES:
    - Never comment on age, gender, religion, ethnicity or nationality
    - Only evaluate professional qualifications and skills
    - Be fair and objective in all evaluations
    - Base recommendations only on job relevant criteria

    Always respond in this exact JSON format:
    {{
        "applicant_name": "name here",
        "total_score": 0,
        "score_breakdown": {{
            "required_skills": 0,
            "experience": 0,
            "location": 0,
            "nice_to_have": 0
        }},
        "strengths": ["strength 1", "strength 2"],
        "weaknesses": ["weakness 1", "weakness 2"],
        "recommendation": "your recommendation here"
    }}

    Do not add any text outside the JSON.
    """

applicants_database = [
    {
        "name": "Ahmed Khan",
        "experience_years": 4,
        "skills": ["Python", "FastAPI", "SQL", "Docker", "REST APIs"],
        "education": "BS Computer Science",
        "previous_roles": ["Backend Developer", "Junior Python Developer"],
        "location": "Budapest, Hungary",
        "languages": ["English", "Urdu"]
    },
    {
        "name": "Sara Ali",
        "experience_years": 2,
        "skills": ["Python", "Django", "PostgreSQL", "Git"],
        "education": "BS Software Engineering",
        "previous_roles": ["Junior Developer", "Intern"],
        "location": "London, UK",
        "languages": ["English"]
    },
    {
        "name": "John Smith",
        "experience_years": 6,
        "skills": ["Python", "FastAPI", "Docker", "Kubernetes", "AWS", "REST APIs"],
        "education": "MS Computer Science",
        "previous_roles": ["Senior Backend Developer", "DevOps Engineer"],
        "location": "Budapest, Hungary",
        "languages": ["English", "German"]
    },
    {
        "name": "Maria Garcia",
        "experience_years": 3,
        "skills": ["JavaScript", "React", "Node.js", "MongoDB"],
        "education": "BS Computer Science",
        "previous_roles": ["Frontend Developer", "Full Stack Developer"],
        "location": "Madrid, Spain",
        "languages": ["English", "Spanish"]
    },
    {
        "name": "Li Wei",
        "experience_years": 5,
        "skills": ["Python", "Machine Learning", "FastAPI", "TensorFlow", "SQL"],
        "education": "MS Data Science",
        "previous_roles": ["ML Engineer", "Data Scientist", "Python Developer"],
        "location": "Budapest, Hungary",
        "languages": ["English", "Mandarin"]
    },
    {
        "name": "Fatima Malik",
        "experience_years": 1,
        "skills": ["Python", "Flask", "MySQL", "Git"],
        "education": "BS Information Technology",
        "previous_roles": ["Junior Python Developer"],
        "location": "Karachi, Pakistan",
        "languages": ["English", "Urdu"]
    }
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_applicant",
            "description": "Analyzes and scores a single applicant against job requirements. Returns detailed score breakdown with strengths and weaknesses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "Full name of the applicant being analyzed"
                    }
                },
                "required": ["applicant_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_candidates",
            "description": "Returns the top 3 highest scoring candidates after all applicants have been analyzed",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generates a detailed recruitment report for the top 3 candidates including scores, strengths, weaknesses and hiring recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string",
                        "description": "Title of the job position being filled"
                    }
                },
                "required": ["job_title"]
            }
        }
    }
]

def session_id_checker(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "job": None,
            "applicants": [],
            "analyzed" : [],
            "results" : None
        }

def create_error_response(code, message, details=None):
    return {
        "status" : "error",
        "code" : code,
        "message" : message,
        "details" : details
    }
def check_output_guardrail(response):
    text = " ".join([
        response.get("recommendation", ""),
        " ".join(response.get("strengths", [])),
        " ".join(response.get("weaknesses", []))
    ]).lower()
    forbidden = ["age", "gender", "religion", "ethnicity", "race", "nationality"]
    for word in forbidden:
        if word in text:
            return False, "Response contains discriminatory content"
    if not text.strip():
        return False, "Empty response"
    return True, None


def analyze_applicant(applicant_name):
    time.sleep(3)
    global current_session
    session = sessions[current_session]
    job = session["job"]

    applicant = None
    for a in session["applicants"]:
        if a["name"].lower() == applicant_name.lower():
            applicant = a
            break

    if not applicant:
        return f"Applicant {applicant_name} not found."

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "max_tokens": 500,
                "messages": [
                    {"role": "system", "content": system_prompt(job=job)},
                    {"role": "user", "content": f"Analyze and score this applicant: {json.dumps(applicant)}"}
                ]
            },
            timeout=15
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        result = json.loads(raw)

        is_valid, error = check_output_guardrail(result)
        if not is_valid:
            logger.warning(f"Guardrail triggered for {applicant_name}: {error}")
            return f"Analysis blocked for {applicant_name} due to security check."

        session["analyzed"] = session.get("analyzed", [])
        session["analyzed"].append(result)

        return json.dumps(result)

    except requests.exceptions.Timeout:
        logger.error(f"Timeout analyzing {applicant_name}")
        return f"Timeout analyzing {applicant_name}"
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON for {applicant_name}")
        return f"Invalid response for {applicant_name}"
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"Error analyzing {applicant_name}: {str(e)}"
    

def get_top_candidates():
    global current_session
    session = sessions[current_session]
    analyzed = session.get("analyzed", [])

    if not analyzed:
        return "No applicants have been analyzed yet."

    ranked = sorted(analyzed, key=lambda x: x["total_score"], reverse=True)

    top3 = ranked[:3]
    session["results"] = top3

    return json.dumps(top3)

def generate_report(job_title):
    global current_session
    session = sessions[current_session]
    top_applicants = session.get("results", [])

    if not top_applicants:
        return "No ranked candidates found. Please run screening first."

    report = f"RECRUITMENT REPORT — {job_title}\n"
    report += "=" * 50 + "\n\n"

    for i, applicant in enumerate(top_applicants, 1):
        report += f"RANK {i}: {applicant['applicant_name']}\n"
        report += f"Total Score: {applicant['total_score']}/100\n\n"

        report += "Score Breakdown:\n"
        breakdown = applicant["score_breakdown"]
        report += f"  Required Skills : {breakdown['required_skills']}/40\n"
        report += f"  Experience      : {breakdown['experience']}/30\n"
        report += f"  Location        : {breakdown['location']}/10\n"
        report += f"  Nice to Have    : {breakdown['nice_to_have']}/20\n\n"

        report += "Strengths:\n"
        for s in applicant["strengths"]:
            report += f"  + {s}\n"

        report += "\nWeaknesses:\n"
        for w in applicant["weaknesses"]:
            report += f"  - {w}\n"

        report += f"\nRecommendation: {applicant['recommendation']}\n"
        report += "-" * 50 + "\n\n"

    return report


@app.post("/setup-job")
def setup_job(job: JobRequirement):
    session_id = job.session_id
    session_id_checker(session_id)

    sessions[session_id]["job"] = {
        "job_title": job.job_title,
        "required_skills": job.required_skills,
        "experience_years": job.experience_years,
        "nice_to_have": job.nice_to_have,
        "location": job.location,
        "language": job.language
    }

    return {
        "status": "success",
        "message": f"Job '{job.job_title}' has been set up successfully.",
        "session_id": session_id
    }


@app.post("/add-applicant")
def add_applicant(applicant: Applicant):
    session_id = applicant.session_id
    session_id_checker(session_id)

    if sessions[session_id]["job"] is None:
        return create_error_response(
            code="JOB_NOT_SETUP",
            message="Please set up a job first before adding applicants.",
            details="Call POST /setup-job first."
        )

    applicant_data = applicant.dict()
    applicant_data.pop("session_id")

    sessions[session_id]["applicants"].append(applicant_data)
    count = len(sessions[session_id]["applicants"])

    return {
        "status": "success",
        "message": f"Applicant '{applicant.name}' added successfully.",
        "total_applicants": count
    }


@app.post("/screen")
def screen(request: ScreenRequest):
    global current_session
    session_id = request.session_id

    if session_id not in sessions:
        return create_error_response(
            code="SESSION_NOT_FOUND",
            message="Session not found.",
            details="Please set up a job first."
        )
    if sessions[session_id]["job"] is None:
        return create_error_response(
            code="JOB_NOT_SETUP",
            message="No job found for this session.",
            details="Call POST /setup-job first."
        )
    if len(sessions[session_id]["applicants"]) < 2:
        return create_error_response(
            code="NOT_ENOUGH_APPLICANTS",
            message="At least 2 applicants are required before screening.",
            details=f"Current applicants: {len(sessions[session_id]['applicants'])}"
        )

    current_session = session_id
    job = sessions[session_id]["job"]
    applicants = sessions[session_id]["applicants"]

    sessions[session_id]["analyzed"] = []
    sessions[session_id]["results"] = None

    screen_prompt = f"""
    You are screening applicants for the position of {job['job_title']}.

    Please do the following steps in order:
    1. Analyze each applicant one by one using analyze_applicant()
    2. After analyzing all applicants get top 3 using get_top_candidates()
    3. Generate final report using generate_report()

    Applicants to analyze: {[a['name'] for a in applicants]}

    Start analyzing now.
    """

    messages = [
        {"role": "system", "content": system_prompt(job=job, applicants=applicants)},
        {"role": "user", "content": screen_prompt}
    ]

    try:
        while True:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto"
                },
                timeout=60
            )
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]

            if not message.get("tool_calls"):
                break

            tool_call = message["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])

            if function_name == "analyze_applicant":
                result = analyze_applicant(**arguments)
            elif function_name == "get_top_candidates":
                result = get_top_candidates()
            elif function_name == "generate_report":
                result = generate_report(**arguments)
            else:
                result = "Function not found"

            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(result)
            })
            time.sleep(2)

        return {
            "status": "success",
            "report": message["content"]
        }

    except requests.exceptions.Timeout:
        logger.error("Screening timeout")
        return create_error_response(
            code="TIMEOUT",
            message="Screening timed out.",
            details="Please try again."
        )
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code}")
        return create_error_response(
            code="API_ERROR",
            message="AI service error.",
            details=f"Status: {e.response.status_code}"
        )
    
    except Exception as e:
        logger.error(f"Screening error: {str(e)}")
        return create_error_response(
            code="UNKNOWN_ERROR",
            message="Something went wrong during screening.",
            details=str(e)
        )
    