import os
from pathlib import Path
from typing import Any

from numpy import column_stack, full
from pyvis.network import Network
from shiny.express import ui, module, render
from shiny import reactive

from auto_cv.cache import BasicInMemoryCache

from llm_foundation import logger

from auto_cv.data_models import JobDetails
from auto_cv.utils import make_serializable

from functools import partial

from htmltools import css
from shiny.express import ui
from shiny.ui import page_fillable


extracted_job_description_cache = BasicInMemoryCache(
    app_name="auto-cv", 
    cache_subdir="extracted_job_descriptions_cache", 
    cache_file="extracted_job_descriptions.jsonl", 
    cache_key_name="url"
)

def get_job_details(url_idx: str, url: str):
    # Check cache first
    if extracted_job_description_cache.exists(url):
        job_stuff = extracted_job_description_cache.get(url)
        job_stuff = make_serializable(job_stuff)  # type: ignore
        status_message.set(f"Job description found in cache for ({url_idx}) - {url}")
        return job_stuff
    else:
        status_message.set(f"No cached job description found for {url}")
        return {}

# Predefined example LinkedIn job URLs
EXAMPLE_URLS = {
    "Amazon test": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3959722886",
    "Amazon Test 2": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4070067137",
}

DEFAULT_EXAMPLE_URL_IDX = list(EXAMPLE_URLS.items())[0][0]

# Reactive variables state
    
# Status banner state
status_message = reactive.value("Ready to extract job details")
selected_url_idx = reactive.value(DEFAULT_EXAMPLE_URL_IDX)
selected_url = reactive.value(EXAMPLE_URLS[DEFAULT_EXAMPLE_URL_IDX])
DEFAULT_JOB_DETAILS = get_job_details(DEFAULT_EXAMPLE_URL_IDX, EXAMPLE_URLS[DEFAULT_EXAMPLE_URL_IDX])
job_details = reactive.value(DEFAULT_JOB_DETAILS)

curated_job_description: reactive.Value[Any] = reactive.Value[Any](JobDetails.model_validate(DEFAULT_JOB_DETAILS))


# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

def format_job_basics(job_details: JobDetails):
    """
    Format job details for display
    
    Args:
        job_details (dict): Extracted job details
    
    Returns:
        str: Formatted markdown text
    """
    if not job_details:
        return "No job details found."
    
    print(f"Formatting job details:\n{type(job_details)}")
    
    # Create a formatted markdown representation
    formatted_text = f"""
#### Basic Job Info
- **URL**: {job_details.url}
- **Job Title (Job Id)**: {job_details.title} ({job_details.job_id})
- **Company Name**: {job_details.company}
- **Location**: {job_details.location}
- **Salary**: {job_details.salary}
""" 
    return formatted_text

@module
def job_extractor_page(input, output, session):
    # ui.page_opts(fillable=True)
    
    ui.markdown(f"Default example URL: {DEFAULT_EXAMPLE_URL_IDX}")
    
    @render.ui  # We have to keep render.ui for the reactive event to work
    @reactive.event(input.select_job_url)
    def job_url_selected():
        selected_url_idx.set(input.select_job_url.get())
        selected_url.set(EXAMPLE_URLS[selected_url_idx.get()])
        status_message.set(f"Job URL selected: ({selected_url_idx.get()}) - {selected_url.get()}")
        
        job_details.set(get_job_details(selected_url_idx.get(), selected_url.get()))
        

    # UI code
    
    ui.h1("Job Extractor")
    
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

    with ui.card(min_height=200):
        # Add a dropdown box with example URLs
        ui.input_select(
            id="select_job_url",
            label="Select a Job URL:",
            choices=EXAMPLE_URLS,
            selected=EXAMPLE_URLS[list(EXAMPLE_URLS.items())[0][0]],
        )

    with ui.layout_columns(col_widths=(3, 9)):
        
        with ui.card(min_height=1200, style = "font-size: 10px;"):
            ui.card_header("Job Basics")
            
            @output
            @render.ui
            @reactive.event(job_details)
            def show_job_basics():
                # Serialize before use as iso format is not supported as is
                serializable_job_details = job_details.get()
                if serializable_job_details == {}:
                    return ui.markdown("No job details available")

                print(f"Serializing job details:\n{serializable_job_details}")
                job_details_pydantic = JobDetails.model_validate(serializable_job_details)
                return ui.markdown(format_job_basics(job_details_pydantic))
        
    
        with ui.card(min_height=1200, style = "font-size: 10px;"):
            ui.card_header("Job Details")
            
            with ui.layout_columns():
                with ui.card():  
                    ui.card_header("Raw Job Description as Extracted")
                    ui.p("Extracted Raw Text")
                    
                    @output
                    @render.ui
                    @reactive.event(job_details)
                    def show_raw_description():
                        serializable_job_details = job_details.get()
                        if serializable_job_details == {}:
                            return "No job details available"
                        job_details_pydantic = JobDetails.model_validate(serializable_job_details)
                        return job_details_pydantic.raw_description or "No raw description available"


                with ui.card(style = "font-size: 12px;"):  
                    ui.card_header("Curated Job Description")
                    ui.p("Markdown Formatted Description")
                    
                    @output
                    @render.ui
                    @reactive.event(job_details)
                    def show_markdown_description():
                        serializable_job_details = job_details.get()
                        if serializable_job_details is None or serializable_job_details == {}:
                            return ui.markdown("No job details available")
                        job_details_pydantic = JobDetails.model_validate(serializable_job_details)
                        curated_job_description.set(job_details_pydantic)
                        return ui.markdown(job_details_pydantic.markdown_description or "No markdown description available")


# Module just to return the curated_job_description to the main_shiny_app.py
@module
def get_curated_job_description(input, output, session):
    return curated_job_description
