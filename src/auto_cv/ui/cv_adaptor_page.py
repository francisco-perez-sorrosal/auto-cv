import datetime
import os
from pathlib import Path

from pyvis.network import Network
from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger

from auto_cv.cache import BasicInMemoryCache
from auto_cv.data_models import JobDetails
from auto_cv.utils import make_serializable

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

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
        downloaded_jobs = extracted_job_description_cache.keys
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


    @reactive.effect
    @reactive.event(input.adapt_cv_btn)
    def adapt_cv():
        job_id = job_selected.get()
        cached_job = extracted_job_description_cache.get(job_id)  # type: ignore
        cached_job = make_serializable(cached_job)  # type: ignore
        pydantic_cached_job = JobDetails.model_validate(cached_job)
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y_%m_%d_%H_%M_%S")
        file_prefix = pydantic_cached_job.generate_filename_prefix() + "_" + timestamp_str
        root_dir = os.path.join(WWW, file_prefix)
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        
        fake_pdf_path = os.path.join(root_dir, os.path.basename(root_dir) + ".pdf")
        with open(fake_pdf_path, 'wb') as f:
            f.write(b'')
        
        print(pydantic_cached_job.generate_filename_prefix(), os.getcwd())

    
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

    @render.code
    def out():
        return f"Sidebar text says {str(text.get())} and CV file says {str(uploaded_file.get())}"    


    with ui.card(min_height=1200,):

        @output
        @render.ui
        def cv_to_present_str():
            return ui.markdown(f"# Showing CV:\n{cv_to_present.get()}")

        
        # Default CV path
        DEFAULT_CV_PATH = os.path.join(WWW, "2025_FranciscoPerezSorrosal_CV_English.pdf")

        @render.ui
        def pdf_viewer():
            """
            Render a PDF viewer with a default CV
            """
            cv_path = Path(DEFAULT_CV_PATH)
            
            if cv_path.exists():
                logger.info(f"CV path: {cv_path}")
            else:
                return ui.markdown(f"### PDF Not Found in {cv_path}")
            
            return ui.tags.iframe(
                src=cv_path.name,
                width="100%", 
                height="1200px", 
                # type="application/pdf"
            )
        