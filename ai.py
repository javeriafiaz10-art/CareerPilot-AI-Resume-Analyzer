
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

# Connect to Groq API
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def analyze_resume(resume_text, user_goal):

    prompt = f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user's career goal.

User goal: "{user_goal}"

STRICT RULES:
- Extract only relevant skills for this goal.
- Remove irrelevant tools.
- Identify real skill gaps.
- Generate roadmap only for missing skills.
- Make output different based on the career goal.

Return only valid JSON.

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict hiring manager. Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON
        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("AI did not return valid JSON.")

        return json.loads(content[start:end + 1])

    except Exception as e:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }
