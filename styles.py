import streamlit as st

def apply_styles():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1450px;}
        [data-testid="stSidebar"] {background: #0f172a;}
        [data-testid="stSidebar"] * {color: #f8fafc;}
        .hero {padding: 1.4rem 1.6rem; border: 1px solid #e2e8f0; border-radius: 18px;
               background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); margin-bottom: 1.25rem;}
        .hero h1 {margin: 0; font-size: 2rem;}
        .hero p {color: #475569; margin: .35rem 0 0 0;}
        .metric-card {padding: 1rem 1.1rem; border: 1px solid #e2e8f0; border-radius: 16px;
                      background: white; min-height: 110px;}
        .metric-label {color: #64748b; font-size: .85rem; font-weight: 600;}
        .metric-value {color: #0f172a; font-size: 2rem; font-weight: 700; line-height: 1.15; margin-top: .3rem;}
        .info-card {padding: 1rem 1.1rem; border: 1px solid #e2e8f0; border-radius: 16px;
                    background: #fff; height: 100%;}
        .info-label {color: #64748b; font-size: .78rem; text-transform: uppercase;
                     letter-spacing: .04em; font-weight: 700;}
        .info-value {color: #0f172a; font-size: 1.05rem; margin-top: .25rem; font-weight: 600;}
        .status {display: inline-block; padding: .3rem .65rem; border-radius: 999px; font-size: .8rem;
                 font-weight: 700; background: #e2e8f0; color: #0f172a;}
        .timeline-item {border-left: 3px solid #cbd5e1; padding: .25rem 0 1rem 1rem; margin-left: .35rem;}
        .timeline-date {color: #64748b; font-size: .8rem;}
        .timeline-title {font-weight: 700; color: #0f172a;}
        .small-muted {color: #64748b; font-size: .88rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
