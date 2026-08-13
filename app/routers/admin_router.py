from fastapi import APIRouter, Depends

from app.models.user import User
from app.core.dependencies import require_admin


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Welcome to the admin dashboard",
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role
    }