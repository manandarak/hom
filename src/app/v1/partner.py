from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db

# --- NEW IMPORTS FOR SECURITY ---
from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.services.permission_service import PermissionService
# --------------------------------

from src.app.models.partner import SuperStockist, Distributor, Retailer
from src.app.schemas.partner import (
    SuperStockistCreate, SuperStockistRead, SuperStockistUpdate,
    DistributorCreate, DistributorRead, DistributorUpdate,
    RetailerCreate, RetailerRead, RetailerUpdate
)
from src.app.crud.partner import (
    create_super_stockist, create_distributor, create_retailer
)

router = APIRouter()


# ==========================================
# SUPER STOCKISTS
# ==========================================
@router.post("/super-stockists", response_model=SuperStockistRead, status_code=status.HTTP_201_CREATED)
def add_super_stockist(ss_in: SuperStockistCreate, db: Session = Depends(get_db)):
    return create_super_stockist(db, ss_in)


@router.get("/super-stockists", response_model=list[SuperStockistRead])
def list_super_stockists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Securely scoped Super Stockist fetch."""
    query = db.query(SuperStockist)

    if not current_user.role: return []
    if current_user.role.name == "Admin": return query.all()

    # Partners only see themselves
    if current_user.role.name == "SuperStockist":
        return query.filter(SuperStockist.user_id == current_user.id).all()
    elif current_user.role.name in ["Distributor", "Retailer"]:
        return []

    # Internal Teams
    scope = PermissionService.get_geo_scope(current_user)
    if scope and "id" not in scope:
        for key, value in scope.items():
            if hasattr(SuperStockist, key) and value is not None:
                query = query.filter(getattr(SuperStockist, key) == value)
            else:
                return []  # Fail-Closed if scope doesn't apply
        return query.all()

    return []


@router.patch("/super-stockists/{ss_id}", response_model=SuperStockistRead)
def update_super_stockist(ss_id: int, ss_in: SuperStockistUpdate, db: Session = Depends(get_db)):
    db_ss = db.query(SuperStockist).filter(SuperStockist.id == ss_id).first()
    if not db_ss:
        raise HTTPException(status_code=404, detail="Super Stockist not found")

    update_data = ss_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ss, key, value)
    db.commit()
    db.refresh(db_ss)
    return db_ss


@router.delete("/super-stockists/{ss_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_super_stockist(ss_id: int, db: Session = Depends(get_db)):
    db_ss = db.query(SuperStockist).filter(SuperStockist.id == ss_id).first()
    if not db_ss:
        raise HTTPException(status_code=404, detail="Super Stockist not found")
    db_ss.is_active = False
    db.commit()
    return None


# ==========================================
# DISTRIBUTORS
# ==========================================
@router.post("/distributors", response_model=DistributorRead, status_code=status.HTTP_201_CREATED)
def add_distributor(dist_in: DistributorCreate, db: Session = Depends(get_db)):
    return create_distributor(db, dist_in)


@router.get("/distributors", response_model=list[DistributorRead])
def list_distributors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Securely scoped Distributor fetch."""
    query = db.query(Distributor)

    if not current_user.role: return []
    if current_user.role.name == "Admin": return query.all()

    if current_user.role.name == "Distributor":
        return query.filter(Distributor.user_id == current_user.id).all()
    elif current_user.role.name == "Retailer":
        return []

    # Internal Teams & Higher Partners (like SS viewing downstream)
    scope = PermissionService.get_geo_scope(current_user)
    if scope and "id" not in scope:
        for key, value in scope.items():
            if hasattr(Distributor, key) and value is not None:
                query = query.filter(getattr(Distributor, key) == value)
            else:
                return []  # Fail-Closed
        return query.all()

    return []


@router.patch("/distributors/{dist_id}", response_model=DistributorRead)
def update_distributor(dist_id: int, dist_in: DistributorUpdate, db: Session = Depends(get_db)):
    db_dist = db.query(Distributor).filter(Distributor.id == dist_id).first()
    if not db_dist:
        raise HTTPException(status_code=404, detail="Distributor not found")

    update_data = dist_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dist, key, value)
    db.commit()
    db.refresh(db_dist)
    return db_dist


@router.delete("/distributors/{dist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_distributor(dist_id: int, db: Session = Depends(get_db)):
    db_dist = db.query(Distributor).filter(Distributor.id == dist_id).first()
    if not db_dist:
        raise HTTPException(status_code=404, detail="Distributor not found")
    db_dist.is_active = False
    db.commit()
    return None


# ==========================================
# RETAILERS
# ==========================================
@router.post("/retailers", response_model=RetailerRead, status_code=status.HTTP_201_CREATED)
def add_retailer(ret_in: RetailerCreate, db: Session = Depends(get_db)):
    return create_retailer(db, ret_in)


@router.get("/retailers", response_model=list[RetailerRead])
def list_retailers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Securely scoped Retailer fetch."""
    query = db.query(Retailer)

    if not current_user.role: return []
    if current_user.role.name == "Admin": return query.all()

    if current_user.role.name == "Retailer":
        return query.filter(Retailer.user_id == current_user.id).all()

    # Internal Teams & Higher Partners (SS, Dist) viewing downstream
    scope = PermissionService.get_geo_scope(current_user)
    if scope and "id" not in scope:
        for key, value in scope.items():
            if hasattr(Retailer, key) and value is not None:
                query = query.filter(getattr(Retailer, key) == value)
            else:
                return []  # Fail-Closed
        return query.all()

    return []


@router.patch("/retailers/{ret_id}", response_model=RetailerRead)
def update_retailer(ret_id: int, ret_in: RetailerUpdate, db: Session = Depends(get_db)):
    db_ret = db.query(Retailer).filter(Retailer.id == ret_id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retailer not found")

    update_data = ret_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ret, key, value)
    db_ret.is_active = False
    db.refresh(db_ret)
    return db_ret


@router.delete("/retailers/{ret_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_retailer(ret_id: int, db: Session = Depends(get_db)):
    db_ret = db.query(Retailer).filter(Retailer.id == ret_id).first()
    if not db_ret:
        raise HTTPException(status_code=404, detail="Retailer not found")
    db.delete(db_ret)
    db.commit()
    return None