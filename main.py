import os
import re
import requests
import json
import logging
import random
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from fastapi import FastAPI
from datetime import datetime


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
memory = {}

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
    language : str

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

class ScreenRequest:
    session_id : str

    @validator("session_id")
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Session ID is missing")
        return v

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


