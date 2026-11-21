from datetime import datetime,timezone
from .trade_engine import analyze_all
from .crash_engine import analyze_crash_risk

def build_report(symbol,asset_class,data):
    scenarios=analyze_all(data)
    daily=data["daily"]
    return {"instrument":symbol,"asset_class":asset_class,"current_price":round(float(daily.frame.close.iloc[-1]),4),
            "price_timestamp":str(daily.frame.index[-1]),"source":daily.source,"synthetic":daily.synthetic,
            "generated_at":datetime.now(timezone.utc).isoformat(),"data_quality":"SYNTHETIC - DEMONSTRATION ONLY" if daily.synthetic else "VERIFY PROVIDER ENTITLEMENTS AND DELAY",
            "timeframes":scenarios,"crash_watch":analyze_crash_risk(daily.frame),
            "disclaimer":"For informational and research purposes only. Not personalized investment advice."}
