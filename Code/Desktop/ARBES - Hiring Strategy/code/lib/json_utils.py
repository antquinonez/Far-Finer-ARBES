def clean_json(text:str)->str:
    return text[text.find('{'):text.rfind('}')+1]