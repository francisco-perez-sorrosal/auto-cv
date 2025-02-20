import os
from pathlib import Path

from pyvis.network import Network
from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

@module
def cv_adaptor_page(input, output, session, sidebar_text, original_cv):
    
    ui.h2("CV Adaptor Page")
    
    # Sidebar text
    text = reactive.value("N/A")
    uploaded_file = reactive.value("N/A")

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
            height="800px", 
            # type="application/pdf"
        )


    # with ui.card(full_screen=True):
    #     pdf_viewer
        # ui.h2("CV Adaptor")
        
        # with ui.layout_sidebar():
        #     with ui.sidebar():
        #         ui.input_file(
        #             "cv_upload", 
        #             "Upload CV", 
        #             accept=[".pdf"], 
        #             multiple=False
        #         )    
        # ui.output_ui("pdf_viewer")
        

    
    # with ui.card(full_screen=True):
        
    #     @render.ui()
    #     def graph():
    #         pass

        