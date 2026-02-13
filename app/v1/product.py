from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.app.models.product import ProductMaster  # Adjust import based on your actual structure
from src.app.schemas.product import ProductCreate, ProductResponse
# Assuming you have a dependency to get the database session
from src.app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        db_product = ProductMaster(**product.model_dump()) # use .dict() if Pydantic v1
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")