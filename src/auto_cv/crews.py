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

@CrewBase
class CVCompilerCrew():
    """CVCompiler crew"""
    
    def __init__(self):
        super().__init__()
        cv_compiler_personas: Persona = Persona.from_yaml_file(Path(self.base_directory, "config", "CVCompilationCrewAI.yaml"))
        # self.doc_compiler_role: Role = cv_compiler_personas.get_role("latex_compiler")
        self.coder_role: Role = cv_compiler_personas.get_role("coder")

    @agent
    def coder(self) -> Agent:
        return self.coder_role.to_crewai_agent(verbose=True, allow_delegation=False, allow_code_execution=True, )

    @task
    def read_doc_task(self) -> Task | None:
        agent = self.coder()
        logger.info(f"Creating doc reader task for agent {agent}")
        return self.coder_role.get_crew_ai_task("read_doc", agent, output_json=LatexContent)

    @task
    def latex_summarizer_task(self) -> Task | None:
        agent = self.coder()
        logger.info(f"Creating a latex summarizer task for agent {agent}")
        return self.coder_role.get_crew_ai_task("latex_summarizer", 
                                                agent,
                                                context=[self.read_doc_task()],
                                                output_json=LatexContent)


    # @agent
    # def doc_compiler(self) -> Agent:
    #     return self.doc_compiler_role.to_crewai_agent(verbose=True, allow_delegation=False)

    # @task
    # def compile_doc_task(self) -> Task:
    #     agent = self.doc_compiler()
    #     logger.info(f"Creating doc compilation task for agent {agent}")
    #     return self.doc_compiler_role.get_crew_ai_task("compile_doc", agent, [LatexCompilerTool()])


    @crew
    def crew(self) -> Crew:
        """Creates the CVCompiler crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
