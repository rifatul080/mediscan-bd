from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class MedicineChaldal(Base):
    __tablename__ = "medicines_chaldal"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, index=True)
    price       = Column(Float, nullable=True)
    unit        = Column(String, nullable=True)
    category    = Column(String, nullable=True)
    image_url   = Column(String, nullable=True)
    product_url = Column(String, nullable=True)
    source      = Column(String, default='chaldal')