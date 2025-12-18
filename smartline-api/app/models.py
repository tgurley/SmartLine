from pydantic import BaseModel
from typing import Optional

class StrategyFilters(BaseModel):
    side: Optional[str] = None
    spread_min: Optional[float] = None
    spread_max: Optional[float] = None
    movement_signal: Optional[str] = None
    injury_diff_min: Optional[int] = None
    injury_diff_max: Optional[int] = None
    book: Optional[str] = None

class StrategyRequest(BaseModel):
    name: str
    filters: StrategyFilters
    stake: float = 100.0
