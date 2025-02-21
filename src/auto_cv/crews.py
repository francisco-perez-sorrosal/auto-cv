from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from llm_foundation import logger
from llm_foundation.agent_types import Persona, Role

from auto_cv.tools.job_scrapper import JobScrapperTool
from auto_cv.tools.latex_compiler import LatexCompilerTool
from auto_cv.data_models import JobDetails, LatexContent

@CrewBase
class JobDescriptionExtractorCrew():
    """JobDescriptionExtractor crew"""
    
    def __init__(self):
        super().__init__()
        job_description_personas: Persona = Persona.from_yaml_file(Path(self.base_directory, "config", "JobDescriptionCrewAI.yaml"))
        self.job_details_extractor_role: Role = job_description_personas.get_role("job_details_extractor")

    @agent
    def job_details_extractor(self) -> Agent:
        return self.job_details_extractor_role.to_crewai_agent(verbose=True, allow_delegation=False)

    @task
    def extract_job_details_task(self) -> Task:
        agent = self.job_details_extractor()
        logger.info(f"Creating job details task for agent {agent}")
        return self.job_details_extractor_role.get_crew_ai_task("extract_job_details", agent, [JobScrapperTool()])

    @task
    def extract_extra_fields_task(self) -> Task:
        agent = self.job_details_extractor()
        logger.info(f"Creating extra job description extractor task for agent {agent}")
        return self.job_details_extractor_role.get_crew_ai_task("extract_extra_fields_from_job_description", 
                                                                agent, 
                                                                context=[self.extract_job_details_task()], 
                                                                output_json=JobDetails)

    @task
    def format_job_description_task(self) -> Task:
        agent = self.job_details_extractor()
        logger.info(f"Creating job description format task for agent {agent}")
        return self.job_details_extractor_role.get_crew_ai_task("format_job_description", agent, context=[self.extract_job_details_task()], output_json=JobDetails)

    @crew
    def crew(self) -> Crew:
        """Creates the JobDescriptionExtractor crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
