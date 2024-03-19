import streamlit as st
import plotly.graph_objects as go

#page_settings------------
page_icon = ":wheel:"
page_title = "Energy Consumption Estimator"
layout = "centered"
#-------------------------

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
st.title(page_title + " " + page_icon)