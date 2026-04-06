import re
import ast
import kagglehub
import pandas as pd
from kagglehub import KaggleDatasetAdapter

# Function to load and extract skills from Kaggle Job Skill Set dataset
def get_kaggle_skills():
    """
    Downloads and extracts unique skills from the 'batuhanmutlu/job-skill-set' Kaggle dataset.
    Returns:
        list: A sorted list of unique skill strings (lowercase).
    """
    try:
        # Load the latest version as a Pandas DataFrame
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "batuhanmutlu/job-skill-set",
            "all_job_post.csv",
        )
        
        all_skills = set()
        for skills in df['job_skill_set'].dropna():
            try:
                # Skills are stored as string representation of lists (e.g., "['python', 'sql']")
                if isinstance(skills, str) and skills.startswith('[') and skills.endswith(']'):
                    skill_list = ast.literal_eval(skills)
                    all_skills.update(skill.lower().strip() for skill in skill_list)
                else:
                    # Single skill or other format
                    all_skills.add(skills.lower().strip())
            except Exception:
                continue
        
        return sorted([s for s in all_skills if s]) # Filter empty strings and sort
    except Exception as e:
        print(f"Error loading Kaggle dataset: {e}")
        # Fallback to a small list if something goes wrong
        return ["python", "sql", "machine learning", "nlp", "java"]

# Initialize PREDEFINED_SKILLS from Kaggle dataset
PREDEFINED_SKILLS = get_kaggle_skills()

def extract_skills(text):
    """
    Extracts skills from text using the skills loaded from Kaggle.
    Returns:
        set: A set of unique extracted skill strings.
    """
    if not text:
        return set()
    
    # Normalize text to lowercase for comparison
    text_lower = text.lower()
    
    extracted = set()
    # Performance Optimization: Only check for skills that might actually be there
    # Instead of iterating 5000+ skills with regex, we can do a faster check
    # But for correctness with spaces (e.g., 'machine learning'), regex is safer.
    # We'll use a slightly optimized approach.
    
    for skill in PREDEFINED_SKILLS:
        # Use regex to find whole words only
        # Note: If skill is very short (e.g. 'c'), \b is important
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            extracted.add(skill)
            
    return extracted

def compare_skills(resume_skills, jd_skills):
    """
    Compares resume skills against job description skills.
    Returns:
        tuple: (matched_skills, missing_skills)
    """
    matched_skills = resume_skills.intersection(jd_skills)
    missing_skills = jd_skills.difference(resume_skills)
    
    return sorted(list(matched_skills)), sorted(list(missing_skills))

def skill_match_score(resume_skills, jd_skills):
    """
    Calculates the percentage of JD skills present in the resume.
    """
    if not jd_skills:
        return 0
    
    matched_skills = resume_skills.intersection(jd_skills)
    score = (len(matched_skills) / len(jd_skills)) * 100
    return round(score)

def generate_explanation(similarity_score, skill_score, matched_skills, missing_skills):
    """
    Generates a short, rule-based explanation for the ranking.
    """
    if skill_score > 70:
        skill_eval = "strong alignment in core skills"
    elif skill_score >= 40:
        skill_eval = "moderate alignment in skills"
    else:
        skill_eval = "limited skill match"

    if similarity_score < 30:
        sim_eval = "but shows low contextual relevance to the JD"
    else:
        sim_eval = "and solid overall profile relevance"

    explanation = f"This candidate has {skill_eval} {sim_eval}."

    if matched_skills:
        explanation += f" They are proficient in {', '.join([s.title() for s in matched_skills[:2]])}."
    
    if missing_skills:
        explanation += f" However, key areas like {', '.join([s.title() for s in missing_skills[:2]])} were not identified in the resume."

    return explanation
