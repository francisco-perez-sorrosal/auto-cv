import os
from pathlib import Path

# WWW directory definition for static assets
DIR = os.path.dirname(os.path.abspath(__file__))
WWW = Path(DIR, "www")
CV_TEMPLATES = Path(WWW, "cv_templates")
DEFAULT_RAW_CV_TEMPLATE = "2025_FranciscoPerezSorrosal_CV_English.tex"
