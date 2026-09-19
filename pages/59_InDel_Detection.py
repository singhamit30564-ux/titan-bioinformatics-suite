import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("✂️ Module 5.07: InDel (Insertion/Deletion) Detection")
st.markdown("Identify gaps (Insertions or Deletions) in an aligned sequence compared to a reference.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    ref_seq = st.text_area("Reference Sequence", "ATGCGT---ACGTAGCTAG", height=150)
with c2:
    query_seq = st.text_area("Query Sequence (with gaps)", "ATGCGTGGGACGTAGCTAG", height=150)

if st.button("🔬 Detect InDels", type="primary", use_container_width=True):
    ref = ref_seq.replace(" ", "").upper()
    query = query_seq.replace(" ", "").upper()
    
    min_len = min(len(ref), len(query))
    ref = ref[:min_len]
    query = query[:min_len]
    
    indels = []
    current_event = None
    
    for i in range(min_len):
        if ref[i] == '-' and query[i] != '-':
            event_type = "Insertion in Query"
            base = query[i]
        elif ref[i] != '-' and query[i] == '-':
            event_type = "Deletion in Query"
            base = ref[i]
        else:
            continue
            
        if current_event and current_event['Type'] == event_type and current_event['End'] == i:
            current_event['End'] = i + 1
            current_event['Length'] += 1
            current_event['Sequence'] += base
        else:
            if current_event:
                indels.append(current_event)
            current_event = {
                "Start": i + 1,
                "End": i + 2,
                "Type": event_type,
                "Length": 1,
                "Sequence": base
            }
            
    if current_event:
        indels.append(current_event)
        
    if not indels:
        st.success("✅ No InDels detected! Sequences are perfectly aligned without gaps.")
    else:
        df = pd.DataFrame(indels)
        st.markdown(f"### 📊 Detected {len(df)} InDel Events")
        
        # Color code the dataframe
        def color_type(val):
            return 'background-color: #1a472a; color: #66fcf1' if 'Insertion' in val else 'background-color: #4a0000; color: #ff0055'
            
        st.dataframe(df.style.applymap(color_type, subset=['Type']), use_container_width=True, hide_index=True)
        
        # Visualization
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Type'],
            y=df['Length'],
            text=df['Length'],
            textposition='auto',
            marker_color=['#66fcf1' if 'Insertion' in t else '#ff0055' for t in df['Type']]
        ))
        
        fig.update_layout(
            title="InDel Length Distribution",
            xaxis_title="Event Type",
            yaxis_title="Length (bp)",
            template="plotly_dark",
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#1a1f2e',
            font=dict(color='#e0e0e0')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Dr. Titan's Tip:** InDels (Insertions/Deletions) are a major source of genetic diversity and disease (e.g., Cystic Fibrosis is caused by a 3-bp deletion). Detecting them accurately is crucial for variant calling!")