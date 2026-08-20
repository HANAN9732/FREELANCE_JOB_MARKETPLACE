from pydantic import BaseModel


class JobSkillResponse(BaseModel):
    job_id: str
    skill_id: str

    model_config = {
        "from_attributes": True
    }