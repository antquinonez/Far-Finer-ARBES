import json

def clean_json(text:str)->str:
    """
    Clean JSON, return JSON
    """
    return text[text.find('{'):text.rfind('}')+1]

def response_to_py(text:str)->str:
    """
    Return Python object from JSON (including dirty JSON) response
    """
    cleaned_json = text[text.find('{'):text.rfind('}')+1]
    
    return json.loads(cleaned_json)
    