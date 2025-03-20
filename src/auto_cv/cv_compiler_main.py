import sys
from auto_cv.cv_compiler_crew import CVCompilerCrew

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        "document": "/Users/fperez/dev/auto-cv/docs/2025_FranciscoPerezSorrosal_CV_English.tex",
    }
    CVCompilerCrew().crew().kickoff(inputs=inputs)
