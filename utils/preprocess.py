import spacy
import re
import string

# Load spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Model might not be installed yet, fallback to placeholder logic or instruct user
    nlp = None

def clean_text(text):
    """
    Cleans text by removing stopwords, punctuation, 
    and applying lemmatization using spaCy.
    """
    if not text:
        return ""
    
    # Check if spacy model is loaded
    if nlp is None:
        return "ERROR: spaCy model 'en_core_web_sm' is not loaded."

    # Basic cleaning: remove extra whitespace and special characters
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Process text through spaCy
    doc = nlp(text)
    
    # Filter tokens: remove stopwords, punctuation, and collect lemmas
    cleaned_tokens = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and not token.is_space
    ]
    
    return " ".join(cleaned_tokens)
