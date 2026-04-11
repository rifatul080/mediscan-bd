from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id            = Column(Integer, primary_key=True, index=True)
    brand_name    = Column(String, nullable=False, index=True)
    generic_name  = Column(String, nullable=True)
    manufacturer  = Column(String, nullable=True)
    strength      = Column(String, nullable=True)
    form          = Column(String, nullable=True)
    unit_price    = Column(Float,  nullable=True)
    pack_size     = Column(Integer, nullable=True)
    barcode       = Column(String, nullable=True, index=True)
    source        = Column(String, nullable=True)
    last_updated  = Column(String, nullable=True)
    image_url     = Column(Text,   nullable=True)

    def __repr__(self):
        return f"<Medicine {self.brand_name} {self.strength}>"