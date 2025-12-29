import json
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from dotenv import dotenv_values
from pydantic import BaseModel
import re

env_vars = dotenv_values(".env")
client = OpenAI(api_key=env_vars.get("OPENAI_API_KEY"))

app = FastAPI(title="Resume Builder AI")

system_prompt = """
You are a CV expert AI assistant. You should format the user details for CV. You should check any spelling mistakes, grammar mistakes etc. You also refine the about me and other description sections to make them more professional and impactful. For format the details use only '\n' for new lines not any bullets or dashes.
User details 
------------------
{details}

Required JSON format:
{{
  "refine_content": "refined user details with professional tone"
}}
"""

class WorkExperience(BaseModel):
    job_title: str
    role: str
    company_name: str
    start_date: str
    end_date: str
    responsibility: str
    
class Education(BaseModel):
    degree: str
    institution: str
    start_year: str
    end_year: str
    results: str | None


class UserDetailsRequest(BaseModel):
    name: str
    email: str
    phone: str
    work_exp: list[WorkExperience]
    location: str
    photo: str
    about_me: str
    skills: list[str]
    educations: list[Education]
 
@app.post("/refine_resume")
async def refine_resume(request: UserDetailsRequest):
    user_details_text = json.dumps(request.model_dump(), indent=2)
    prompt = system_prompt.format(details=user_details_text)
    
    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "You are a helpful assistant to refine user details for a CV."},
            {"role": "user", "content": prompt}
        ],
        reasoning={"effort": "low"},
    )
    
    try:
        # content = response.choices[0].message.content
        content = response.output_text
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()

        result = json.loads(content)
        
        return result
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=500, detail="Failed to parse AI response")