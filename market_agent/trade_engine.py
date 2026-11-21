from dataclasses import dataclass,asdict
import math
from .indicators import enrich

@dataclass
class Scenario:
    horizon:str; direction:str; status:str; entry_low:float; entry_high:float
    stop:float; tp1:float; tp2:float; tp3:float; invalidation:str
    risk_reward:float|None; confidence:str; score:int; rationale:list[str]

def _rr(entry,stop,target):
    risk=abs(entry-stop); return round(abs(target-entry)/risk,2) if risk>0 else None

def analyze_horizon(data,horizon):
    x=enrich(data.frame).dropna().copy(); r=x.iloc[-1]
    price=float(r.close); atr=float(r.atr_14); trend=0
    trend += 1 if price>r.sma_21 else -1
    trend += 1 if r.sma_21>r.sma_50 else -1
    trend += 1 if price>r.sma_200 else -1
    momentum=1 if r.rsi_14>55 else (-1 if r.rsi_14<45 else 0)
    signal=trend+momentum
    direction="LONG" if signal>=3 else ("SHORT" if signal<=-3 else "WAIT")
    status="ACTIONABLE" if direction!="WAIT" else "NO TRADE"
    mult={"hourly":.35,"daily":.65,"weekly":1.2,"long_term":2.0}[horizon]
    if direction=="LONG":
        entry=(price-.25*atr,price+.10*atr); stop=price-mult*2*atr; targets=[price+mult*k*atr for k in (2,3.5,5)]
        invalidation=f"Close below {stop:.2f} or material thesis deterioration"
    elif direction=="SHORT":
        entry=(price-.10*atr,price+.25*atr); stop=price+mult*2*atr; targets=[price-mult*k*atr for k in (2,3.5,5)]
        invalidation=f"Close above {stop:.2f} or material thesis deterioration"
    else:
        entry=(price-atr,price+atr); stop=targets=[math.nan,math.nan,math.nan]
        invalidation="Wait for trend and momentum alignment"
    score=min(95,40+abs(signal)*12)
    conf="HIGH" if score>=76 else ("MODERATE" if score>=55 else "LOW")
    return Scenario(horizon,direction,status,*map(float,entry),float(stop) if direction!="WAIT" else math.nan,
                    *[float(v) for v in targets],invalidation,_rr(sum(entry)/2,stop,targets[0]) if direction!="WAIT" else None,
                    conf,score,[f"Trend score: {trend}",f"RSI(14): {r.rsi_14:.1f}",f"ATR(14): {atr:.2f}"])

def analyze_all(data_by_horizon):
    return {h:asdict(analyze_horizon(d,h)) for h,d in data_by_horizon.items()}
