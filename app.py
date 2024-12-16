from flask import Flask, request, jsonify, render_template
import json
import threading
import pyttsx3
import speech_recognition as sr
from groq import Groq
import os
import pdfplumber
import subprocess
from pymongo import MongoClient
from langchain_groq import ChatGroq
import random

app = Flask(__name__)

# Initialize the Groq client using your API key
client = Groq(api_key="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")  # Replace with your actual API key

# Global variables for handling welcome message and question flow
question_index = 0
questions = []
welcome_message_shown = False  # Flag to track if welcome message was shown

# Load questions from JSON file at startup
def load_questions():
    global questions
    try:
        with open("interview_questions.json", "r") as file:
            questions = json.load(file)
    except Exception as e:
        print(f"Error loading questions: {e}")
        questions = []

load_questions()  # Load questions when the application starts

def run_groq_sync(prompt):
    """Run Groq API request and return the output."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred while contacting the Groq API: {e}")
        return "Feedback unavailable due to an error."

def speak_text(text):
    """Use text-to-speech to speak text."""
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Speed of voice
    engine.say(text)
    engine.runAndWait()

@app.route('/')
def main():
    return render_template('main1.html')

@app.route('/mock')
def moc():
    return render_template('moc1.html')

@app.route('/get_question', methods=['GET'])
def get_question():
    """Return a single question from the list if available."""
    global question_index, questions, welcome_message_shown

    # Show welcome message on first request
    if not welcome_message_shown:
        welcome_message = "Welcome to your mock interview session! Let's get started with the questions."
        threading.Thread(target=speak_text, args=(welcome_message,)).start()
        welcome_message_shown = True  # Set the flag to avoid repeating the message
        return jsonify({"question": welcome_message, "keywords": []})

    if question_index < len(questions):
        question_data = questions[question_index]
        question = question_data["question"]
        keywords = question_data["keywords"]

        # Start speaking the question in a separate thread
        threading.Thread(target=speak_text, args=(question,)).start()

        # Increment the question index to move to the next question for the following request
        question_index += 1
    else:
        question = "No more questions available."
        keywords = []
    return jsonify({"question": question, "keywords": keywords})

@app.route('/feedback', methods=['POST'])
def feedback():
    if request.method == 'POST':
        user_input = request.json.get('user_input')
        keywords = request.json.get('keywords', [])
        
        # Check for "exit" command to end the interview
        if "exit" in user_input.lower():
            exit_message = "All the best for your future interviews!"
            threading.Thread(target=speak_text, args=(exit_message,)).start()
            return jsonify({'feedback': exit_message})

        # Construct the prompt for Groq
        feedback_prompt = (
             f"Evaluate the following interview answer: '{user_input}'. "
             f"Please provide feedback on whether the answer is relevant to the question. "
             f"If relevant, give a positive comment about the answer. "
             f"If not relevant, suggest that the user include keywords like {', '.join(keywords)} in their response."
        )
        
        feedback = run_groq_sync(feedback_prompt)
        threading.Thread(target=speak_text, args=(feedback,)).start()
        return jsonify({'feedback': feedback})

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    
    return text if text.strip() else None

def get_resume_feedback(resume_text, job_description):
    prompt = f"""
    Analyze the following resume based on its suitability for the provided job description.
    
    Resume Text:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Provide specific, constructive feedback on areas of improvement for the resume to align better with the job description, including missing skills, experience alignment, and formatting suggestions if needed.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        feedback = chat_completion.choices[0].message.content
        feedback_lines = feedback.strip().splitlines()
        return feedback_lines
    except Exception as e:
        print(f"Error getting feedback from LLaMA: {e}")
        return ["Failed to get feedback. Please try again later."]

@app.route('/resume', methods=['GET', 'POST'])
def res():
    if request.method == 'POST':
        job_description = request.form.get('job_description')
        resume_file = request.files['resume']
        
        if resume_file and job_description:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(pdf_path)

            resume_text = extract_text_from_pdf(pdf_path)
            if resume_text:
                feedback_lines = get_resume_feedback(resume_text, job_description)
                return render_template('res.html', feedback_lines=feedback_lines)
            else:
                feedback_lines = ["Failed to process the resume. Please try again."]
                return render_template('res.html', feedback_lines=feedback_lines)
    
    return render_template('res.html')

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/run', methods=['POST'])
def run_code():
    code = request.json['code']
    user_input = request.json.get('input', '')

    try:
        process = subprocess.Popen(
            ['python', '-c', code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=user_input)
        return jsonify({'output': stdout + stderr})
    except Exception as e:
        return jsonify({'output': str(e)}), 400

@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    prompt = request.json['prompt']
    response = chat_with_groq(prompt)  # Call optimized Groq API function
    if response:
        return jsonify({'response': response})
    else:
        return jsonify({'response': 'AI encountered an error.'}), 500

def chat_with_groq(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": f"Please answer briefly: {prompt}"},
            ],
            model="llama3-8b-8192",
            temperature=0.2,
            max_tokens=50,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None
    
@app.route('/profile')
def profile():
    return render_template('profile.html')

def get_llm_feedback(incorrect_questions, score, total_questions, question_type):
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
        api_key='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'
    )

    prompt = f"""I have answered incorrectly {len(incorrect_questions)} questions out of {total_questions} for the question type '{question_type}'.
                My score is {score}. Here are the incorrect questions:\n"""

    for question in incorrect_questions:
        prompt += f"- {question.get('question')}, Correct Answer: {question.get('correct_answer')}\n"

    prompt += "Please provide suggestions on how I can improve in this topic."

    # Get response from the LLM
    response = llm.invoke(prompt)
    return response.content

