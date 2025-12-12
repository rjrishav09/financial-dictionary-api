import pandas as pd
import re
from fuzzywuzzy import process
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Financial Dictionary API")

# Allow Flutter/mobile/web apps to call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === LOAD YOUR CSV (Render will have it) ===
df = pd.read_csv("financial_terms_100k_realistic_style.csv")
financial_dict = dict(zip(df["term"].str.lower(), df["definition"]))
term_list = list(financial_dict.keys())

def simple_tokenize(text: str):
    return re.findall(r"\w+", text.lower())

def extract_financial_term(sentence: str, max_ngram=6) -> Optional[str]:
    if not sentence or not sentence.strip():
        return None
    tokens = simple_tokenize(sentence)
    if not tokens:
        return None

    ngrams = []
    L = len(tokens)
    for n in range(1, min(max_ngram, L) + 1):
        for i in range(L - n + 1):
            ngrams.append(" ".join(tokens[i:i+n]))

    full_text = " ".join(tokens)
    best_full = process.extractOne(full_text, term_list)
    if best_full and best_full[1] >= 82:
        return best_full[0]

    best_match = None
    best_score = 0
    for ng in sorted(ngrams, key=lambda x: -len(x.split())):
        res = process.extractOne(ng, term_list)
        if res and res[1] > best_score:
            best_score = res[1]
            best_match = res[0]
            if best_score >= 80:
                return best_match

    if best_score >= 70:
        return best_match
    return None

def get_definition(term: Optional[str]) -> Optional[str]:
    if not term:
        return None
    return financial_dict.get(term.lower())

def financial_dictionary_model(user_input: str) -> str:
    term = extract_financial_term(user_input)
    if not term:
        return "Could not identify a financial term. Try asking directly (e.g., 'What is EBITDA?')"
    definition = get_definition(term)
    if not definition:
        return f"Term found: '{term}' → no definition."
    return f"**{term.upper()}**\n\n{definition}"

class QueryRequest(BaseModel):
    user_input: str

@app.get("/")
def home():
    return {"message": "Financial Dictionary API is LIVE!"}

@app.post("/query")
async def query(request: QueryRequest):
    result = financial_dictionary_model(request.user_input)
    return {"response": result}
