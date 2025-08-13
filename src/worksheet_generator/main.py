import os
from src.worksheet_generator.crew import get_worksheet_crew

def run():
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    inputs = {
        'board': 'CBSE',
        'class_level': '12',
        'stream': 'Science',
        'subject': 'Physics',
        'topic': 'Electromagnetic Induction'
    }
    print("🚀 Kicking off the worksheet generation crew...")
    result = get_worksheet_crew.kickoff(inputs=inputs)
    print("\n✅ Worksheet Generated Successfully!")
    print(result)

if __name__ == "__main__":
    run()