# Function to generate feedback based on performance summary
def generate_feedback(performance_summary, incorrect_by_type):
    feedback = ""
    
    # Initialize the LLM (assuming it's already set up in your project)
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
        api_key='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'
    )
    
    for q_type, summary in performance_summary.items():
        total_attempted = summary["correct"] + summary["incorrect"]
        
        # Skip this question type if no questions were attempted
        if total_attempted == 0:
            continue
        
        accuracy = (summary["correct"] / total_attempted) * 100
        
        # Construct a dynamic prompt to the LLM based on the user's performance
        prompt = f"""I answered {total_attempted} questions from the '{q_type}' category. 
        I got {summary['correct']} correct and {summary['incorrect']} incorrect. My accuracy is {accuracy:.2f}%.
        Here are the incorrect questions and the correct answers:\n"""
        
        if incorrect_by_type[q_type]:
            for question in incorrect_by_type[q_type]:
                prompt += f"- Question: {question['question']}, Correct Answer: {question['correct_answer']}\n"

        # Add a request for improvement suggestions in the prompt
        prompt += "\nBased on my performance and the incorrect answers, please provide suggestions on how I can improve in this topic."
        
        # Send the dynamic prompt to the LLM and get the feedback
        llm_response = llm.invoke(prompt)
        feedback += f"\n===== Feedback for {q_type.capitalize()} =====\n"
        feedback += llm_response.content  # Append the LLM's response as feedback

    return feedback

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["QuatitativeAptitude"]  # Ensure the correct database name
    collection = db["aptitude_questions"]

    # Fetch questions and limit to 5 from each difficulty level for each type
    difficulty_levels = ["easy", "medium", "hard"]
    question_types = ["profit_loss", "time_and_work", "ratio_and_proportion", "mixtures_and_allegations"]
    
    selected_questions = []

    for q_type in question_types:
        for difficulty in difficulty_levels:
            questions = list(collection.find({"type": q_type, "difficulty": difficulty}))
            random.shuffle(questions)  # Shuffle to randomize selection
            selected_questions.extend(questions[:5])  # Take only 5 questions per type and difficulty

    if not selected_questions:
        print("No questions found in the database.")
        exit()

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

@app.route('/aptitude', methods=['GET', 'POST'])
def aptitude():
    score = 0
    total_questions = len(selected_questions)
    incorrect_questions = []
    
    # Initialize a dictionary to track correct and incorrect counts for each type
    performance_summary = {q_type: {"correct": 0, "incorrect": 0} for q_type in question_types}
    
    # Initialize a dictionary to store incorrect questions by type
    incorrect_by_type = {q_type: [] for q_type in question_types}
    
    if request.method == 'POST':
        for question in selected_questions:
            user_answer = request.form.get(str(question['_id']))
            if user_answer == question['correct_answer']:
                score += 1
                performance_summary[question['type']]['correct'] += 1
            else:
                incorrect_questions.append(question)
                performance_summary[question['type']]['incorrect'] += 1
                incorrect_by_type[question['type']].append(question)
        
        # Generate feedback for each type based on incorrect answers
        feedback = []
        for q_type, incorrect_questions in incorrect_by_type.items():
            if incorrect_questions:
                llm_feedback = get_llm_feedback(incorrect_questions, performance_summary[q_type]["correct"], total_questions, q_type)
                feedback.append(f"Feedback for {q_type.capitalize()}:\n{llm_feedback}")

        # Generate overall feedback based on performance summary
        overall_feedback = generate_feedback(performance_summary, incorrect_by_type)
        
        # Return feedback and score as JSON
        return jsonify({
            'feedback': overall_feedback.split('\n'),  # Split feedback into lines
            'score': score
        })

    return render_template('aptitude.html', questions=selected_questions)

if __name__ == "__main__":
    app.config['UPLOAD_FOLDER'] = 'uploads'
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5000)
