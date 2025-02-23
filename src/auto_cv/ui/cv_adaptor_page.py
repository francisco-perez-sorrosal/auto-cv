import datetime
import os
from pathlib import Path

from pyvis.network import Network
from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger

from auto_cv.cache import BasicInMemoryCache
from auto_cv.cv_adaptor_crew import CVAdaptorCrew
from auto_cv.cv_compiler_crew import CVCompilerCrew
from auto_cv.data_models import JobDetails
from auto_cv.utils import make_serializable

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

# Default CV path for test purposes
DEFAULT_CV_PATH = os.path.join(WWW, "2025_FranciscoPerezSorrosal_CV_English.pdf")


extracted_job_description_cache = BasicInMemoryCache(
    app_name="auto-cv", 
    cache_subdir="extracted_job_descriptions_cache", 
    cache_file="extracted_job_descriptions.jsonl", 
    cache_key_name="url"
)

@module
def cv_adaptor_page(input, output, session, sidebar_text, original_cv, cv_2_present):
    
    # Reactive variables state
    
    # Status banner state
    status_message = reactive.value("Ready to adapt CV to job details")

    first_job = extracted_job_description_cache.keys[0] if not extracted_job_description_cache.is_empty() else "N/A"
    job_selected = reactive.value(first_job)
    
    # Sidebar text
    text = reactive.value("N/A")
    uploaded_file = reactive.value("N/A")
    cv_to_present = reactive.value("N/A")

    @reactive.effect
    @reactive.event(cv_2_present)
    def get_cv_2_present_event():
        cv_to_present.set(cv_2_present.get())
        status_message.set(f"Last CV Compiled: {os.path.basename(cv_to_present.get())}")

    # UI code

    ui.h2("CV Adaptor Page")

    with ui.card(min_height=150):
        ui.page_opts(fillable=True)
        ui.card_header("Status")
        
        # @output
        # @render.text
        # def status_message_out():
        #     return str(job_selected.get())

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

    @render.ui()
    async def cached_jobs_to_adapt():    
        downloaded_jobs = extracted_job_description_cache.build_dict_with("company", "title")    
        if downloaded_jobs:
            # Display the files as a bulleted list.
            return ui.input_select(
                "job_selected_from_cache",
                "Select job to adapt CV",
                downloaded_jobs,
                multiple=False,
                width="1000px",
            )
        else:
            return ui.tags.div("No changes detected yet.")

    @reactive.event(input.job_selected_from_cache)
    def job_selected_evt():    
        job_selected.set(input.job_selected_from_cache.get())

    adaptation_state = reactive.value()
    compile_state = reactive.value()

    @reactive.effect
    @reactive.event(input.adapt_cv_btn)
    def adapt_cv():
        job_id = job_selected.get()
        cached_job = extracted_job_description_cache.get(job_id)  # type: ignore
        cached_job = make_serializable(cached_job)  # type: ignore        
        pydantic_cached_job = JobDetails.model_validate(cached_job)
        
        # Create a unique dir structure based on the job title and timestamp
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y_%m_%d_%H_%M_%S")
        file_prefix = pydantic_cached_job.generate_filename_prefix() + "_" + timestamp_str
        target_dir = os.path.join(WWW, 'generated_cvs', file_prefix)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        adaptor_inputs = {
            "original_cv": "/Users/fperez/dev/auto-cv/docs/2025_FranciscoPerezSorrosal_CV_English.tex",
            "target_dir": target_dir,
            "filename_prefix": "2025_FranciscoPerezSorrosal_CV_English"
        }
        status_message.set(f"Adapting CV: {adaptor_inputs}")
        adaption_output =CVAdaptorCrew().crew().kickoff(inputs=adaptor_inputs)
        adaptation_state.set(adaption_output.token_usage)
        
        compiler_inputs = {
            "document": os.path.join(target_dir, "2025_FranciscoPerezSorrosal_CV_English.tex"),
        }
        compiler_output = CVCompilerCrew().crew().kickoff(inputs=compiler_inputs)
        compile_state.set(compiler_output.token_usage)

    
    # Button to search in cache
    ui.input_action_button(
        id="adapt_cv_btn", 
        label="Adapt CV",
    )


    @reactive.effect
    @reactive.event(sidebar_text)
    def get_sidebar_text_events():
        text.set(str(sidebar_text.get()) + " and " + str(original_cv.get()))

    @reactive.effect
    @reactive.event(original_cv)
    def get_cv_filename_events():
        uploaded_file.set(str(original_cv.get()))

    # @render.code
    # def out():
    #     return f"Last cv compiled: {str(last_cv_compiled.get())} and CV file says {str(input.job_selected_from_cache.get())}"    

    with ui.card(min_height=200):
        with ui.layout_columns():
            with ui.card():
                ui.card_header("Adaptation Cost")
                @render.ui
                def show_adaptation_state():
                    return ui.markdown(f"# {adaptation_state.get()}")
                
            with ui.card():
                ui.card_header("Compile Cost")
                @render.ui
                def show_compile_state():
                    return ui.markdown(f"# {compile_state.get()}")
                
    with ui.card(min_height=1200,):

        @output
        @render.ui
        def cv_to_present_str():
            status_message.set(f"CV: {cv_to_present.get()}")
            return ui.markdown(f"# Showing CV:\n{cv_to_present.get()}")

        @render.ui
        def pdf_viewer():
            """
            Render a PDF viewer with a default CV
            """
            cv_path = Path(cv_to_present.get())
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
        