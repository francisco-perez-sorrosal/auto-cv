from typing import Any
from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger

from shiny.express import ui

from auto_cv.data_models import JobDetails


@module
def pipeline_page(input, output, session, raw_cv_content, curated_job_description):
    
    # UI code
    
    ui.h1("Pipeline CVs")
            
    with ui.card(min_height=250, fill=True):
        ui.page_opts(fillable=True)
        ui.card_header("Raw CV Latex Content")
                
        with ui.layout_columns():
            ui.page_opts(fillable=True)
            with ui.card(min_height=100, fill=True):
                ui.page_opts(fillable=True)
                font_size = reactive.value(12)
                ui.input_slider("font_size_slider", "Font Size", min=8, max=14, value=12) 
                
                @render.ui
                @reactive.event(input.font_size_slider)
                def update_font_size():
                    font_size.set(input.font_size_slider())

            with ui.card(min_height=100, fill=True):
                ui.page_opts(fillable=True)
                ui.input_checkbox("show_full_text", "Show full text", False)
        
        with ui.card(min_height=150, fill=True):
            ui.page_opts(fillable=True)
            
            @output
            @render.ui
            @reactive.event(input.show_full_text)
            def show_raw_cv_content():
                ui.page_opts(fillable=True)
                full_cv_text = raw_cv_content.get()
                if not input.show_full_text.get():
                    full_cv_text = full_cv_text[:1000] + "..."
                    
                return ui.tags.div(
                    ui.markdown(full_cv_text),
                    style=f"font-size: {font_size.get()}px",
                )

    with ui.card(min_height=400, style = "font-size: 12px;"):
        ui.page_opts(fillable=True)
        ui.card_header("Job Description")
                            
        @output
        @render.ui
        @reactive.event(curated_job_description)
        def show_markdown_curated_job_description():
            serializable_job_details = curated_job_description.get()
            if serializable_job_details is None or serializable_job_details == {}:
                return ui.markdown("No job details available")
            job_details_pydantic: JobDetails = JobDetails.model_validate(serializable_job_details)
            return ui.markdown(job_details_pydantic.markdown_description or "No markdown description available")
