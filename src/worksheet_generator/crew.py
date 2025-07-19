import os
import yaml
from crewai import Agent, Task, Crew, Process, LLM
from src.worksheet_generator.tools.custom_tool import WorksheetGeneratorTool

def _load_config(file_path):
    """Helper function to load YAML configuration files."""
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_path = os.path.join(dir_path, file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {full_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")

def get_worksheet_crew():
    """
    Creates and returns a CrewAI crew instance on-demand.
    This function is called after the API key is set in the environment.
    """
    # Initialize the LLM using the crewai.LLM class as requested
    llm = LLM(
        model='gemini/gemini-2.5-pro',
        api_key=os.environ.get("GEMINI_API_KEY"),
        temperature=0.0
    )

    # Load agent and task configurations
    agents_config = _load_config('config/agents.yaml')
    tasks_config = _load_config('config/tasks.yaml')

    # Create the worksheet generator tool
    worksheet_tool = WorksheetGeneratorTool()

    # Create the Worksheet Generator Agent with the tool
    agent_cfg = agents_config['worksheet_generator_agent']
    worksheet_agent = Agent(
        role=agent_cfg['role'],
        goal=agent_cfg['goal'],
        backstory=agent_cfg['backstory'],
        llm=llm,
        tools=[worksheet_tool],  # Add the tool here
        verbose=True,
        allow_delegation=False
    )

    # Create the Worksheet Generation Task
    task_cfg = tasks_config['worksheet_generation_task']
    worksheet_task = Task(
        description=task_cfg['description'],
        expected_output=task_cfg['expected_output'],
        agent=worksheet_agent
    )

    # Assemble and return the Crew instance
    return Crew(
        agents=[worksheet_agent],
        tasks=[worksheet_task],
        process=Process.sequential,
        verbose=True
    )