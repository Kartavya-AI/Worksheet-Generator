import os
from src.worksheet_generator.crew import get_worksheet_crew

def run():
    # Ensure the API key is set as an environment variable before running the script
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    # Define the inputs for the worksheet generation task
    inputs = {
        'board': 'CBSE',
        'class_level': '12',
        'stream': 'Science',
        'subject': 'Physics',
        'topic': 'Electromagnetic Induction'
    }
    
    # Kick off the crew with the defined inputs
    print("🚀 Kicking off the worksheet generation crew...")
    result = get_worksheet_crew.kickoff(inputs=inputs)
    
    print("\n✅ Worksheet Generated Successfully!")
    print(result)

if __name__ == "__main__":
    run()