from shiny.reactive._reactives import Value


import os
from pathlib import Path
import threading

from numpy import column_stack, full
from pyvis.network import Network
from shiny.express import ui, module, render
from shiny import reactive
from watchfiles import Change

from auto_cv.cache import BasicInMemoryCache

from llm_foundation import logger

from auto_cv.data_models import JobDetails
from auto_cv.utils import make_serializable, run_async_watcher

from functools import partial

from htmltools import css
from shiny.express import ui
from shiny.ui import page_fillable

from auto_cv.ui.shared import CV_TEMPLATES, DEFAULT_RAW_CV_TEMPLATE

from auto_cv.utils import save_text_file, read_text_file, find_files_with_extension


def only_added_tex(change: Change, path: str) -> bool:
    allowed_extensions = '.tex'
    return change == Change.added and path.endswith(allowed_extensions)


tex_filename: Value[str] = reactive.Value[str](Path(CV_TEMPLATES, DEFAULT_RAW_CV_TEMPLATE).as_posix())
cv_content: Value[str] = reactive.Value[str](read_text_file(Path(CV_TEMPLATES, DEFAULT_RAW_CV_TEMPLATE)))


@module
def raw_tex_cv_page(input, output, session):

    
    # Global list to store tex file changes and a lock for thread safety
    global tex_changed_files
    tex_changed_files = {f: os.path.basename(f) for f in find_files_with_extension(CV_TEMPLATES, extension=".tex")}
    lock = threading.Lock()

    # Start the asynchronous file watcher in a daemon thread.
    watcher_thread = threading.Thread(target=run_async_watcher, args=(CV_TEMPLATES, tex_changed_files, lock, only_added_tex), daemon=True)
    watcher_thread.start()

    print(f"tex_changed_files: {tex_changed_files}")
    
    # Reactive variables state
    raw_cv_template_files = reactive.value(tex_changed_files)
    # Status banner state
    status_message = reactive.value("Ready to extract job details")
    
    # UI code
    
    ui.h1("Raw Template CVs")
    
    with ui.card(min_height=180):
        ui.page_opts(fillable=True)
        ui.card_header("Raw CV Latex Templates")

        with ui.layout_columns():
            
            with ui.card(min_height=120, fill=True):
                ui.page_opts(fillable=True)
                ui.input_file(
                    "cv_upload", 
                    "Upload a new Latex CV template...", 
                    accept=[".tex"], 
                    multiple=False,
                    placeholder="Select a latex CV to upload",
                )
                    
            with ui.card(min_height=120, fill=True):
                ui.page_opts(fillable=True)
                def poll_func():
                    with lock:
                        # Return a copy of the list for rendering.
                        return list(tex_changed_files)
        
                @reactive.poll(poll_func=poll_func, interval_secs=1)
                def new_tex_files():
                    raw_cv_template_files.set(tex_changed_files)
                    return list(tex_changed_files)

                @output
                @render.ui()
                def show_raw_cv_template_selection():        
                    return ui.input_select(
                        id="select_raw_cv_template",
                    label="...or select a CV template:",
                    choices=raw_cv_template_files.get(),
                )            
        
    with ui.card(min_height=200):
        ui.page_opts(fillable=True)
        ui.card_header("Latex Content")
        
        font_size = reactive.value(12)
        ui.input_slider("font_size_slider", "Font Size", min=8, max=14, value=12)
        
        @render.ui
        @reactive.event(input.font_size_slider)
        def update_font_size():
            font_size.set(input.font_size_slider())
        
        with ui.card(min_height=150):
            @output
            @render.ui
            def show_raw_cv_content():
                selected_raw_cv = input.select_raw_cv_template.get()
                if selected_raw_cv is None:
                    ui.markdown("Please select a CV to view. Showing default for now...")
                    selected_raw_cv = DEFAULT_RAW_CV_TEMPLATE
                cv_content.set(read_text_file(Path(CV_TEMPLATES, selected_raw_cv)))
                tex_filename.set(Path(CV_TEMPLATES, selected_raw_cv).as_posix())

                return ui.tags.div(
                    ui.markdown(cv_content.get()),
                    style=f"font-size: {font_size.get()}px",
                )

        @render.text
        @reactive.event(input.cv_upload)
        def cv_text():
            logger.info(f"Reading CV file from {input.cv_upload.get()}")
            file = input.cv_upload.get()[0]['datapath']
            file_content = read_text_file(file)
            filename = input.cv_upload.get()[0]['name']
            save_text_file(Path(CV_TEMPLATES, filename), file_content, overwrite=False)
            logger.info(f"CV file saved in {os.path.join(CV_TEMPLATES, filename)}")
            RAW_CVS = {f: os.path.basename(f) for f in find_files_with_extension(CV_TEMPLATES, extension=".tex")}
            raw_cv_template_files.set(RAW_CVS)


# Module just to return the cv_content to the main_shiny_app.py
@module
def get_raw_tex_cv_content(input, output, session):
    return cv_content

@module
def get_raw_tex_filename(input, output, session):
    return tex_filename
