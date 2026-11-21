import numpy as np
import pandas as pd

def enrich(df:pd.DataFrame)->pd.DataFrame:
    x=df.copy()
    for n in (9,21,50,100,200): x[f"sma_{n}"]=x.close.rolling(n).mean()
    delta=x.close.diff(); up=delta.clip(lower=0); down=-delta.clip(upper=0)
    rs=up.ewm(alpha=1/14,adjust=False).mean()/down.ewm(alpha=1/14,adjust=False).mean().replace(0,np.nan)
    x["rsi_14"]=100-(100/(1+rs))
    tr=pd.concat([(x.high-x.low),(x.high-x.close.shift()).abs(),(x.low-x.close.shift()).abs()],axis=1).max(axis=1)
    x["atr_14"]=tr.rolling(14).mean()
    x["ret"]=x.close.pct_change(); x["vol_20"]=x.ret.rolling(20).std()*np.sqrt(252)
    x["drawdown"]=x.close/x.close.cummax()-1
    x["volume_z"]=(x.volume-x.volume.rolling(20).mean())/x.volume.rolling(20).std()
    x["high_20"]=x.high.rolling(20).max(); x["low_20"]=x.low.rolling(20).min()
    return x
