from dataclasses import dataclass
from typing import Optional

@dataclass
class SymbolMeta:
    symbol: str
    status: str
    quote_asset: str
    tick_size: float
    step_size: float

@dataclass
class StructureResult:
    latest_swing_high: Optional[float]
    latest_swing_low: Optional[float]
    previous_swing_high: Optional[float]
    previous_swing_low: Optional[float]
    trend_label: str

@dataclass
class BreakoutResult:
    state: str
    level: Optional[float]
    direction: Optional[str]

@dataclass
class AVPResult:
    anchor_index: int
    poc: float
    vah: float
    val: float
    bias: str

@dataclass
class RecommendationResult:
    status: str
    entry_text: str
    sl: Optional[float]
    tp1: Optional[float]
    tp2: Optional[float]
    tp3: Optional[float]
    confidence: str
    note: str

@dataclass
class MTFResult:
    macro_tf: str
    macro_trend: str
    macro_bias: str
    micro_tf: str
    micro_trend: str
    micro_bias: str
    confluence: str
