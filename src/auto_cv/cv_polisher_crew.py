from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileWriterTool

from auto_cv.tools.date_time import DateTimeTool

@CrewBase
class CVPolisherCrew():
    """CV Polisher crew"""
    
    agents_config = "config/cv_polishing_agents.yaml"
    tasks_config = "config/cv_polishing_tasks.yaml"
    
    @agent
    def cv_polisher(self) -> Agent:
        return Agent(
            config=self.agents_config['cv_polisher'], # type: ignore
            allow_code_execution=False,
            code_execution_mode='unsafe',
            allow_delegation=False,
            memory=True,
            verbose=True,
        )    
    
    @task
    def polishing_task(self) -> Task:
        return Task(  # type: ignore
            config=self.tasks_config['polishing'], # type: ignore
        )

    @task
    def write_doc_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_doc'], # type: ignore
            context=[self.polishing_task()],
            tools=[FileWriterTool(), DateTimeTool()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CV Polisher crew"""
        return Crew(
            agents=self.agents, # type: ignore
            tasks=self.tasks, # type: ignore
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
