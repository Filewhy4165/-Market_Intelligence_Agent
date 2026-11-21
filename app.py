import json, os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from market_agent.data import get_provider
from market_agent.report import build_report

st.set_page_config(page_title="Market Intelligence Agent",layout="wide")
st.title("Multi-Asset Market Intelligence Agent")
st.caption("Research only. No order execution. No guaranteed predictions.")
with st.sidebar:
    symbol=st.text_input("Instrument","SPY")
    asset=st.selectbox("Asset class",["stock","forex","futures","index","crypto"])
    run=st.button("Run complete analysis",type="primary")
if run:
    provider=get_provider()
    with st.spinner("Verifying data and analyzing multiple horizons..."):
        data={h:provider.fetch(symbol,asset,h,1500 if h!="hourly" else 1200) for h in ["hourly","daily","weekly","long_term"]}
        report=build_report(symbol,asset,data)
    if report["synthetic"]: st.error("DEMO MODE: all prices and conclusions below use synthetic data, not live markets.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Price",report["current_price"]); c2.metric("Crash Risk",report["crash_watch"]["crash_risk_score"])
    c3.metric("Warning",report["crash_watch"]["warning_level"]); c4.metric("Source",report["source"])
    daily=data["daily"].frame
    fig=go.Figure(data=[go.Candlestick(x=daily.index,open=daily.open,high=daily.high,low=daily.low,close=daily.close)])
    fig.update_layout(height=440,xaxis_rangeslider_visible=False); st.plotly_chart(fig,use_container_width=True)
    st.subheader("Multi-timeframe dashboard")
    rows=[]
    for h,s in report["timeframes"].items():
        rows.append({"Horizon":h,"Direction":s["direction"],"Entry":f'{s["entry_low"]:.2f}-{s["entry_high"]:.2f}',"Stop":s["stop"],"TP1":s["tp1"],"TP2":s["tp2"],"TP3":s["tp3"],"R:R":s["risk_reward"],"Confidence":s["confidence"],"Score":s["score"],"Status":s["status"]})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.subheader("Crash & correction engine")
    cw=report["crash_watch"]
    st.write({k:cw[k] for k in ["structural_vulnerability","immediate_downside_pressure","validation","historical_analogs"]})
    st.download_button("Download JSON report",json.dumps(report,indent=2,default=str),file_name=f"{symbol}_market_report.json")
    with st.expander("Complete machine-readable report"): st.json(report)
else:
    st.info("Enter an instrument and run the analysis. The included demo provider is deliberately labeled synthetic.")
