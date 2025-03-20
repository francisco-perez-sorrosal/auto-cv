import json
import json
import os
from pathlib import Path
from crewai.crew import CrewOutput
from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger

from shiny.express import ui

from auto_cv.cv_adaptor_crew import CVAdaptorCrew
from auto_cv.cv_compiler_crew import CVCompilerCrew
from auto_cv.data_models import AdaptorProject, JobDetails
from auto_cv.utils import build_target_dir_structure
from auto_cv.ui.shared import WWW

compiled_cv = reactive.Value[str | None](None)

@module
def pipeline_page(input, output, session, raw_tex_filename, raw_cv_content, curated_job_description):
    
    # Reactive variables state
    
    # Status banner state
    status_message = reactive.value("Ready to adapt CV to job details")
    
    
    @reactive.effect
    @reactive.event(input.tailor_cv_btn)
    def tailor_cv():
        job_details_pydantic: JobDetails = curated_job_description.get()
        
        # Create a unique dir structure based on the job title and timestamp
        target_dir = build_target_dir_structure(job_details_pydantic, WWW)

        markdown_job_description = job_details_pydantic.markdown_description
        adaptor_inputs = {
            "original_cv": raw_tex_filename.get(),
            "curated_job_description": markdown_job_description,
            "target_dir": target_dir,
            "filename_prefix": "2025_FranciscoPerezSorrosal_CV_English",
        }
        status_message.set(f"Adapting CVs: {json.dumps(adaptor_inputs, indent=4)}")
        adaption_output =CVAdaptorCrew().crew().kickoff(inputs=adaptor_inputs)
        logger.info(f"Adaption output: {adaption_output}")
        # adaptation_state.set(adaption_output.token_usage)
        
        compiler_inputs = {
            "document_path": os.path.join(target_dir, "2025_FranciscoPerezSorrosal_CV_English.tex"),
        }
        status_message.set(f"Compiling CV: {json.dumps(compiler_inputs, indent=4)}")
        compiler_output: CrewOutput = CVCompilerCrew().crew().kickoff(inputs=compiler_inputs)
        logger.info(f"Compiler output: {compiler_output}")
        # compiled_cv.set(str(compiler_output))
        
        project = AdaptorProject(
            project_dir=target_dir,
            source_cv_latex_filename=raw_tex_filename.get(),
            filename_prefix="2025_FranciscoPerezSorrosal_CV_English",
            curated_job_description=markdown_job_description,
            last_revision=0
        )
        with open(os.path.join(target_dir, "project.json"), "w") as f:
            json.dump(project.model_dump(), f, indent=4)
        
    
    
    # UI code
    
    ui.h1("CV Creation Pipeline")
    ui.h4("""Starting from a template selected from the Text Raw CVs page 
          and a Job Description selected in the Job Extractor page, will 
          create a tailored adaptation of the CV that you will be able to 
          refine in the Tailor page""")
    
    with ui.card(min_height=150):
        ui.page_opts(fillable=True)
        ui.card_header("Status")
        
        @render.ui
        @reactive.event(status_message)
        def status_banner():
            # Add a status banner right after the h1
            return ui.div(
                ui.help_text(status_message.get()),  # Get the message to print
                ui.tags.script("""
                    $(document).ready(function() {
                        setTimeout(function() {
                            $('#status_banner').fadeOut('slow');
                        }, 3000);  // 3000 milliseconds = 3 seconds
                    });
                """),
                id="status_banner",
                class_="alert alert-info"
                )
    

    with ui.card(min_height=600, fill=True):
        with ui.layout_columns():
            ui.page_opts(fillable=True)
            
            with ui.card(min_height=300, fill=True):
                ui.page_opts(fillable=True)
                
                @output
                @render.ui
                def show_raw_tex_filename():
                    return ui.card_header(f"Latex CV:\n\n{raw_tex_filename.get()}")
                
                with ui.layout_columns():

                    ui.page_opts(fillable=True)
                    with ui.card(min_height=100, fill=True, style="overflow: hidden;"):
                        ui.page_opts(fillable=True)
                        font_size = reactive.value(12)
                        ui.input_slider("font_size_slider", "Font Size", min=8, max=14, value=12) 
                        
                        @render.ui
                        @reactive.event(input.font_size_slider)
                        def update_font_size():
                            font_size.set(input.font_size_slider())
                            status_message.set(f"Font size set to {font_size.get()}")

                        @output
                        @render.ui
                        @reactive.event(input.show_full_text)
                        def update_fulltext_checkbox():
                            status_message.set(f"Show full text set to {input.show_full_text.get()}")


                    with ui.card(min_height=100, fill=True, style="height: 100px;"):
                        ui.page_opts(fillable=True)
                        ui.input_checkbox("show_full_text", "Show full text", False)
                
                with ui.card(min_height=150, fill=True):
                    ui.page_opts(fillable=True)
                    
                    @output
                    @render.ui
                    def show_raw_cv_content():
                        ui.page_opts(fillable=True)
                        
                        full_cv_text = raw_cv_content.get()
                        if not input.show_full_text.get():
                            full_cv_text = full_cv_text[:1000] + "..."
                            
                        return ui.tags.div(
                            ui.markdown(full_cv_text),
                            style=f"font-size: {font_size.get()}px",
                        )

            with ui.card(min_height=300, style = "font-size: 12px;"):
                ui.page_opts(fillable=True)
                
                @output
                @render.ui
                def show_job_title():
                    job_company = curated_job_description.get().company if curated_job_description.get() is not None else "Unknown Company"
                    job_title = curated_job_description.get().title if curated_job_description.get() is not None else "Select a Job in the Job Extractor Page"
                    return ui.card_header(f"{job_company} - {job_title}")
                                    
                @output
                @render.ui
                @reactive.event(curated_job_description)
                def show_markdown_curated_job_description():
                    serializable_job_details = curated_job_description.get()
                    if serializable_job_details is None or serializable_job_details == {}:
                        return ui.markdown("No job details available")
                    job_details_pydantic: JobDetails = JobDetails.model_validate(serializable_job_details)
                    return ui.markdown(job_details_pydantic.markdown_description or "No markdown description available")


    with ui.card(min_height=150, style = "font-size: 12px;"):
        ui.page_opts(fillable=True)
        ui.card_header("Tailor CV")
        
        @output
        @render.ui
        def configure_tailor_cv_btn():
            btn_disabled = curated_job_description.get() is None or raw_cv_content.get() == 'N/A'
            return ui.input_action_button(
                id="tailor_cv_btn", 
                label="Tailor CV",
                disabled=btn_disabled
            )
        

    with ui.card(min_height=500, style = "font-size: 12px;"):
        ui.page_opts(fillable=True)
        ui.card_header("Output CV")

        @output
        @render.ui
        def cv_to_present_str():
            if compiled_cv.get() is None:
                return ui.markdown("### No CV to display")
            status_message.set(f"CV: {compiled_cv.get()}")
            return ui.markdown(f"Showing CV:{compiled_cv.get()}")

        @render.ui
        def pdf_viewer():
            """
            Render a PDF viewer with a default CV
            """
            
            if compiled_cv.get() is None:
                return ui.markdown("Result will be shown when latex compilation finishes")
            
            cv_path = Path(compiled_cv.get())
            print(f"CV to print {cv_path}")
            if cv_path.exists():
                logger.info(f"CV path: {cv_path}")
            else:
                return ui.markdown(f"### PDF Not Found in {cv_path}")
            
            # IFrame src below only understands path relative to the www/ directory
            cv_path_relative_to_www = str(cv_path)[str(cv_path).index("www") + len("www"):]
            return ui.tags.iframe(
                src=cv_path_relative_to_www,
                width="100%", 
                height="1200px", 
                # type="application/pdf"
            )