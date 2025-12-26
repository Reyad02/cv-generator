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
Yor are an CV expert AI assistant. You should format the user details for CV. You should check any spelling mistakes, grammar mistakes etc. You also refine the about me and other description sections to make them more professional and impactful. For format the details use only '\n' for new lines not any bullets or dashes.
User details 
------------------
{details}

Return ONLY this JSON structure:
{{
  "refine_content": "refined user details with professional tone",
}}
"""

class UserDetailsRequest(BaseModel):
    details: str
    
@app.post("/refine_resume")
async def refine_resume(request: UserDetailsRequest):
    prompt = system_prompt.format(details=request.details)
    
    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "You are a helpful assistant to refine user details for a CV."},
            {"role": "user", "content": prompt}
        ],
        reasoning={"effort": "low"},

        # max_tokens=1000,
        # temperature=0.7,
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