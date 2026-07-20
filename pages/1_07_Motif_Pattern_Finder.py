import streamlit as st
import re
import pandas as pd
import plotly.graph_objects as go

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 TITAN TOOL 7: MOTIF & PATTERN FINDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🔍 Module 7: Motif & Pattern Finder")
st.markdown("Search for specific DNA patterns, regulatory motifs, or custom sequences with position highlighting.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    "Enter DNA Sequence (5' to 3'):", 
    "ATGCGCTAGCTAGCTATAAATAGCTAGCTAGCTAGCTAGCATCGATCGATGAAACCCGGGTTTAA", 
    height=150, 
    key="motif_dna_input"
)

st.markdown("### 🎯 Search Pattern")
st.caption("Enter a specific motif (e.g., 'TATAAA' for TATA box) or use regex (e.g., 'ATG[ATGC]{3}TAA')")

col1, col2 = st.columns([2, 1])
with col1:
    pattern_input = st.text_input("Pattern to search:", "TATAAA", key="motif_pattern")
with col2:
    case_sensitive = st.checkbox("Case Sensitive", value=False, key="motif_case")

st.markdown("<br>", unsafe_allow_html=True)
calculate_btn = st.button("🔍 Find Pattern Matches", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "")
    pattern = pattern_input.strip()
    
    if not case_sensitive:
        clean_dna = clean_dna.upper()
        pattern = pattern.upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif not pattern:
        st.error("❌ Please enter a search pattern.")
    elif any(char not in "ATCG" for char in clean_dna.replace("N", "")):
        st.error("❌ Invalid DNA! Only A, T, C, G (and N for unknown) are allowed.")
    else:
        try:
            # Find all matches with positions
            matches = []
            for match in re.finditer(pattern, clean_dna):
                matches.append({
                    'Match_Number': len(matches) + 1,
                    'Start_Position': match.start() + 1,
                    'End_Position': match.end(),
                    'Matched_Sequence': match.group(),
                    'Context': clean_dna[max(0, match.start()-10):min(len(clean_dna), match.end()+10)]
                })
            
            total_matches = len(matches)
            
            # --- DISPLAY METRICS ---
            st.markdown("### 📊 Search Statistics")
            met_col1, met_col2, met_col3 = st.columns(3)
            met_col1.metric("📏 Sequence Length", f"{len(clean_dna)} bp")
            met_col2.metric("🎯 Pattern Length", f"{len(pattern)} bp")
            met_col3.metric("✅ Total Matches", f"{total_matches}")
            
            st.markdown("---")
            
            if total_matches > 0:
                # --- VISUAL POSITION MAP ---
                st.markdown("### 🗺️ Match Position Map")
                st.caption("Visual representation of where your pattern occurs in the sequence")
                
                fig = go.Figure()
                
                # Add sequence as a horizontal line
                fig.add_trace(go.Scatter(
                    x=[1, len(clean_dna)],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#45a29e', width=2),
                    name='Sequence',
                    hoverinfo='skip'
                ))
                
                # Add matches as markers
                match_positions = [m['Start_Position'] for m in matches]
                fig.add_trace(go.Scatter(
                    x=match_positions,
                    y=[0] * len(match_positions),
                    mode='markers',
                    marker=dict(
                        color='#d4af37',
                        size=12,
                        symbol='diamond'
                    ),
                    name=f'Pattern Matches ({total_matches})',
                    text=[f"Position: {m['Start_Position']}-{m['End_Position']}<br>Sequence: {m['Matched_Sequence']}" for m in matches],
                    hoverinfo='text'
                ))
                
                fig.update_layout(
                    title=f"Pattern '{pattern}' Location Map",
                    xaxis_title="Position (bp)",
                    yaxis=dict(visible=False),
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    showlegend=True,
                    margin=dict(t=40, b=40, l=40, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # --- DETAILED MATCHES TABLE ---
                st.markdown("### 📋 Detailed Match Results")
                df_matches = pd.DataFrame(matches)
                
                st.dataframe(
                    df_matches,
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- FREQUENCY ANALYSIS ---
                if total_matches > 1:
                    st.markdown("---")
                    st.markdown("### 📊 Match Frequency Distribution")
                    
                    # Calculate spacing between matches
                    spacings = []
                    for i in range(1, len(matches)):
                        spacing = matches[i]['Start_Position'] - matches[i-1]['End_Position']
                        spacings.append(spacing)
                    
                    if spacings:
                        avg_spacing = sum(spacings) / len(spacings)
                        min_spacing = min(spacings)
                        max_spacing = max(spacings)
                        
                        spacing_col1, spacing_col2, spacing_col3 = st.columns(3)
                        spacing_col1.metric("📏 Average Spacing", f"{avg_spacing:.1f} bp")
                        spacing_col2.metric("📐 Minimum Spacing", f"{min_spacing} bp")
                        spacing_col3.metric("📐 Maximum Spacing", f"{max_spacing} bp")
                        
            else:
                st.warning(f"⚠️ **No matches found** for pattern '{pattern}' in the given sequence.")
                st.info("💡 Try a different pattern or check if the sequence contains your target motif.")
            
            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
            with col_btn2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, batch processing, and advanced analytics.")
                    
        except re.error as e:
            st.error(f"❌ Invalid regex pattern: {e}")
        except Exception as e:
            st.error(f"⚠️ Search Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** Common biological motifs include:\n- **TATA Box:** 'TATAAA' (promoter region)\n- **Kozak Sequence:** 'GCCRCCATGG' (translation initiation)\n- **Poly-A Signal:** 'AATAAA' (mRNA processing)\n\nYou can also use regex patterns like 'ATG[ATGC]{3}TAA' to find variable-length motifs!")