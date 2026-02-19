from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

from src.app.models.user import User
from src.app.schemas.user import UserCreate, UserRead, UserUpdate
from src.app.crud.user import create_user
from src.app.core.security import check_permissions
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

from src.app.models.user import User, Role
from src.app.schemas.user import (
    UserCreate, UserRead, UserUpdate,
    RoleCreate, RoleRead, RolePermissionUpdate, PermissionRead
)
from src.app.crud.user import (
    create_user, create_role, get_all_permissions, update_role_permissions
)
from src.app.core.security import check_permissions

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_new_user(
        user_in: UserCreate,
        db: Session = Depends(get_db),
        # Uncomment to restrict to admins: _=Depends(check_permissions("manage_users"))
):
    return create_user(db, user_in)


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    """Fetch all users (ZSM, RSM, ASM, SO, etc.)"""
    return db.query(User).all()


@router.patch("/{user_id}", response_model=UserRead)
def edit_user(
        user_id: int,
        user_in: UserUpdate,
        db: Session = Depends(get_db)
):
    """Update a user's role, active status, or geographical assignment"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    SOFT DELETE: We never hard-delete employees because their ID is tied to
    historical orders and ledger entries. We just deactivate their login access.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = False
    db.commit()
    return None

@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def add_new_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions("manage_roles"))
):
    """Admin creates a new role type (e.g. 'Auditor', 'Finance')."""
    return create_role(db, role_in)

@router.get("/roles", response_model=list[RoleRead])
def list_roles_and_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions("manage_roles"))
):
    """View all roles and the permissions currently assigned to them."""
    return db.query(Role).all()

@router.get("/permissions", response_model=list[PermissionRead])
def list_available_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions("manage_roles"))
):
    """View all system actions that can be assigned."""
    return get_all_permissions(db)

@router.put("/roles/{role_id}/permissions", response_model=RoleRead)
def modify_role_permissions(
    role_id: int,
    perm_in: RolePermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permissions("manage_roles"))
):
    """Admin dynamically updates what a specific Role is allowed to do."""
    try:
        role = update_role_permissions(db, role_id, perm_in.permission_ids)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except ValueError as e:
        # This catches the Guardrail restriction (e.g. assigning admin rights to an SO)
        raise HTTPException(status_code=403, detail=str(e))