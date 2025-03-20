from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, FileWriterTool

from auto_cv.tools.date_time import DateTimeTool

@CrewBase
class CVAdaptorCrew():
    """CV Adaptor crew"""
    
    agents_config = "config/cv_adaptation_agents.yaml"
    tasks_config = "config/cv_adaptation_tasks.yaml"
    
    @agent
    def cv_adaptor(self) -> Agent:
        return Agent(
            config=self.agents_config['cv_adaptor'], # type: ignore
            allow_code_execution=False,
            code_execution_mode='unsafe',
            allow_delegation=False,
            memory=True,
            verbose=True,
        )    
    
    @task
    def read_doc_task(self) -> Task:
        return Task(
            config=self.tasks_config['read_doc'], # type: ignore
            tools=[FileReadTool()],
        )
    
    @task
    def latex_summarizer_task(self) -> Task:
        return Task(  # type: ignore
            config=self.tasks_config['latex_summarizer'], # type: ignore
            context=[self.read_doc_task()],
        )

    @task
    def write_doc_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_doc'], # type: ignore
            context=[self.latex_summarizer_task()],
            tools=[FileWriterTool(), DateTimeTool()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CV Adaptor crew"""
        return Crew(
            agents=self.agents, # type: ignore
            tasks=self.tasks, # type: ignore
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
