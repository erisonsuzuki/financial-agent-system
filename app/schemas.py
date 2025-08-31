from pydantic import BaseModel, ConfigDict
from app.models import AssetType
    
class AssetBase(BaseModel):
    ticker: str
    name: str
    asset_type: AssetType
    sector: str | None = None

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
