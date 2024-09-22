import streamlit as st
import PyPDF2 as pdf
import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Set the Google API key from Streamlit's secrets (stored in secrets.toml)
os.environ['GOOGLE_API_KEY'] = st.secrets['API_KEY']["GOOGLE_API_KEY"]
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure the Google Generative AI (Gemini) with the API key
genai.configure(api_key=GOOGLE_API_KEY)

# Function to interact with the Gemini AI model and get a response based on input text
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-1.0-pro')
    response = model.generate_content(input)
    return response.text

# Function to extract text content from an uploaded PDF file
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    # Iterate through each page in the PDF and extract the text
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract a brief description from the AI-generated response
def extract_description(response):
    # Split the response into lines and return the first two lines as a brief description
    lines = response.split("\n")
    description = " ".join(lines[:2])  # You can adjust the number of lines for a more detailed description
    return description

# Input prompt template for interacting with the AI model
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of the tech field, software engineering, data science,
data analysis, and big data engineering. Your task is to evaluate the resumes based
on the given job description. You must consider the job market is very competitive
and you should provide the best assistance for improving the resumes. Assign the
percentage matching based on JD and the missing keywords with high accuracy.
resume:{text}
description:{jd}

I want the response as per below structure
{{"JD Match": "%", "MissingKeywords": [], "Profile Summary": ""}}
"""

# Set the page configuration for the Streamlit app
st.set_page_config(page_title="Smart ATS for Resumes", layout="wide")

# App Title
st.title("Resume Checker using LLM")

# Text area for users to input a job description (JD)
jd = st.text_area("Paste the Job Description")

# File uploader for uploading multiple resume PDFs
uploaded_files = st.file_uploader("Upload Your Resumes", type="pdf", accept_multiple_files=True,
                                  help="Please upload the resumes in PDF format")

# Submit button to trigger the analysis
submit = st.button("Submit")

if submit:
    if uploaded_files and jd:
        ranked_resumes = []
        # Loop through each uploaded resume
        for uploaded_file in uploaded_files:
            text = input_pdf_text(uploaded_file)  # Extract text from the PDF
            input_text = input_prompt.format(text=text, jd=jd)  # Format the input for the AI model
            response = get_gemini_response(input_text)  # Get AI-generated feedback

            # Calculate a simple match percentage (based on text length comparison)
            if len(text) > 0:
                match_percentage = min(len(jd) / len(text) * 100, 100)
            else:
                match_percentage = 0

            # Extract a brief description from the AI response
            description = extract_description(response)

            # Store the results for each resume, including the AI response and description
            ranked_resumes.append({
                "name": uploaded_file.name,
                "match_percentage": match_percentage,
                "response": response,
                "description": description
            })

        # Sort the resumes by match percentage in descending order
        ranked_resumes = sorted(ranked_resumes, key=lambda x: x["match_percentage"], reverse=True)

        # Create a DataFrame for better display of ranked results
        df = pd.DataFrame(ranked_resumes)
        df["Rank"] = range(1, len(df) + 1)

        # Display the ranked resumes in a table format with resume name, rank, match percentage, and description
        st.table(df[["name", "Rank", "match_percentage", "description"]]
                 .rename(columns={"name": "RESUME_NAME", "match_percentage": "MATCH_PERCENTAGE", "description": "DESCRIPTION"}))
