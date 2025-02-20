import os
from pathlib import Path
import subprocess
from crewai.tools import BaseTool

from llm_foundation import logger

class LatexCompilerTool(BaseTool):
    name: str = "Latex Compiler Tool"
    description: str = "Compile a latex-based document."
        
    def _run(self, document: str = "2025_FranciscoPerezSorrosal_CV_English.tex") -> bool:
        """
        Compile a latex-based document.
        """
        document_path = (Path(__file__).parent.parent.parent.parent / "docs" / document).resolve()
        print(f"Compiling document {document} from {document_path}")
        logger.info(f"Compiling latex document {document_path} from {os.getcwd()}")
        command = ["pdflatex", 
                              "-synctex=1", 
                              "-interaction=nonstopmode", 
                              "-file-line-error", 
                              "-output-directory", 
                              str(document_path.parent),
                              "-recorder", 
                              document_path]
        process = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(stderr.decode())
            logger.error("Error compiling latex document")
            return False
        logger.info(stdout.decode())
        return True
        