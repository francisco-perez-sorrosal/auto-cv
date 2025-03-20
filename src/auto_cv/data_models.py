import json

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class JobDetails(BaseModel):
    """
    Pydantic model representing extracted job details from a job posting URL.
    
    Provides a structured and validated representation of job information.
    """
    url: str = Field(..., description="Full URL of the job posting")
    company: str = Field(..., description="Name of the company posting the job")
    title: str = Field(..., description="Title of the job position")
    raw_description: Optional[str] = Field(None, description="Original, unformatted job description")
    
    # Salary information
    salary: Optional[str] = Field("N/A", description="Salary or salary range for the position")
    
    # Job location    
    location: Optional[str] = Field("N/A", description="Geographic location of the job")
    
    # Hiring manager and job ID
    hiring_manager: Optional[str] = Field("N/A", description="Name of the hiring manager")
    job_id: Optional[str] = Field("N/A", description="ID of the job posting")

    # Job description with markdown format    
    markdown_description: Optional[str] = Field(None, description="Markdown formatted job description")
    
    # Metadata
    extracted_at: datetime = Field(default_factory=datetime.isoformat, description="Timestamp of job details extraction")
    # url_hash: str = Field(..., description="Hash of the job posting URL")
    
    # Additional metadata for flexibility
    # extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata or unstructured information")
    
    @field_validator('url')
    def validate_url(cls, v):
        """
        Validate that the URL is a non-empty string and looks like a valid URL.
        
        Args:
            v (str): URL to validate
        
        Returns:
            str: Validated URL
        
        Raises:
            ValueError: If URL is invalid
        """
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('URL must be a valid HTTP or HTTPS URL')
        return v
    
    # @field_validator('technical_skills', 'technology_stack', 'soft_skills', each_item=True)
    # def strip_skills(cls, v):
    #     """
    #     Clean and strip whitespace from skills.
        
    #     Args:
    #         v (str): Skill to clean
        
    #     Returns:
    #         str: Cleaned skill
    #     """
    #     return v.strip() if isinstance(v, str) else v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary, excluding None values.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the job details
        """
        return {k: v for k, v in self.model_dump().items() if v is not None}
    
    class DateTimeEncoder(json.JSONEncoder):
        """
        Custom JSON encoder to handle datetime serialization
        """
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    def to_json(self, **kwargs) -> str:
        """
        Convert the model to a JSON string.
        
        Args:
            **kwargs: Additional arguments to pass to json.dumps()
        
        Returns:
            str: JSON representation of the job details
        """
        return json.dumps(self.model_dump(), cls=DateTimeEncoder, **kwargs)
    
    @property
    def json_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary suitable for JSON serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the job details
        """
        return json.loads(self.to_json())
    
    def generate_filename_prefix(self) -> str:
        """
        Generate a filename prefix based on the job details.
        
        Returns:
            str: Filename prefix
        """
        return (
            f"{self.company.replace(',', '_').replace(' ', '_')}_" 
            f"{self.title.replace(',', '_').replace(' ', '_')}"
        )
    
    class Config:
        """Pydantic model configuration"""
        title = "Job Details"
        description = "Structured model for job posting details"
        extra = 'ignore'  # Ignore extra fields not defined in the model
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "url": "https://www.linkedin.com/jobs/view/example-job",
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "salary": "$150,000 - $180,000 per year"
            }
        }

class LatexContent(BaseModel):
    """
    Pydantic model representing the structure of a latex document.
    """
    content: str = Field(..., description="content of the latex document as string")


class AdaptorProject(BaseModel):
    """
    Pydantic model representing information about a CV adaptation project.
    """
    project_dir: str = Field(..., description="Target directory for the adapted CV")
    source_cv_latex_filename: str = Field(..., description="Original content of the latex document to adapt")
    filename_prefix: str = Field(..., description="Prefix for the adapted CV filename")
    curated_job_description: str = Field(..., description="Curated job description")
    last_revision: int = Field(0, description="Last revision number")
