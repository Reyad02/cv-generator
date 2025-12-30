from fastapi import FastAPI, UploadFile, File, HTTPException
from openai import OpenAI
from dotenv import dotenv_values
import re
import base64
import json

env_vars = dotenv_values(".env")
client = OpenAI(api_key=env_vars.get("OPENAI_API_KEY"))

app = FastAPI(title="User Details Extractor")

def extract_json(text: str):
    """
    Extracts JSON from a string (even if it has escape sequences) and returns a Python dict.
    """
    # Optional: match ```json blocks if they exist
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_text = match.group(1)
    else:
        json_text = text

    # Remove leading/trailing quotes if the entire JSON is in quotes
    if json_text.startswith('"') and json_text.endswith('"'):
        json_text = json_text[1:-1]

    # Replace escaped characters
    json_text = json_text.encode('utf-8').decode('unicode_escape')

    # Parse as JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        return None

@app.post("/extract_user_details")
async def extract_user_details(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")
    
    try:
        contents = await file.read()
        base64_file = base64.b64encode(contents).decode("utf-8")
        file_name = file.filename
        file_type = file.content_type
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File read/encode failed: {str(e)}")
    
    prompt = f"""
    You are a data extraction assistant. Extract user details from the uploaded resume.

    Return the result exactly in this JSON structure:
    {{
        "name": "string",
        "email": "string",
        "phone": "string",
        "work_exp": [
            {{
            "job_title": "string",
            "role": "string",
            "company_name": "string",
            "start_date": "string",
            "end_date": "string",
            "responsibility": "string"
            }}
        ],
        "location": "string",
        "photo": "base64-encoded string",
        "about_me": "string",
        "skills": ["string"],
        "educations": [
            {{
            "degree": "string",
            "institution": "string",
            "start_year": "string",
            "end_year": "string",
            "results": "string or null"
            }}
        ]
    }}
    """
    
    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=[
                    {"role": "system", "content": "Act as a Data Extraction Assistant."},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "filename": file_name,
                                "file_data": f"data:{file_type};base64,{base64_file}",
                            },
                            {
                                "type": "input_text",
                                "text": prompt,
                            },
                        ],
                    },
            ]
        )
        
        raw_report = response.output_text
        user_details = extract_json(raw_report)
        return user_details
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
