from pydantic import BaseModel, Field


class ProfileLinks(BaseModel):
    github: str
    linkedin: str


class ProfileCoreSkills(BaseModel):
    languages_and_frameworks: list[str] = Field(default_factory=list)
    databases_and_tools: list[str] = Field(default_factory=list)
    testing_and_devops: list[str] = Field(default_factory=list)
    development_practices: list[str] = Field(default_factory=list)


class ProfileExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    description: str


class ProfileEducation(BaseModel):
    degree: str
    institution: str
    location: str
    graduation_date: str


class ProfileTrainingCertification(BaseModel):
    name: str
    provider: str
    duration: str


class UserProfileCreateRequest(BaseModel):
    full_name: str
    title: str
    location: str
    phone: str
    email: str
    links: ProfileLinks
    professional_summary: str
    core_skills: ProfileCoreSkills
    professional_experience: list[ProfileExperienceItem] = Field(default_factory=list)
    education: ProfileEducation
    training_and_certifications: list[ProfileTrainingCertification] = Field(default_factory=list)


class UserProfileCreateResponse(BaseModel):
    id: str
    message: str


class UserProfileUpdateResponse(BaseModel):
    id: str
    message: str
