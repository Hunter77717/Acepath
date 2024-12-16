from pymongo import MongoClient
from langchain_groq import ChatGroq


def get_llm_feedback(incorrect_questions, score, total_questions):
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
        api_key='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'
    )

    prompt = f"""I have answered incorrectly {len(incorrect_questions)} questions out of {total_questions}.
                 My score is {score}. Here are the incorrect questions:\n"""

    for question in incorrect_questions:
        prompt += f"- {question.get('question_text')}, Correct Answer: {question.get('correct_answer')}\n"

    prompt += "Please provide suggestions on how I can improve."

    # Get response from the LLM
    response = llm.invoke(prompt)  # Use the invoke method to get the response
    return response.content  # Return the content of the response

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Aptitude_"]
    collection = db["questions"]

    
    questions = list(collection.find())


    print("Questions fetched from the database:")
    for q in questions:
        print(q)

    if not questions:  
        print("No questions found in the database.")
        exit()  #

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()


score = 0
total_questions = len(questions)
incorrect_questions = []

for question in questions:
    print("\n" + question.get("question_text", "No question text found")) 

    if question.get("type") == "MCQ":
        options = [opt.get("option_text", "No option text found") for opt in question.get("options", [])]

        
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")


        try:
            selected_option_index = int(input("Choose an option (1/2/3/4): ")) - 1
            if 0 <= selected_option_index < len(options):
                if options[selected_option_index] == question.get("correct_answer"):
                    print("Correct!")
                    score += 1  # Increment score for correct answer
                else:
                    print("Incorrect! The correct answer is:", question.get("correct_answer"))
                    incorrect_questions.append(question)  
            else:
                print("Invalid option selected!")
        except ValueError:
            print("Please enter a valid number!")

    elif question.get("type") == "Short Answer":
        user_answer = input("Your answer: ")

        
        if user_answer.strip().lower() == question.get("correct_answer", "").strip().lower():
            print("Correct!")
            score += 1  
        else:
            print("Incorrect! The correct answer is:", question.get("correct_answer"))
            incorrect_questions.append(question) 


print(f"\nThank you for taking the test! Your score is: {score}/{total_questions}")


if incorrect_questions:
    
    print("\nIt seems you struggled with the following questions:")
    for question in incorrect_questions:
        print(f" - Question: {question.get('question_text')}, Correct Answer: {question.get('correct_answer')}")
    
    # Get suggestions from the LLM
    llm_feedback = get_llm_feedback(incorrect_questions, score, total_questions)
    print("\nSuggestions from the LLM:")
    print(llm_feedback)

print("\nConsider revisiting these topics for better understanding.")
