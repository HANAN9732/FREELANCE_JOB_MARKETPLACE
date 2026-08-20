from pydantic import BaseModel


class UserSkillResponse(BaseModel):
    user_id: str
    skill_id: str

    model_config = {
        "from_attributes": True
    }