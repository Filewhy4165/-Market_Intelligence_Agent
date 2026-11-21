from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import requests

@dataclass
class MarketData:
    symbol: str
    asset_class: str
    timeframe: str
    frame: pd.DataFrame
    source: str
    timestamp: datetime
    delayed: bool
    synthetic: bool = False

    def validate(self) -> None:
        required={"open","high","low","close","volume"}
        missing=required-set(self.frame.columns)
        if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
        if self.frame.empty: raise ValueError("No market data returned")
        if not self.frame.index.is_monotonic_increasing: self.frame.sort_index(inplace=True)

class DemoProvider:
    def fetch(self, symbol:str, asset_class:str, timeframe:str="daily", bars:int=1500)->MarketData:
        seed=abs(hash((symbol,asset_class,timeframe)))%(2**32)
        rng=np.random.default_rng(seed)
        freq={"hourly":"h","daily":"B","weekly":"W-FRI","long_term":"W-FRI"}.get(timeframe,"B")
        idx=pd.date_range(end=pd.Timestamp.now(tz="UTC").floor("h"),periods=bars,freq=freq)
        # deterministic regime changes and shocks for exercising crash logic
        drift=np.r_[np.full(bars//3,.0004),np.full(bars//3,.0001),np.full(bars-2*(bars//3),.00025)]
        vol=np.r_[np.full(bars//2,.009),np.full(bars-bars//2,.014)]
        ret=drift+rng.normal(0,vol,bars)
        for p in [int(bars*.38),int(bars*.72),int(bars*.88)]:
            ret[p:min(p+8,bars)] += rng.normal(-.018,.012,min(8,bars-p))
        close=100*np.exp(np.cumsum(ret)); spread=np.abs(rng.normal(.006,.003,bars))
        open_=close*(1+rng.normal(0,.002,bars)); high=np.maximum(open_,close)*(1+spread)
        low=np.minimum(open_,close)*(1-spread); volume=rng.lognormal(15,0.35,bars)
        frame=pd.DataFrame({"open":open_,"high":high,"low":low,"close":close,"volume":volume},index=idx)
        out=MarketData(symbol,asset_class,timeframe,frame,"DEMO SYNTHETIC DATA",datetime.now(timezone.utc),False,True)
        out.validate(); return out

class AlphaVantageProvider:
    BASE="https://www.alphavantage.co/query"
    def __init__(self,key:str):
        if not key: raise ValueError("ALPHA_VANTAGE_API_KEY is required")
        self.key=key
    def fetch(self,symbol:str,asset_class:str,timeframe:str="daily",bars:int=1500)->MarketData:
        if asset_class=="forex":
            base,quote=symbol.replace("/","")[:3],symbol.replace("/","")[3:]
            params={"function":"FX_DAILY","from_symbol":base,"to_symbol":quote,"outputsize":"full","apikey":self.key}
        else:
            function="TIME_SERIES_INTRADAY" if timeframe=="hourly" else "TIME_SERIES_DAILY_ADJUSTED"
            params={"function":function,"symbol":symbol,"outputsize":"full","apikey":self.key}
            if timeframe=="hourly": params["interval"]="60min"
        payload=requests.get(self.BASE,params=params,timeout=30).json()
        key=next((k for k in payload if "Time Series" in k),None)
        if not key: raise RuntimeError(payload.get("Note") or payload.get("Error Message") or "Unexpected provider response")
        frame=pd.DataFrame.from_dict(payload[key],orient="index").astype(float)
        frame.columns=[c.split(". ")[-1].replace("adjusted ","") for c in frame.columns]
        if "volume" not in frame: frame["volume"]=0.0
        frame.index=pd.to_datetime(frame.index,utc=True); frame=frame.sort_index().tail(bars)
        out=MarketData(symbol,asset_class,timeframe,frame[["open","high","low","close","volume"]],"Alpha Vantage",datetime.now(timezone.utc),True)
        out.validate(); return out

def get_provider():
    if os.getenv("DATA_PROVIDER","demo").lower()=="alpha_vantage":
        return AlphaVantageProvider(os.getenv("ALPHA_VANTAGE_API_KEY",""))
    return DemoProvider()
