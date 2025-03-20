from os.path import basename
from crewai.crews.crew_output import CrewOutput
import os
import json

from pathlib import Path
from shiny.ui._chat import Chat

from shiny.express import ui, module, render
from shiny import reactive

from llm_foundation import logger
from shiny.ui import Tag

from auto_cv.cv_polisher_crew import CVPolisherCrew
from auto_cv.cv_compiler_crew import CVCompilerCrew
from auto_cv.data_models import AdaptorProject
from auto_cv.ui.shared import WWW
from auto_cv.utils import DirWatcher, only_added_pdfs, only_added_tex

from llm_foundation import logger


# Start the asynchronous file watcher in a daemon thread for pdf files in the WWW directory.
PROJECTS = Path(WWW, "generated_cvs")
project_dir_watcher = DirWatcher(PROJECTS)
project_dir_watcher.start()

# Reactive watchers for pdf and tex files
pdf_revision_watcher_reactive = reactive.value[DirWatcher | None](None)
tex_revision_watcher_reactive = reactive.value[DirWatcher | None](None)

project_metadata = reactive.value[AdaptorProject | None](None)
current_projects = reactive.value(project_dir_watcher.changed_files)


@module
def cv_adaptor_page(input, output, session):
    
    # Reactive variables state
    
    # Status banner state
    status_message = reactive.value("Ready to adapt CV to job details")    
    
    # CV to present
    cv_to_present = reactive.value("N/A")
    latex_revision_text_reactive = reactive.value("")
    cv_template_text_reactive = reactive.value("")
    
    # Adaptation and compile states
    adaptation_state = reactive.value()
    compile_state = reactive.value()
    
    # UI code
    
    ui.h2("CV Adaptor")

    with ui.card(min_height=150, fill=True, fluid=True):
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

    with ui.card(min_height=400, fill=True):
        @render.ui()
        @reactive.event(input.selected_project)
        def selected_project_header():
            return ui.card_header(f"Selected Project: {basename(project_metadata.get().project_dir) if project_metadata.get() else 'None yet'}")
        
        with ui.layout_columns():
            with ui.card():
                ui.card_header("CV Project Selection")

                @render.ui()
                async def project_dropdown_list() -> Tag:
                    projects = project_dir_watcher.new_changes()  # new_projects()
                    if len(projects) > 0:
                        logger.info(f"{len(projects)} projects detected:\n{projects}")
                        # Display the files as a bulleted list.
                        return ui.input_select(
                            "selected_project",
                            "Select a project to display:",
                            choices={str(p): str(p.name) for p in projects},
                            multiple=False,
                            width="500px",
                        )
                    else:
                        return ui.tags.div("No changes detected yet.")

                @reactive.effect
                @reactive.event(input.selected_project)
                def update_project():
                    project_path = input.selected_project.get()
                    
                    logger.info(f"Loading project {project_path}")
                    with open(os.path.join(project_path, "project.json"), "r") as f:
                        project_json = json.load(f)
                        project = AdaptorProject.model_validate(project_json)
                        project_metadata.set(project)

                    status_message.set(f"Last Project Adapted: {project}")

            with ui.card():
                ui.card_header("Job Description")

                @render.ui()
                async def show_job_description() -> Tag:
                    return ui.tags.div(
                        ui.markdown(project_metadata.get().curated_job_description)
                    )

            with ui.card():
                ui.card_header("Latex Revision Selection")

                @render.ui()
                async def latex_revision_dropdown_list() -> Tag:
                    revisions = tex_revision_watcher_reactive.get().new_changes()  # new_projects()
                    if len(revisions) > 0:
                        logger.info(f"{len(revisions)} revisions detected:\n{revisions}")
                        # Display the files as a bulleted list.
                        return ui.input_select(
                            "selected_latex_revision",
                            "Select a Latex revision to display:",
                            choices={str(p): str(p.name) for p in revisions},
                            multiple=False,
                            width="500px",
                        )
                    else:
                        return ui.tags.div("No changes detected yet.")

                @reactive.effect
                @reactive.event(input.selected_latex_revision)
                def latex_revision_change():
                    logger.info(f"Changing Latex revision to show to {input.selected_latex_revision.get()}")
                    # cv_to_present.set(input.selected_latex_revision.get())

    
    with ui.card(min_height=400, fill=True):
        with ui.layout_columns():
            with ui.card(min_height=400, fill=True):
                ui.card_header("Source Template CV")
                
                @output
                @render.ui
                def show_source_template_cv_content():
                    ui.page_opts(fillable=True)
                    
                    cv_template_text_file = project_metadata.get().source_cv_latex_filename
                    with open(cv_template_text_file, "r") as f:
                        cv_template_text = f.read()
                    # if not input.show_full_text.get():
                    #     full_template_text = full_template_text[:1000] + "..."
                    cv_template_text_reactive.set(cv_template_text)
                    return ui.tags.div(
                        ui.markdown(cv_template_text),
                        # style=f"font-size: {font_size.get()}px",
                    )

            with ui.card(min_height=400, fill=True):
                ui.card_header("Target Latex CV Revision")
                
                @output
                @render.ui
                def show_target_latex_cv_revision_content():
                    ui.page_opts(fillable=True)
                    
                    latex_revision_text_file = input.selected_latex_revision.get()
                    with open(latex_revision_text_file, "r") as f:
                        latex_revision_text = f.read()
                    # if not input.show_full_text.get():
                    #     full_template_text = full_template_text[:1000] + "..."
                    latex_revision_text_reactive.set(latex_revision_text)
                    return ui.tags.div(
                        ui.markdown(latex_revision_text),
                        # style=f"font-size: {font_size.get()}px",
                    )


      
        @reactive.effect
        @reactive.event(input.selected_project)
        def project_change():
            logger.info(f"Adding new project watcher for pdfs in project {input.selected_project.get()}")
            pdf_revision_dir_watcher = DirWatcher(
                directory=Path(input.selected_project.get()),
                extension=".pdf",
                filter=only_added_pdfs
            )
            pdf_revision_dir_watcher.start()
            pdf_revision_watcher_reactive.set(pdf_revision_dir_watcher)

            tex_revision_dir_watcher = DirWatcher(
                directory=Path(input.selected_project.get()),
                extension=".tex",
                filter=only_added_tex
            )
            tex_revision_dir_watcher.start()
            tex_revision_watcher_reactive.set(tex_revision_dir_watcher)

    async def create_polished_cv_revision(user_instructions: str):

        project_info: AdaptorProject | None = project_metadata.get()
        if project_info is None:
            status_message.set("Please select a project to adapt.")
            return

        # Create new revision prefix
        project_info.last_revision += 1
        filename_prefix = f"{project_info.filename_prefix}_rev_{project_info.last_revision}"

        polisher_inputs = {
            "user_instructions": user_instructions,
            "cv_revision": latex_revision_text_reactive.get(),
            "original_cv": cv_template_text_reactive.get(),
            "curated_job_description": project_info.curated_job_description,
            "target_dir": project_info.project_dir,
            "filename_prefix": filename_prefix
        }
        status_message.set(f"Polishing CV Review: {polisher_inputs}")
        await chat.append_message(f"Polishing CV Review: {polisher_inputs}")
        polisher_output =CVPolisherCrew().crew().kickoff(inputs=polisher_inputs)
        adaptation_state.set(polisher_output.token_usage)
        
        compiler_inputs = {
            "document_path": os.path.join(project_info.project_dir, f"{filename_prefix}.tex"),
        }        
        await chat.append_message(f"Compiling CV: {compiler_inputs}")
        compiler_output: CrewOutput = CVCompilerCrew().crew().kickoff(inputs=compiler_inputs)
        compile_state.set(compiler_output.token_usage)
        
        with open(os.path.join(project_info.project_dir, "project.json"), "w") as f:
            json.dump(project_info.model_dump(), f, indent=4)
        project_metadata.set(project_info)
        
        return compiler_output.raw
        

    # Create and display chat instance
    with ui.card(min_height=300, fill=True):
        # Create a chat
        chat = ui.Chat(
            id="chat",
            messages=["Add your instructions to polish the CV!"],
        )        
        chat.ui()
        
        # Define a callback to run when the user submits a message
        @chat.on_user_submit
        async def handle_user_input():
            # Get the user's input            
            # Append the response into the chat
            orders = chat.user_input()
            await chat.append_message(f"Accomplishing your orders... {orders}")
            response = await create_polished_cv_revision(orders)
            if response is not None:
                cv_to_present.set(response)
            await chat.append_message(f"Response: {response}")

        
    # Cost display
    with ui.card(min_height=200):
        ui.card_header("Costs")
        
        with ui.layout_columns():
            with ui.card():
                ui.card_header("Adaptation Cost")
                @render.ui
                def show_adaptation_state():
                    return ui.markdown(f"{adaptation_state.get()}")
                
            with ui.card():
                ui.card_header("Compile Cost")
                @render.ui
                def show_compile_state():
                    return ui.markdown(f"{compile_state.get()}")

    with ui.card(min_height=200):
        ui.card_header("Revision List")

        @render.ui()
        async def revision_list() -> Tag:
            if pdf_revision_watcher_reactive.get() is not None:
                revisions = pdf_revision_watcher_reactive.get().new_changes()
                logger.info(f"Revisions: {revisions}")
                if revisions:                
                    # Display the files as a bulleted list.
                    return ui.input_select(
                        "selected_pdf_revision",
                        "Select a PDF revision to display:",
                        choices={str(p): str(p.name) for p in revisions},
                        multiple=False,
                        width="1000px",
                    )
            else:
                return ui.tags.div("No changes detected yet.")
            

        @reactive.effect
        @reactive.event(input.selected_pdf_revision)
        def pdf_revision_change():
            logger.info(f"Changing document revision to show to {input.selected_pdf_revision.get()}")
            cv_to_present.set(input.selected_pdf_revision.get())

                
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
