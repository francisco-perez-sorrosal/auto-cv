from datetime import datetime
import json
from typing import Any, Tuple

from llm_foundation import logger
import streamlit as st

from auto_cv.cache import BasicInMemoryCache
from auto_cv.crews import JobDescriptionExtractorCrew
from auto_cv.data_models import JobDetails
from auto_cv.utils import make_serializable

# Set page configuration to wide mode by default
st.set_page_config(page_title="Auto CV Job Description Extractor", layout="wide")

# Predefined example LinkedIn job URLs
EXAMPLE_URLS = {
    "Select an example URL": "",
    "Amazon test": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3959722886",
    "Amazon Test 2": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4070067137",
}

extracted_job_description_cache = BasicInMemoryCache(
    app_name="auto-cv", 
    cache_subdir="extracted_job_descriptions_cache", 
    cache_file="extracted_job_descriptions.jsonl", 
    cache_key_name="url"
)

def extract_job_description_from_raw(url: str) -> dict[str, Any]:
    """
    Extract job description using the JobDescriptionExtractorCrew
    
    Args:
        url (str): URL of the job posting
    
    Returns:
        Dictionary of job details (empty if extraction fails)
    """
    
    try:
        # Initialize the crew
        crew = JobDescriptionExtractorCrew()
        
        # Kickoff the crew with the URL
        job_details = crew.crew().kickoff(inputs={"url": url})
        if job_details.json_dict:
            return job_details.json_dict
        st.warning(f"No job details found in crew response")
        return {}
    except Exception as e:
        st.error(f"Error extracting job description: {e}")
        return {}

def display_job_basics(job_details: JobDetails):
    """
    Format job details for display
    
    Args:
        job_details (dict): Extracted job details
    
    Returns:
        str: Formatted markdown text
    """
    if not job_details:
        return "No job details found."
    
    print(f"Formatting job details:\n{type(job_details)}")
    
    # Create a formatted markdown representation
    formatted_text = f"""
## Job Details

### Basic Information
- **URL**: {job_details.url}
- **Job Title (Job Id)**: {job_details.title} ({job_details.job_id})
- **Company Name**: {job_details.company}
- **Location**: {job_details.location}
- **Salary**: {job_details.salary}
""" 
    st.markdown(formatted_text)

def display_job_descriptions(job_details: JobDetails):
    """
    Display job details with side-by-side raw and markdown descriptions
    
    Args:
        job_details (JobDetails): Pydantic model of job details
    """
    # Create two columns for side-by-side display
    col1, col2 = st.columns([2,1])
    
    with col1:
        st.subheader("Raw Description")
        st.text_area(
            label="Raw Job Description", 
            value=job_details.raw_description or "No raw description available", 
            height=800,  # Adjust height as needed
            disabled=True  # Make it read-only
        )
    
    with col2:
        st.subheader("Formatted Description")
        st.markdown(job_details.markdown_description or "No formatted description available")

def main()-> None:
    st.title("Job Description Extractor")
    
    # Dropdown for example URLs
    selected_example = st.selectbox(
        "Choose an example job URL",
        list(EXAMPLE_URLS.keys())
    )
    
    # URL input with example URL pre-filled if selected
    url = st.text_input(
        "Or enter a custom Job Posting URL", 
        value=EXAMPLE_URLS[selected_example],
        placeholder="https://www.linkedin.com/jobs/view/..."
    )
    
    # Extract button
    if st.button("Extract Job Description"):
        if url:
            
            # Check cache first
            if extracted_job_description_cache.exists(url):
                job_details = extracted_job_description_cache.get(url)
                st.success(f"Retrieved previously extracted job description from cache: {url}")
            else:
                with st.spinner('Agent extracting job details...'):
                    # Extract job details
                    job_details = extract_job_description_from_raw(url)
            
            # Display results
            if job_details and job_details != {}:
                
                st.success("Job description extracted successfully!")
                
                job_details = make_serializable(job_details)
                with st.expander("Serializable JSON"):
                    st.json(job_details)

                extracted_job_description_cache_hit = extracted_job_description_cache.put(job_details)
                if extracted_job_description_cache_hit:
                    st.info(f"Job description with extractions from {url} added to cache")
                                                    
                job_details_pydantic = JobDetails.model_validate(job_details)
                                
                # Display job stuff
                display_job_basics(job_details_pydantic)
                display_job_descriptions(job_details_pydantic)
                    
            else:
                st.error("Failed to extract job details!!!")
        else:
            st.warning("Please enter a valid URL")

if __name__ == "__main__":
    main()
