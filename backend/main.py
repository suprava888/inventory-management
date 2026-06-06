import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from pydantic import BaseModel, ConfigDict

load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None
Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    items = relationship("InventoryItem", back_populates="category", cascade="all, delete-orphan")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False, default=0.0)
    sku = Column(String(64), nullable=True, unique=True, index=True)
    status = Column(String(40), nullable=False, default="In Stock")
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    category = relationship("Category", back_populates="items")


app = FastAPI(title="Inventory Management API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(CategoryCreate):
    pass


class CategoryOut(CategoryCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ItemCreate(BaseModel):
    name: str
    category_id: Optional[int] = None
    quantity: int = 0
    price: float = 0.0
    sku: Optional[str] = None
    status: str = "In Stock"


class ItemUpdate(ItemCreate):
    pass


class ItemOut(ItemCreate):
    id: int
    category_name: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured. Add your Supabase connection string to backend/.env.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup():
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass


@app.get("/api")
def api_root():
    return {
        "message": "Inventory API is running",
        "endpoints": [
            "/api/health",
            "/api/stats",
            "/api/categories",
            "/api/items"
        ],
        "database_url_configured": bool(DATABASE_URL),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "database_url_configured": bool(DATABASE_URL)}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    total_items = db.query(func.count(InventoryItem.id)).scalar() or 0
    total_units = db.query(func.sum(InventoryItem.quantity)).scalar() or 0
    stock_value = db.query(func.sum(InventoryItem.quantity * InventoryItem.price)).scalar() or 0.0
    total_categories = db.query(func.count(Category.id)).scalar() or 0
    low_stock = db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == "Low Stock").scalar() or 0
    out_of_stock = db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == "Out of Stock").scalar() or 0
    return {
        "total_items": total_items,
        "total_units": int(total_units),
        "stock_value": round(float(stock_value), 2),
        "total_categories": total_categories,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
    }


@app.get("/api/categories", response_model=list[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@app.post("/api/categories", response_model=CategoryOut)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    try:
        record = Category(name=category.name, description=category.description)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category name already exists") from exc


@app.put("/api/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    record = db.query(Category).filter(Category.id == category_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Category not found")
    record.name = category.name
    record.description = category.description
    db.commit()
    db.refresh(record)
    return record


@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    record = db.query(Category).filter(Category.id == category_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(record)
    db.commit()
    return {"message": "Category deleted"}


@app.get("/api/items", response_model=list[ItemOut])
def list_items(
    q: Optional[str] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(InventoryItem).join(Category, InventoryItem.category_id == Category.id, isouter=True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(InventoryItem.name.ilike(like), InventoryItem.sku.ilike(like)))
    if category_id is not None:
        query = query.filter(InventoryItem.category_id == category_id)
    items = query.order_by(InventoryItem.created_at.desc()).all()
    result = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "quantity": item.quantity,
                "price": item.price,
                "sku": item.sku,
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
        )
    return result


@app.post("/api/items", response_model=ItemOut)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    try:
        record = InventoryItem(**item.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "id": record.id,
            "name": record.name,
            "category_id": record.category_id,
            "category_name": record.category.name if record.category else None,
            "quantity": record.quantity,
            "price": record.price,
            "sku": record.sku,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate SKU or invalid category") from exc


@app.put("/api/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    record = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.model_dump().items():
        setattr(record, key, value)
    try:
        db.commit()
        db.refresh(record)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate SKU or invalid category") from exc
    return {
        "id": record.id,
        "name": record.name,
        "category_id": record.category_id,
        "category_name": record.category.name if record.category else None,
        "quantity": record.quantity,
        "price": record.price,
        "sku": record.sku,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    record = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(record)
    db.commit()
    return {"message": "Item deleted"}
