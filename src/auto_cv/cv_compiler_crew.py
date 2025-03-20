from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from auto_cv.tools.latex_compiler import LatexCompilerTool

from llm_foundation import logger

@CrewBase
class CVCompilerCrew():
    """CVCompiler crew"""

    agents_config = "config/cv_compilation_agents.yaml"
    tasks_config = "config/cv_compilation_tasks.yaml"

    @agent
    def latex_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['latex_compiler'], # type: ignore
            allow_code_execution=False,
            code_execution_mode='unsafe',
            allow_delegation=False,
            # memory=True,
            verbose=True,
        )

    @task
    def compile_doc_task(self) -> Task:
        return Task(
            config=self.tasks_config['compile_doc'], # type: ignore
            tools=[LatexCompilerTool(result_as_answer=True)],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CVCompiler crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,  # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
            verbose=True,
        )
