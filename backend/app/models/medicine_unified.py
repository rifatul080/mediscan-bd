from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class MedicineUnified(Base):
    __tablename__ = "medicines_unified"

    id           = Column(Integer, primary_key=True, index=True)
    source_id    = Column(Integer)
    source       = Column(String, index=True)
    brand_name   = Column(String, index=True)
    generic_name = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    strength     = Column(String, nullable=True)
    form         = Column(String, nullable=True)
    unit_price   = Column(Float,  nullable=True)
    unit         = Column(String, nullable=True)
    category     = Column(String, nullable=True)
    image_url    = Column(String, nullable=True)
    product_url  = Column(String, nullable=True)