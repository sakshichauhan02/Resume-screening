import re

def extract_experience(text):
    """
    Extracts years of experience from text using regex.
    Handles single values, ranges (5-10 years), and prefixes (at least 5 years).
    """
    if not text:
        return 0
    text_lower = text.lower()
    
    # 1. Handle ranges like "5-10 years", "5-10 yrs", "5 to 10 years"
    range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?|yr)', text_lower)
    if range_match:
        return int(range_match.group(1))

    # 2. Handle "at least X years", "minimum X years", etc.
    min_match = re.search(r'(?:at least|minimum|min|more than|over|atleast)\s*(\d+)\s*(?:years?|yrs?|yr)', text_lower)
    if min_match:
        return int(min_match.group(1))

    # 3. Standard patterns (X years of experience, X+ years exp, etc.)
    # Added leniency for typos like "expierence"
    patterns = [
        r'\b(\d+)\+?\s*years?\s*of\s*(?:experience|expierence)\b',
        r'\b(\d+)\+?\s*years?\s*exp\b',
        r'\b(?:experience|expierence)\s*of\s*(\d+)\+?\s*years?\b',
        r'\b(\d+)\+?\s*yrs\b',
        r'\b(\d+)\+?\s*yr\b',
        r'\b(\d+)\+\s*years?\b',
        r'should\s*be\s*(?:of\s*)?(\d+)\s*years?', # Handle "should be of 6 years"
        r'\b(\d+)\s*years?\b' # Broadest fallback: "X years"
    ]
    
    max_years = 0
    for pattern in patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # The group might be different for the "should be" pattern
            try:
                val = match.group(1)
            except IndexError:
                val = match.group(0) # Fallback if no group 1
                
            years = int(re.search(r'\d+', val).group())
            if years > max_years:
                max_years = years

    # 4. Handle date ranges (e.g. 2015 - 2020 or 2018 - present)
    # Useful for resumes that list work history by dates
    # We must be careful not to include education dates
    current_year = 2026
    date_range_pattern = r'(20\d{2})\s*(?:-|to)\s*(20\d{2}|present|current|now)'
    
    sum_diff_years = 0
    # Use finditer to get positions
    for match in re.finditer(date_range_pattern, text_lower):
        start_pos = match.start()
        # Check context (last 150 chars) for education keywords
        context = text_lower[max(0, start_pos - 150):start_pos]
        edu_keywords = ["education", "university", "college", "degree", "school", "bachelor", "master", "phd", "btech", "mtech", "b.tech", "m.tech", "be ", "m.e.", "b.s.", "m.s."]
        
        if any(keyword in context for keyword in edu_keywords):
            continue # Likely an education date range, skip it
            
        start, end = match.groups()
        s_year = int(start)
        e_year = current_year if end in ["present", "current", "now"] else int(end)
        diff = e_year - s_year
        if 0 < diff < 50:
            sum_diff_years += diff
            
    if sum_diff_years > max_years:
        max_years = sum_diff_years
                
    return max_years

def extract_education_level(text):
    """
    Identifies the highest level and specific degree subjects.
    Returns: (level, [subjects])
    """
    if not text:
        return 0, []
    
    text_lower = text.lower()
    
    # 1. Level Detection
    levels = {
        3: ["phd", "doctorate", "ph.d"],
        2: ["master", "postgraduate", "pg"],
        1: ["bachelor", "undergraduate", "ug", "graduta", "graduate"]
    }
    
    max_level = 0
    for level, keywords in levels.items():
        if any(k in text_lower for k in keywords):
            if level > max_level:
                max_level = level

    # 2. Specific Subject Detection (using word boundaries for accuracy)
    subjects = ["mba", "mtech", "m.tech", "mca", "btech", "b.tech", "bsc", "b.s.", "msc", "m.s.", "bca", "be ", "b.e.", "me ", "m.e.", "phd"]
    found_subjects = []
    for sub in subjects:
        if re.search(r'\b' + re.escape(sub.strip()) + r'\b', text_lower):
            # Normalize common names
            norm_sub = sub.replace(".", "").strip()
            found_subjects.append(norm_sub)
            
    # If level is missing but subject found, upgrade level
    if max_level < 2:
        if any(s in ["mba", "mtech", "mca", "msc", "me", "ms"] for s in found_subjects):
            max_level = 2
    if max_level < 1:
        if any(s in ["btech", "bsc", "bca", "be", "bs"] for s in found_subjects):
            max_level = 1

    return max_level, list(set(found_subjects))

def score_experience(resume_years, jd_years):
    """
    Scores experience based on JD requirements.
    """
    if jd_years == 0:
        return 100
    if resume_years == 0:
        return 0
    
    score = (resume_years / jd_years) * 100
    return min(100, round(score))

def score_education(resume_info, jd_info):
    """
    resume_info/jd_info: (level, [subjects])
    """
    resume_lvl, resume_subs = resume_info
    jd_lvl, jd_subs = jd_info
    
    if jd_lvl == 0 and not jd_subs:
        return 100
        
    score = 0
    
    # 1. Level Alignment (50%)
    if resume_lvl >= jd_lvl:
        score += 50
    else:
        score += (resume_lvl / max(1, jd_lvl)) * 50
        
    # 2. Subject Alignment (50%)
    if not jd_subs:
        score += 50 # No specific subject asked
    else:
        # Check for intersection
        matches = set(jd_subs).intersection(set(resume_subs))
        if matches:
            score += 50
        else:
            # If it's a technical role and they have a different technical degree, give partial
            # But here we want to be strict if they asked for MBA
            score += 0 # Mismatch in subject
            
    return round(score)
