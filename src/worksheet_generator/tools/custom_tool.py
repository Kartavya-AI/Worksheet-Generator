from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class WorksheetGeneratorSchema(BaseModel):
    """Input schema for the Worksheet Generator Tool."""
    board: str = Field(..., description="The school board (e.g., CBSE, ICSE).")
    class_level: str = Field(..., description="The class level (e.g., 10, 12).")
    subject: str = Field(..., description="The subject for the worksheet.")
    topic: str = Field(..., description="The specific chapter or topic.")
    stream: Optional[str] = Field(None, description="The stream for classes 11th and 12th (e.g., Science).")

class WorksheetGeneratorTool(BaseTool):
    name: str = "Worksheet Generator"
    description: str = "Generates a practice worksheet of 10 MCQs with four options each based on user-provided details."
    args_schema: Type[BaseModel] = WorksheetGeneratorSchema

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def _run(self, board: str, class_level: str, subject: str, topic: str, stream: Optional[str] = None) -> str:
        """
        Uses the agent's configured LLM to generate a worksheet of 10 MCQs.
        This tool relies on the LLM provided by the agent executing it.
        """
        # Construct the detailed prompt for the agent's LLM
        prompt = (
            f"Generate a practice worksheet of 10 multiple-choice questions with four options each for the following:\n"
            f"School Board: {board}\n"
            f"Class: {class_level}\n"
        )
        if stream:
            prompt += f"Stream: {stream}\n"
        prompt += (
            f"Subject: {subject}\n"
            f"Topic/Chapter: {topic}\n\n"
            f"Please provide the questions in a clear, numbered list format with the options labeled A, B, C, and D. "
            f"Also, provide a separate answer key at the end."
        )

        try:
            # Use the agent's LLM to generate the content.
            # CrewAI makes the agent's LLM available to the tool at runtime.
            response = self.agent.llm.invoke(prompt)
            
            # Extract text from the response object
            response_text = str(response.content if hasattr(response, 'content') else response)

            if not response_text.strip():
                 return "Error: The model returned an empty response. Please try again with a more specific topic."
            return response_text
        except Exception as e:
            # This will be caught by tenacity, which will retry. If it fails after all retries,
            # this message will be returned.
            return f"An error occurred while generating the worksheet after multiple retries: {e}"