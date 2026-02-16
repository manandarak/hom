from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.app.models.product import ProductMaster
from src.app.schemas.product import ProductCreate, ProductResponse
from src.app.core.database import get_db
from src.app.schemas.product import ProductUpdate
from fastapi import status

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        db_product = ProductMaster(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")


@router.get("/", response_model=list[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(ProductMaster).all()


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(ProductMaster).filter(ProductMaster.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update only the fields that were provided in the request
    update_data = product_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Soft delete a product by setting is_active to False"""
    db_product = db.query(ProductMaster).filter(ProductMaster.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_product.is_active = False
    db.commit()
    return None