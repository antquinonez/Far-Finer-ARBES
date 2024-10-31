# Installation

- Create some environment variables 
- Create a Python environment, install libs, and run

# set env variables, like in an .env file

```
ANTHROPIC_TOKEN=XXXXXXXXXXXXX
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
ANTHROPIC_MAX_TOKENS=2000
ANTHROPIC_TEMPERATURE=0.5
```

# installl
```
python -m venv .venv
pip install -r requirements.txt
python candidate_role_evaluation.py
```