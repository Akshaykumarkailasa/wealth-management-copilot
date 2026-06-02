import os
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(
    api_key=API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

def ask_gemini(prompt):

    response = model.generate_content(
        prompt
    )

    return response.text