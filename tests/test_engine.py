from market_agent.data import DemoProvider
from market_agent.report import build_report

def test_complete_report():
    p=DemoProvider(); data={h:p.fetch("SPY","stock",h,700) for h in ["hourly","daily","weekly","long_term"]}
    r=build_report("SPY","stock",data)
    assert set(r["timeframes"])=={"hourly","daily","weekly","long_term"}
    assert 0<=r["crash_watch"]["crash_risk_score"]<=100
    assert r["synthetic"] is True
