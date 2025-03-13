import concurrent.futures
import os
from pathlib import Path
import threading



from shiny import reactive
from shiny.express import input, ui, app_opts, render, output
from shiny.ui import Tag
from watchfiles import Change

from auto_cv.utils import find_files_with_extension, run_async_watcher
from auto_cv.ui.shared import WWW

from .cv_adaptor_page import  cv_adaptor_page
from .job_extractor_page import  job_extractor_page
from .pipeline_page import pipeline_page
from .raw_tex_cv_page import raw_tex_cv_page, get_raw_tex_filename, get_raw_tex_cv_content
from .job_extractor_page import get_curated_job_description

# from langtrace_python_sdk import langtrace  # Must precede any llm module imports

from llm_foundation import logger


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

raw_tex_filename = get_raw_tex_filename("tex_filename")
raw_tex_content = get_raw_tex_cv_content("cv_content")
curated_job_description = get_curated_job_description("curated_job_description")


with ui.sidebar():
    
    # raw_tex_content = reactive.Value()
        
    cv_to_present = reactive.Value("N/A")

    ui.h1("CV Polisher")

    ui.markdown(f"Watching dir:\n{WWW}")
    
    @output
    @render.ui
    @reactive.event(raw_tex_content)
    def have_raw_tex_cv_content():
        return f"Raw CV content loaded: {raw_tex_content.get() != 'N/A'}"

    @output
    @render.ui
    # @reactive.event(curated_job_description)
    def have_curated_job_description():
        return f"Curated job description loaded: {curated_job_description.get() is not None}"

    
    with ui.card():

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

with ui.nav_panel("Pipeline"):
    pipeline_page("pipeline_page", raw_tex_filename=raw_tex_filename, raw_cv_content=raw_tex_content, curated_job_description=curated_job_description)


with ui.nav_panel("Raw CV"):
    raw_tex_cv_page("raw_tex_cv_page")


with ui.nav_panel("CV Adaptor Page"):
    cv_adaptor_page("cv_adaptor_page", 
                    cv_2_present=cv_to_present,)


with ui.nav_panel("Job Extractor Page"):
    job_extractor_page("job_extractor_page")
