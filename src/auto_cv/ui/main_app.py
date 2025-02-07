import streamlit as st
import json
from auto_cv.agents.web_scraper import JobPostingExtractor
from auto_cv.crews import JobDescriptionExtractorCrew
from auto_cv.data_models import JobDetails

from llm_foundation import logger

# Predefined example LinkedIn job URLs
EXAMPLE_URLS = {
    "Select an example URL": "",
    "Amazon test": "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=3959722886",
    "Software Engineer - AI/ML at TechCorp": "https://www.linkedin.com/jobs/view/software-engineer-ai-ml-at-3959722886/",
}

def extract_job_description(url):
    """
    Extract job description using the JobDescriptionExtractorCrew
    
    Args:
        url (str): URL of the job posting
    
    Returns:
        dict: Extracted job details
    """
    try:
        # Initialize the crew
        crew = JobDescriptionExtractorCrew()
        
        # Kickoff the crew with the URL
        result = crew.crew().kickoff(inputs={"url": url})
        
        return result
    except Exception as e:
        st.error(f"Error extracting job description: {e}")
        return None

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
            height=400,  # Adjust height as needed
            disabled=True  # Make it read-only
        )
    
    with col2:
        st.subheader("Formatted Description")
        st.markdown(job_details.markdown_description or "No formatted description available")

def main():
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
            # Show loading spinner
            with st.spinner('Extracting job details...'):
                # Extract job details
                job_details = extract_job_description(url)
            
            # Display results
            if job_details:
                st.success("Job description extracted successfully!")
                
                # Display raw JSON
                with st.expander("Raw JSON"):
                    st.json(job_details)
                    
                if job_details.json_dict:
                    from datetime import datetime
                    # When displaying JSON
                    def json_serial(obj):
                        """Custom JSON serializer for datetime objects"""
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        raise TypeError(f"Type {type(obj)} not serializable")
                        
                    with st.expander("Dumped JSON"):
                        json_output = json.dumps(job_details.json_dict, indent=2, default=json_serial)
                        st.warning(f"JSON Output: {json_output}")
                    
                    job_details_pydantic = JobDetails.model_validate(job_details.json_dict)
                                    
                    # Display job stuff
                    display_job_basics(job_details_pydantic)
                    display_job_descriptions(job_details_pydantic)
                    
            else:
                st.error("Failed to extract job details.")
        else:
            st.warning("Please enter a valid URL")

if __name__ == "__main__":
    main()