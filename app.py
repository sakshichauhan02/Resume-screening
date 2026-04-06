import streamlit as st
from utils.parser import extract_text_from_pdf
from utils.preprocess import clean_text
from utils.skills import extract_skills, compare_skills, skill_match_score, generate_explanation
from utils.extractor import extract_experience, extract_education_level, score_experience, score_education
import re

# Page Config
st.set_page_config(
        page_title="AI Candidate Shortlisting",
        page_icon="🤖",
        layout="wide"
)

# Custom Styling (Enhanced UI)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTitle { color: #1e293b; font-size: 3rem; font-weight: 800; margin-bottom: 0px; }
    .stHeader { color: #334155; }
    .section-header { 
        font-size: 1.5rem; 
        font-weight: 700; 
        margin-bottom: 12px; 
        color: #0f172a;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8px;
    }
    .clean-box {
        background-color: #ffffff;
        color: #334155;
        padding: 20px;
        border-radius: 8px;
        border-left: 6px solid #10b981;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        font-family: inherit;
        margin-bottom: 24px;
    }
    .score-badge {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2563eb;
        background-color: #eff6ff;
        padding: 8px 32px;
        border-radius: 50px;
        display: inline-block;
        margin-bottom: 25px;
        border: 2px solid #3b82f6;
    }
    .skill-tag {
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .skill-matched {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    .skill-missing {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🚀 AI-Powered Candidate Screening & Shortlisting Tool")
    st.caption("🔍 Advanced NLP-driven Resume Matching with Weighted Experience, Education & Skill Analysis")
    st.divider()

    # Layout with columns
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("<div class='section-header'>📥 Input Sources</div>", unsafe_allow_html=True)
        
        # 1. Resume Upload
        st.write("### Resumes")
        uploaded_files = st.file_uploader("Upload Profile(s) (PDF)", type=["pdf"], accept_multiple_files=True)
        
        # 2. JD Text Area
        st.write("### Job Description")
        jd_text = st.text_area("Paste the Job Description here", height=200, placeholder="We are looking for a Senior Developer with expertise in...")

    # Process and View
    if uploaded_files and jd_text:
        candidate_results = []
        
        # Step 1: Extract and Process JD once
        with st.spinner("Analyzing Job Description..."):
            jd_cleaned = clean_text(jd_text)
            jd_skills = extract_skills(jd_text)
            jd_years_req = extract_experience(jd_text)
            jd_edu_req = extract_education_level(jd_text)

        # Step 2: Extract and Process each Resume
        with st.spinner(f"Processing {len(uploaded_files)} resumes..."):
            for uploaded_file in uploaded_files:
                # Extraction
                resume_raw = extract_text_from_pdf(uploaded_file)
                if not resume_raw.strip():
                    continue # Skip empty resumes
                    
                # Cleaning
                resume_cleaned = clean_text(resume_raw)
                
                # Scoring Components
                resume_skills = extract_skills(resume_raw)
                resume_years = extract_experience(resume_raw)
                resume_edu = extract_education_level(resume_raw)

                skill_score = skill_match_score(resume_skills, jd_skills)
                exp_score = score_experience(resume_years, jd_years_req)
                edu_score = score_education(resume_edu, jd_edu_req)
                
                matched, missing = compare_skills(resume_skills, jd_skills)
                
                # Weighted Calculation: 45% Skills, 35% Experience, 20% Education
                final_score = round(
                    (0.45 * skill_score) + 
                    (0.35 * exp_score) + 
                    (0.20 * edu_score)
                )
                
                # Explanation
                explanation = generate_explanation(final_score, skill_score, matched, missing)
                
                candidate_results.append({
                    "name": uploaded_file.name,
                    "final_score": final_score,
                    "skill_score": skill_score,
                    "exp_score": exp_score,
                    "edu_score": edu_score,
                    "exp_years": resume_years,
                    "edu_level": resume_edu[0],
                    "edu_degrees": resume_edu[1],
                    "matched": matched,
                    "missing": missing,
                    "explanation": explanation,
                    "resume_cleaned": resume_cleaned
                })

        # Step 3: Sort candidates by score
        candidate_results.sort(key=lambda x: x["final_score"], reverse=True)

        with col_output:
            st.markdown("<div class='section-header'>🏆 Ranked Candidates</div>", unsafe_allow_html=True)
            st.caption("🔍 Score Weightage: 45% Skills, 35% Experience, 20% Education")
            
            if not candidate_results:
                st.warning("No readable resume text found in uploaded files.")
            else:
                for i, candidate in enumerate(candidate_results):
                    rank = i + 1
                    with st.expander(f"#{rank} | {candidate['name']} — {candidate['final_score']}% Match", expanded=(i==0)):
                        # Score Breakdown
                        col_m1, col_m2, col_m3 = st.columns(3)
                        col_m1.metric("Skills (45%)", f"{candidate['skill_score']}%")
                        col_m2.metric("Experience (35%)", f"{candidate['exp_score']}%")
                        col_m3.metric("Education (20%)", f"{candidate['edu_score']}%")

                        # Detail sub-info
                        st.caption(f"📍 Detected: {candidate['exp_years']} years experience | Education Level: {['Unknown', 'Bachelor', 'Master', 'PhD'][candidate['edu_level']]}")

                        # Explanation
                        st.markdown(f"**AI Explanation:** {candidate['explanation']}")
                        
                        st.divider()
                        
                        # Skills
                        st.write("**Matched Skills:**")
                        if candidate['matched']:
                            skill_html = "".join([f"<span class='skill-tag skill-matched'>{s.title()}</span>" for s in candidate['matched']])
                            st.markdown(skill_html, unsafe_allow_html=True)
                        else:
                            st.info("No matching skills found.")

                        st.write("**Missing Skills:**")
                        if candidate['missing']:
                            skill_html = "".join([f"<span class='skill-tag skill-missing'>{s.title()}</span>" for s in candidate['missing']])
                            st.markdown(skill_html, unsafe_allow_html=True)
                        else:
                            st.success("All JD skills present!")

                        # Raw NLP View (Inside the expander, hidden by default)
                        with st.popover("View NLP Details"):
                            st.info("Normalized text used for TF-IDF processing.")
                            st.markdown(f"<div class='clean-box'>{candidate['resume_cleaned']}</div>", unsafe_allow_html=True)
                
                st.success(f"Successfully ranked {len(candidate_results)} candidates.")

if __name__ == "__main__":
    main()
