from pymongo import MongoClient
from langchain_groq import ChatGroq
import random

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

def generate_feedback(performance_summary):
    feedback = ""
    for q_type, summary in performance_summary.items():
        total_attempted = summary["correct"] + summary["incorrect"]
        if total_attempted == 0:  # Prevent division by zero
            continue
        accuracy = (summary["correct"] / total_attempted) * 100

        if accuracy < 50:
            feedback += f"You are lagging in {q_type}. Consider revisiting the concepts and practicing more questions.\n"
        elif accuracy >= 50 and accuracy < 75:
            feedback += f"You are doing okay in {q_type}, but there's room for improvement. Keep practicing!\n"
        else:
            feedback += f"You are good at {q_type}. Great job! Keep up the good work!\n"
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

    print("Questions fetched from the database:")
    for q in selected_questions:
        print(q)

    if not selected_questions:
        print("No questions found in the database.")
        exit()

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

score = 0
total_questions = len(selected_questions)
incorrect_questions = []
# Initialize a dictionary to track correct and incorrect counts for each type
performance_summary = {q_type: {"correct": 0, "incorrect": 0} for q_type in question_types}

# Initialize a dictionary to store incorrect questions by type
incorrect_by_type = {q_type: [] for q_type in question_types}

# Loop through the question types and display them together
for question_type in question_types:
    print(f"\n[Type: {question_type.capitalize()} Questions]")

    for difficulty in difficulty_levels:
        # Get questions of the specific type and difficulty
        questions = list(collection.find({"type": question_type, "difficulty": difficulty}))
        random.shuffle(questions)  # Shuffle questions

        for question in questions[:5]:  # Limit to 5 questions
            print(f"[Difficulty: {difficulty.capitalize()}] {question.get('question', 'No question text found')}")

            options = question.get("options", [])
            for i, option in enumerate(options):
                print(f"{i + 1}. {option}")  # Display the options

            try:
                selected_option_index = int(input("Choose an option (1/2/3/4): ")) - 1
                if 0 <= selected_option_index < len(options):
                    user_answer = options[selected_option_index]  # Get the selected option text
                    if user_answer == question.get("correct_answer"):
                        print("Correct!")
                        score += 1  # Increment score for correct answer
                        performance_summary[question.get("type")]["correct"] += 1
                    else:
                        print("Incorrect! The correct answer is:", question.get("correct_answer"))
                        incorrect_questions.append(question)
                        performance_summary[question.get("type")]["incorrect"] += 1
                        incorrect_by_type[question.get("type")].append(question)  # Add to incorrect by type
                else:
                    print("Invalid option selected!")
            except ValueError:
                print("Please enter a valid number!")

print(f"\nThank you for taking the test! Your score is: {score}/{total_questions}")

# Generate feedback for each type based on incorrect answers
for q_type, incorrect_questions in incorrect_by_type.items():
    if incorrect_questions:
        print(f"\nFeedback for {q_type}:")
        llm_feedback = get_llm_feedback(incorrect_questions, performance_summary[q_type]["correct"], total_questions, q_type)
        print("\nSuggestions from the LLM:")
        print(llm_feedback)

# Generate overall feedback based on performance summary
overall_feedback = generate_feedback(performance_summary)
print("\nOverall Personalized Feedback:")
print(overall_feedback)

# Print performance summary
print("\nPerformance Summary:")
for q_type, summary in performance_summary.items():
    print(f"{q_type.capitalize()}: Correct: {summary['correct']}, Incorrect: {summary['incorrect']}")
