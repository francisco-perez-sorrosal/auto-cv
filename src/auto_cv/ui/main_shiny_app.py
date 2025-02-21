import asyncio
import concurrent.futures
from functools import partial
import os
from pathlib import Path
import threading


from htmltools import css
from shiny import reactive
from shiny.express import input, ui, app_opts, render, output
from shiny.ui import Tag, page_fillable, page_fluid
from watchfiles import Change, DefaultFilter, watch, awatch, run_process, arun_process


from .cv_adaptor_page import  cv_adaptor_page
from .job_extractor_page import  job_extractor_page
# from langtrace_python_sdk import langtrace  # Must precede any llm module imports

from llm_foundation import logger

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(DIR, "www")

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
changed_files = []
lock = threading.Lock()

async def directory_watcher(directory):
    """
    Asynchronously watches the given directory for file changes.
    Each detected change is appended to the global changed_files list.
    """
    async for changes in awatch(directory, watch_filter=only_added_pdf):
        logger.info(f"Changes: {changes}")
        
        with lock:
            for change_type, file_path in changes:
                changed_files.append(file_path)
                print(f"Detected change in: {file_path}")

def run_async_watcher():
    """
    Runs the asynchronous directory watcher inside an asyncio event loop.
    """
    asyncio.run(directory_watcher(WWW))
    

# Start the asynchronous file watcher in a daemon thread.
watcher_thread = threading.Thread(target=run_async_watcher, daemon=True)
watcher_thread.start()

with ui.sidebar():
        
    ui.h1("CV Polisher")
    
    ui.input_text("text_in", "Type something here (Useless now):")

    ui.markdown(f"Watching dir:\n{WWW}")
    with ui.card():

        def poll_func():
            with lock:
                # Return a copy of the list for rendering.
                return list(changed_files)
        
        @reactive.poll(poll_func=poll_func, interval_secs=1)
        def new_pdfs():
            return list(changed_files)
        
        # @output(id="pdfs_added")
        @render.ui()
        async def file_list() -> Tag:
            pdfs = new_pdfs()
            if pdfs:
                # Display the files as a bulleted list.
                return ui.input_select(
                    "pdfs_added",
                    "Select a PDF to display:",
                    new_pdfs(),
                    multiple=False,
                )
            else:
                return ui.tags.div("No changes detected yet.")

    ui.input_file(
        "cv_upload", 
        "Upload CV", 
        accept=[".pdf"], 
        multiple=False,
        placeholder="Select a CV to upload",
        
    )

with ui.nav_panel("Job Extractor Page"):
    job_extractor_page("job_extractor_page")

with ui.nav_panel("CV Adaptor Page"):
    cv_adaptor_page("cv_adaptor_page", 
                    sidebar_text=input.text_in,
                    original_cv=input.cv_upload,)
                    # original_cv=output.pdfs_added)
