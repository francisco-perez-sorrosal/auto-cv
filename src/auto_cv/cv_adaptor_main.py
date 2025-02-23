from auto_cv.cv_adaptor_crew import CVAdaptorCrew

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        "original_cv": "/Users/fperez/dev/auto-cv/docs/2025_FranciscoPerezSorrosal_CV_English.tex",
        "target_dir": "/Users/fperez/dev/auto-cv/docs/generated-cvs",
        "filename_prefix": "2025_FranciscoPerezSorrosal_CV_English"
    }
    return CVAdaptorCrew().crew().kickoff(inputs=inputs)
