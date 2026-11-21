from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import precision_score,recall_score
from .indicators import enrich

FACTORS=["trend_gap","momentum_20","volatility","drawdown","volume_z"]

def factor_frame(df):
    x=enrich(df).copy()
    x["trend_gap"]=x.close/x.sma_200-1
    x["momentum_20"]=x.close.pct_change(20)
    x["volatility"]=x.ret.rolling(20).std()*np.sqrt(252)
    # Target: a 10% maximum drawdown from today's close during the next 60 observations.
    future_min=x.close.iloc[::-1].rolling(60,min_periods=20).min().iloc[::-1]
    x["target"]=(future_min/x.close-1<=-.10).astype(int)
    return x.dropna(subset=FACTORS+["target"])

def detect_events(df,threshold=-.10):
    x=enrich(df); events=[]; in_event=False; peak=None
    for date,row in x.iterrows():
        dd=float(row.drawdown)
        if dd<=threshold and not in_event:
            in_event=True; events.append({"start":str(date.date()),"trigger_drawdown":dd})
        if in_event and dd>-0.03: in_event=False
    return events

def walk_forward(df,min_train=500,step=60):
    f=factor_frame(df); rows=[]
    if len(f)<min_train+step: return pd.DataFrame()
    for end in range(min_train,len(f)-step,step):
        train=f.iloc[:end]; test=f.iloc[end:end+step]
        if train.target.nunique()<2: continue
        model=make_pipeline(StandardScaler(),LogisticRegression(class_weight="balanced",max_iter=1000))
        model.fit(train[FACTORS],train.target)
        p=model.predict_proba(test[FACTORS])[:,1]
        rows.append(pd.DataFrame({"actual":test.target,"probability":p},index=test.index))
    return pd.concat(rows) if rows else pd.DataFrame()

def analyze_crash_risk(df):
    f=factor_frame(df); latest=f.iloc[-1]
    hist=f.iloc[:-1]
    percentile=lambda col,val: float((hist[col]<=val).mean()) if len(hist) else .5
    components={
      "trend":1-percentile("trend_gap",latest.trend_gap),
      "momentum":1-percentile("momentum_20",latest.momentum_20),
      "volatility":percentile("volatility",latest.volatility),
      "drawdown":1-percentile("drawdown",latest.drawdown),
      "volume":percentile("volume_z",latest.volume_z),
    }
    structural=round(100*(.30*components["trend"]+.20*components["momentum"]+.20*components["volatility"]+.15*components["drawdown"]+.15*components["volume"]))
    pressure=round(100*(.35*components["momentum"]+.30*components["volatility"]+.20*components["drawdown"]+.15*components["volume"]))
    score=round(.6*structural+.4*pressure)
    level="GREEN" if score<=20 else "YELLOW" if score<=40 else "ORANGE" if score<=60 else "RED" if score<=80 else "BLACK"
    wf=walk_forward(df)
    validation={"observations":int(len(wf))}
    if len(wf):
        pred=(wf.probability>=.5).astype(int)
        validation.update({"precision":round(precision_score(wf.actual,pred,zero_division=0),3),"recall":round(recall_score(wf.actual,pred,zero_division=0),3),"false_positives":int(((pred==1)&(wf.actual==0)).sum())})
    z=((hist[FACTORS]-hist[FACTORS].mean())/hist[FACTORS].std()).fillna(0)
    current=((latest[FACTORS]-hist[FACTORS].mean())/hist[FACTORS].std()).fillna(0)
    dist=((z-current)**2).mean(axis=1).pow(.5)
    analogs=[{"date":str(i.date()),"similarity":round(float(1/(1+d)),3)} for i,d in dist.nsmallest(5).items()]
    return {"crash_risk_score":score,"warning_level":level,"structural_vulnerability":structural,
            "immediate_downside_pressure":pressure,"risk_components":components,
            "validation":validation,"historical_analogs":analogs,"events_detected":detect_events(df),
            "disclaimer":"Risk classification is probabilistic, not a prediction of an exact crash date or magnitude."}
