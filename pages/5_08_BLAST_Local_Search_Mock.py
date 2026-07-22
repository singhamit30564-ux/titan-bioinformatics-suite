import streamlit as st
import pandas as pd

st.title("🔍 Module 5.08: BLAST Local Search (Seed & Extend)")
st.markdown("Simulate the Basic Local Alignment Search Tool (BLAST) algorithm to find High Scoring Segment Pairs (HSPs).")
st.markdown("---")

# --- INPUTS ---
c1, c2 = st.columns(2)
with c1:
    query_seq = st.text_area("Query Sequence (Your DNA)", "ATGCGTACG", height=100)
with c2:
    subject_seq = st.text_area("Subject Sequence (Database/Target)", "CCATGCGTACGTTTAGCGATGCGTACGAA", height=100)

word_size = st.slider("Word Size (k-mer seed length)", 2, 5, 3, help="Smaller word size = more sensitive but slower.")
match_score = st.number_input("Match Score", value=2)
mismatch_score = st.number_input("Mismatch Penalty", value=-1)

if st.button("🚀 Run BLAST Search", type="primary", use_container_width=True):
    query = query_seq.replace(" ", "").upper()
    subject = subject_seq.replace(" ", "").upper()
    
    if len(query) < word_size or len(subject) < word_size:
        st.error(f"❌ Sequences too short! Must be at least {word_size} bp.")
    else:
        with st.spinner(" Seeding and Extending..."):
            hsps = [] # High Scoring Pairs
            
            # 1. SEEDING: Find exact k-mer matches
            for i in range(len(query) - word_size + 1):
                seed = query[i:i+word_size]
                
                # Find all occurrences of this seed in the subject
                start_idx = 0
                while True:
                    start_idx = subject.find(seed, start_idx)
                    if start_idx == -1:
                        break
                        
                    # 2. EXTENSION: Extend the match in both directions
                    q_pos = i
                    s_pos = start_idx
                    
                    # Extend Left
                    while q_pos > 0 and s_pos > 0:
                        if query[q_pos-1] == subject[s_pos-1]:
                            q_pos -= 1
                            s_pos -= 1
                        else:
                            break
                            
                    # Extend Right
                    q_end = i + word_size
                    s_end = start_idx + word_size
                    
                    while q_end < len(query) and s_end < len(subject):
                        if query[q_end] == subject[s_end]:
                            q_end += 1
                            s_end += 1
                        else:
                            break
                            
                    # 3. SCORING
                    aligned_q = query[q_pos:q_end]
                    aligned_s = subject[s_pos:s_end]
                    
                    score = 0
                    for q_char, s_char in zip(aligned_q, aligned_s):
                        if q_char == s_char:
                            score += match_score
                        else:
                            score += mismatch_score
                            
                    # Only keep if score is positive (Threshold)
                    if score > 0:
                        hsps.append({
                            "Query Start": q_pos + 1,
                            "Query End": q_end,
                            "Subject Start": s_pos + 1,
                            "Subject End": s_end,
                            "Score": score,
                            "Query Align": aligned_q,
                            "Subject Align": aligned_s
                        })
                        
                    start_idx += 1 # Move to find next seed occurrence
                    
            if not hsps:
                st.warning("⚠️ No significant local alignments (HSPs) found with the current parameters.")
            else:
                # Sort by score (highest first)
                hsps.sort(key=lambda x: x['Score'], reverse=True)
                
                # Remove overlapping/duplicate HSPs (Simple filter)
                unique_hsps = []
                seen_subject_ranges = set()
                
                for hsp in hsps:
                    s_range = (hsp['Subject Start'], hsp['Subject End'])
                    if s_range not in seen_subject_ranges:
                        unique_hsps.append(hsp)
                        seen_subject_ranges.add(s_range)
                        
                df = pd.DataFrame(unique_hsps)
                
                st.markdown(f"###  Found {len(unique_hsps)} High Scoring Segment Pair(s) (HSP)")
                
                # Display Results
                for index, row in df.iterrows():
                    with st.expander(f"HSP #{index+1} | Score: {row['Score']} | Subject Pos: {row['Subject Start']}-{row['Subject End']}", expanded=True):
                        st.code(f"Query:  {row['Query Align']}\nSubject:{row['Subject Align']}", language="text")
                        
                st.info("💡 **Dr. Titan's Tip:** Real BLAST uses complex heuristics (like 2-hit method) to speed this up. This 'Seed and Extend' is the core logic: find a small exact match (seed), then grow it (extend) as long as the score remains positive!")