import asyncio
import concurrent.futures
from functools import partial
import os
from pathlib import Path
import threading


from htmltools import css
from shiny import Session, reactive
from shiny.express import input, ui, app_opts, render, output
from shiny.ui import Tag, page_fillable, page_fluid
from watchfiles import Change

from auto_cv.utils import find_files_with_extension, run_async_watcher


from .cv_adaptor_page import  cv_adaptor_page
from .job_extractor_page import  job_extractor_page
from .raw_tex_cv_page import raw_tex_cv_page, get_raw_tex_cv_content

# from langtrace_python_sdk import langtrace  # Must precede any llm module imports

from llm_foundation import logger

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = Path(DIR, "www")
CV_TEMPLATES = Path(WWW, "cv_templates")
DEFAULT_RAW_CV_TEMPLATE = "2025_FranciscoPerezSorrosal_CV_English.tex"

# Execute the extended task logic on a different thread. To use a different
# process instead, use concurrent.futures.ProcessPoolExecutor.
pool = concurrent.futures.ProcessPoolExecutor(max_workers=8)

# We need to load the .env file in a function, otherwise there's an weird Shiny-related error
def load_dotenv():
    import dotenv
    dotenv.load_dotenv()

load_dotenv()
logger.info(f"Observing agents: {bool(os.environ.get("OBSERVE_AGENTS"))}")
# if bool(os.environ.get("OBSERVE_AGENTS")):
#     langtrace.init()

logger.info("Starting main app...")

# Configure Shiny page
app_opts(static_assets=WWW)

ui.page_opts(
    title="CV Polisher",
    # fillable=True,
    # fluid=True,
    # fillable_mobile=True,
)

ui.nav_spacer()

def only_added_pdf(change: Change, path: str) -> bool:
    allowed_extensions = '.pdf'
    return change == Change.added and path.endswith(allowed_extensions)


# Global list to store file changes and a lock for thread safety
global changed_files
changed_files = find_files_with_extension(WWW)
lock = threading.Lock()

# Start the asynchronous file watcher in a daemon thread.
watcher_thread = threading.Thread(target=run_async_watcher, args=(WWW, changed_files, lock, only_added_pdf), daemon=True)
watcher_thread.start()

raw_tex_content = get_raw_tex_cv_content("cv_content")



with ui.sidebar():
    
    # raw_tex_content = reactive.Value()
        
    cv_to_present = reactive.Value("N/A")

    ui.h1("CV Polisher")
    
    ui.input_text("text_in", "Type something here (Useless now):")

    ui.markdown(f"Watching dir:\n{WWW}")
    
    
    with ui.card():

        @output
        @render.ui
        @reactive.event(raw_tex_content)
        def have_raw_tex_cv_content():
            return f"Raw CV content loaded: {raw_tex_content.get() != 'N/A'}"

        def poll_func():
            with lock:
                # Return a copy of the list for rendering.
                return list(changed_files)
        
        @reactive.poll(poll_func=poll_func, interval_secs=1)
        def new_pdfs():
            cv_to_present.set(changed_files[-1])
            return list(changed_files)
        
        @render.ui()
        async def file_list() -> Tag:
            pdfs = new_pdfs()
            if pdfs:
                
                # Display the files as a bulleted list.
                return ui.input_select(
                    "selected_pdf",
                    "Select a PDF to display:",
                    new_pdfs(),
                    multiple=False,
                )
            else:
                return ui.tags.div("No changes detected yet.")
            
        @reactive.effect
        @reactive.event(input.selected_pdf)
        def update_cv_to_present():
            cv_to_present.set(input.selected_pdf.get())


# Navigation panels

with ui.nav_panel("Raw CV"):
    raw_tex_cv_page("raw_tex_cv_page", template_dir=CV_TEMPLATES, default_template=DEFAULT_RAW_CV_TEMPLATE)


with ui.nav_panel("CV Adaptor Page"):
    cv_adaptor_page("cv_adaptor_page", 
                    sidebar_text=input.text_in,
                    cv_2_present=cv_to_present,)

with ui.nav_panel("Job Extractor Page"):
    job_extractor_page("job_extractor_page")
