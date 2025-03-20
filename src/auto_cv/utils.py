import asyncio
from datetime import datetime
import os
from pathlib import Path
import threading
from typing import Any, Callable
from shiny import reactive
from watchfiles import Change, watch, awatch, run_process, arun_process

from llm_foundation import logger

from auto_cv.data_models import JobDetails

class DirWatcher:
    
    def __init__(self, directory: Path, filter: Callable | None = None, extension: str | None = None):
        self._lock = threading.Lock()
        
        self.directory = directory
        self.filter = filter
        self._changed_files = find_directories_or_files_with_extension(self.directory, extension)
        print(f"Initial files: {self._changed_files}")


    def poll_func(self):
        with self._lock:
            # Return a copy of the list for rendering.
            return list(self._changed_files)


    def start(self, daemon: bool = True):
        self._watcher_thread = threading.Thread(target=run_async_watcher, 
                                                args=(self.directory, self._changed_files, self._lock, self.filter), 
                                                daemon=daemon)
        self._watcher_thread.start()


    def new_changes(self):
        @reactive.poll(poll_func=self.poll_func, interval_secs=5)
        def changes():
            if self._watcher_thread is None:
                return []
            return list(self.changed_files)
        return changes()
        

    @property
    def changed_files(self):
        return self._changed_files


def only_added_filter(change: Change, path: str, allowed_extensions: tuple[str]) -> bool:    
    return change == Change.added and path.endswith(allowed_extensions)


def only_added_pdfs(change: Change, path: str) -> bool:
    return only_added_filter(change, path, (".pdf",))


def only_added_tex(change: Change, path: str) -> bool:
    return only_added_filter(change, path, (".tex",))


async def directory_watcher(directory: Path, changed_files: list[Path], lock: threading.Lock, filter: Callable | None = None):
    """
    Asynchronously watches the given directory for file changes.
    Each detected change is appended to the global changed_files list.
    """
    async for changes in awatch(directory, recursive=True, watch_filter=filter):
        logger.info(f"Changes: {changes}")
        
        with lock:
            for change_type, file_path in changes:
                changed_files.append(Path(file_path))
                print(f"Detected change in: {file_path}")


def run_async_watcher(directory: Path, changed_files: list[Path], lock: threading.Lock, filter: Callable | None = None):
    """
    Runs the asynchronous directory watcher inside an asyncio event loop.
    """
    asyncio.run(directory_watcher(directory, changed_files, lock, filter))
    

def make_serializable(structure: dict[str, Any]) -> dict[str, Any]:
        """
        Convert complex objects to JSON-serializable format
        
        Args:
            structure (dict): Original structure to be serialized
        
        Returns:
            dict: Serializable version of the structure
        """
        def serialize_value(value):
            if isinstance(value, datetime):
                return value.isoformat()
            return value
        
        return {k: serialize_value(v) for k, v in structure.items()}


def find_directories_or_files_with_extension(directory: Path, extension: str | None = None) -> list[Path]:
    """
    Find all directories or files with a particular extension from a directory
    
    Args:
        directory (Path): Starting directory to search
        extension (str, optional): File extension or directory name extension to be searched. Defaults to None.
    
    Returns:
        list: List of absolute root paths of directories or files found
    """
    import os
    from glob import glob

    if extension is None:
        return [p for p in directory.rglob('*/') if p.is_dir()]

    files = []
    for path in glob(f"{directory}/**/*{extension}", recursive=True):
        files.append(Path(os.path.abspath(path)))

    return files


def read_text_file(file_path: Path) -> str:
    """
    Reads the contents of a text file
    
    Args:
        file_path (Path): Path to the text file
    
    Returns:
        str: Contents of the text file
    """
    try:
        with open(file_path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}"


def save_text_file(file_path: Path, content: str, overwrite: bool = True) -> Path:
    """
    Save the content in a text file. If the file already exists, it will be overwritten if overwrite is True.
    
    Args:
        file_path (Path): Path to the text file.
        content (str): Content to be written to the file.
        overwrite (bool, optional): If True, the file will be overwritten if it exists. Defaults to True.
    
    Returns:
        Path: Path of the saved file.
    """
    # Ensure the parent directory exists.
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 'w' overwrites or creates the file; 'x' only creates the file if it doesn't exist.
    mode = 'w' if overwrite or not file_path.exists() else 'x'
    
    with file_path.open(mode) as f:
        f.write(content)
        
    return file_path


def build_target_dir_structure(pydantic_cached_job: JobDetails, basedir: Path):
    # Create a unique dir structure based on the job title and timestamp
    now = datetime.now()
    timestamp_str = now.strftime("%Y_%m_%d_%H_%M_%S")
    file_prefix = pydantic_cached_job.generate_filename_prefix() + "_" + timestamp_str
    target_dir = os.path.join(basedir, 'generated_cvs', file_prefix)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        logger.info(f"Target directory created: {target_dir}")

    return target_dir
