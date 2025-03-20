import os

from shiny import reactive
from shiny.express import input, ui, app_opts, render, output
from shiny.ui import Tag
from watchfiles import Change

from auto_cv.utils import DirWatcher
from auto_cv.ui.shared import WWW

from .cv_adaptor_page import  cv_adaptor_page
from .job_extractor_page import  job_extractor_page
from .pipeline_page import pipeline_page
from .raw_tex_cv_page import raw_tex_cv_page, get_raw_tex_filename, get_raw_tex_cv_content
from .job_extractor_page import get_curated_job_description

# from langtrace_python_sdk import langtrace  # Must precede any llm module imports

from llm_foundation import logger


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

raw_tex_filename = get_raw_tex_filename("tex_filename")
raw_tex_content = get_raw_tex_cv_content("cv_content")
curated_job_description = get_curated_job_description("curated_job_description")


with ui.sidebar():
        
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
    @reactive.event(curated_job_description)
    def have_curated_job_description():
        return f"Curated job description loaded: {curated_job_description.get() is not None}"


# Navigation panels

with ui.nav_panel("Raw Latex CV Templates"):
    raw_tex_cv_page("raw_tex_cv_page")

with ui.nav_panel("Job Extractor"):
    job_extractor_page("job_extractor_page")

with ui.nav_panel("CV Project Creation Pipeline"):
    pipeline_page("pipeline_page", raw_tex_filename=raw_tex_filename, raw_cv_content=raw_tex_content, curated_job_description=curated_job_description)

with ui.nav_panel("CV Tailoring Process"):
    cv_adaptor_page("cv_adaptor_page")
