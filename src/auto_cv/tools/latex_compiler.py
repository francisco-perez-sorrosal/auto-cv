import os
from pathlib import Path
import subprocess
from crewai.tools import BaseTool

from llm_foundation import logger

class LatexCompilerTool(BaseTool):
    name: str = "Latex Compiler Tool"
    description: str = "Compile a latex-based document."
        
    def _run(self, document_path: str) -> str:
        """
        Compile a latex-based document.
        
        Args:
            document_path (str): Path to the document to compile.
        
        Returns:
            str: the path of the directory where the document was compiled.
        """
        logger.info(f"Compiling latex document from path {document_path}")
        # document_path: Path = (Path(__file__).parent.parent.parent.parent / document_path)
        document_as_path: Path = Path(document_path)
        logger.info(f"Compiling latex document {document_as_path} from {os.getcwd()}")
        command = ["pdflatex", 
                              "-synctex=1", 
                              "-interaction=nonstopmode", 
                              "-file-line-error", 
                              "-output-directory", 
                              str(document_as_path.parent),
                              "-recorder", 
                              str(document_as_path)]
        logger.info(f"Compiling command {command}")
        
        process = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(stderr.decode())
            logger.error("Error compiling latex document")
            return ""
        logger.info(stdout.decode())
        new_file_path = document_as_path.with_suffix(".pdf")
        logger.info(f"New file path {new_file_path}")
        return str(new_file_path)
        