import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math

st.title("️ Module 5.05: DNA Melting Curve Simulation (qPCR)")
st.markdown("Simulate the dissociation of double-stranded DNA as temperature increases, just like a real-time PCR machine.")
st.markdown("---")

# --- INPUTS ---
dna_seq = st.text_input("Enter DNA Sequence (Amplicon)", "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCG").replace(" ", "").upper()
na_conc = st.slider("Na+ Concentration (mM)", 10, 200, 50)
steepness = st.slider("Curve Steepness (Cooperativity)", 1.0, 5.0, 2.5, help="Higher value means a sharper, more specific melting peak.")

if st.button("📈 Simulate Melting Curve", type="primary", use_container_width=True):
    if not dna_seq or any(c not in "ATCG" for c in dna_seq):
        st.error("❌ Please enter a valid DNA sequence!")
    else:
        # 1. Calculate Tm (Salt-adjusted basic formula)
        length = len(dna_seq)
        gc = dna_seq.count('G') + dna_seq.count('C')
        at = length - gc
        
        # Basic Tm
        tm_basic = 64.9 + 41 * (gc - 16.4) / length
        # Salt correction
        tm_corrected = tm_basic + 16.6 * math.log10(na_conc / 1000)
        
        # 2. Generate Temperature Range (Tm - 15 to Tm + 15)
        temps = np.arange(tm_corrected - 15, tm_corrected + 15, 0.1)
        
        # 3. Calculate Fraction of Double-Stranded DNA (Sigmoid Curve)
        # Using a logistic function to simulate the melting transition
        exponent = (temps - tm_corrected) * steepness
        # Clip exponent to avoid overflow warnings in numpy
        exponent = np.clip(exponent, -500, 500) 
        fraction_dsDNA = 1 / (1 + np.exp(exponent))
        
        # 4. Calculate Derivative (-dF/dT) for the Peak
        derivative = -np.gradient(fraction_dsDNA, temps)
        
        # --- PLOTTING ---
        fig = go.Figure()
        
        # Primary Y-axis: Fraction of dsDNA (Sigmoid)
        fig.add_trace(go.Scatter(
            x=temps, y=fraction_dsDNA, 
            mode='lines', name='Fraction of dsDNA',
            line=dict(color='#66fcf1', width=3),
            yaxis='y1'
        ))
        
        # Secondary Y-axis: Derivative Peak (-dF/dT)
        fig.add_trace(go.Scatter(
            x=temps, y=derivative, 
            mode='lines', name='-dF/dT (Melting Peak)',
            line=dict(color='#d4af37', width=4),
            yaxis='y2'
        ))
        
        # Mark the Tm Peak
        peak_idx = np.argmax(derivative)
        peak_temp = temps[peak_idx]
        
        fig.add_vline(x=peak_temp, line_dash="dash", line_color="#ff0055", 
                      annotation_text=f"Tm = {peak_temp:.1f}°C", annotation_position="top right")

        fig.update_layout(
            title="DNA Melting Curve & Derivative Peak",
            xaxis_title="Temperature (°C)",
            yaxis=dict(title="Fraction of dsDNA (0 to 1)", range=[-0.1, 1.1], side="left"),
            yaxis2=dict(title="-dF/dT (Derivative)", range=[0, max(derivative)*1.2], side="right", overlaying="y"),
            template="plotly_dark",
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#1a1f2e',
            font=dict(color='#e0e0e0'),
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- ANALYSIS ---
        st.markdown("### 📊 Melt Analysis")
        c1, c2, c3 = st.columns(3)
        c1.metric("Calculated Tm", f"{tm_corrected:.1f} °C")
        c2.metric("Peak Melt Temp", f"{peak_temp:.1f} °C")
        c3.metric("Amplicon Length", f"{length} bp")
        
        # Specificity Check
        peak_width = np.sum(derivative > (max(derivative) * 0.5)) * 0.1 # FWHM approx
        if peak_width < 2.0:
            st.success("✅ **Sharp Peak Detected!** This indicates a highly specific, single PCR product.")
        else:
            st.warning("⚠️ **Broad Peak Detected!** This might indicate non-specific binding, primer dimers, or a mixed population of products.")

        st.info("💡 **Dr. Titan's Tip:** In a real qPCR machine, the cyan line shows the DNA melting. The gold line (-dF/dT) is the derivative. A single, sharp gold peak means your PCR worked perfectly! Multiple peaks mean contamination or primer dimers.")