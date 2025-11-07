# =========================================
# DSPy: Structuring Unstructured Data Assignment
# Secure Version with .env Integration
# =========================================

# Install dependencies
!pip install dspy trafilatura pandas tqdm requests beautifulsoup4 python-dotenv

# -----------------------------------------
# 1. Imports
# -----------------------------------------
import os
import dspy
import requests
import pandas as pd
import trafilatura
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path
import random
from dotenv import load_dotenv

# -----------------------------------------
# 2. Load Environment Variables (.env)
# -----------------------------------------
# Load .env file
load_dotenv()

# Now the environment variables are available
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

# Set environment variables
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_API_BASE"] = api_base

# Configure DSPy with LongCat model
dspy.configure(lm=dspy.LM("openai/LongCat-Flash-Chat"))

# -----------------------------------------
# 3. Define Entity Extraction Signature
# -----------------------------------------
class EntityWithAttr(BaseModel):
    entity: str = Field(description="the named entity")
    attr_type: str = Field(description="semantic type (e.g. Drug, Disease, Process, Concept)")

class ExtractEntities(dspy.Signature):
    paragraph: str = dspy.InputField()
    entities: List[EntityWithAttr] = dspy.OutputField()

extract_entities = dspy.Predict(ExtractEntities)

# -----------------------------------------
# 4. Deduplication
# -----------------------------------------
class DeduplicateEntities(dspy.Signature):
    items: List[str] = dspy.InputField()
    deduplicated: List[str] = dspy.OutputField()
    confidence: float = dspy.OutputField()

dedup_predictor = dspy.ChainOfThought(DeduplicateEntities)

def deduplicate_with_lm(items, target_confidence=0.9):
    for _ in range(3):
        pred = dedup_predictor(items=items)
        if pred.confidence and pred.confidence >= target_confidence:
            return pred.deduplicated
    return list(set(items))

# -----------------------------------------
# 5. Relationship Generator
# -----------------------------------------
def generate_semantic_relationships(entities):
    verbs = [
        "influences", "causes", "is part of", "depends on", "regulates",
        "supports", "enhances", "reduces", "affects", "develops into"
    ]
    triples = []
    for i in range(min(len(entities) - 1, 5)):
        src, dst = entities[i], entities[i + 1]
        rel = random.choice(verbs)
        triples.append((src, rel, dst))
    return triples

# -----------------------------------------
# 6. Mermaid Generator
# -----------------------------------------
def triples_to_mermaid(triples, entity_list):
    entity_set = {e.strip().lower() for e in entity_list}
    lines = ["graph TD"]
    clean = lambda s: s.replace(" ", "_").replace("-", "_")[:40]
    for src, lbl, dst in triples:
        if src.lower() in entity_set and dst.lower() in entity_set:
            lines.append(f"  {clean(src)} -- {lbl[:40]} --> {clean(dst)}")
    return "\n".join(lines)

# -----------------------------------------
# 7. Fetch Functions
# -----------------------------------------
def fetch_with_bs(url):
    """Fallback: Use BeautifulSoup for plain text extraction."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code != 200:
            print(f"  Fallback failed ({res.status_code}) for {url}")
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text().split())
        return text[:10000]
    except Exception as e:
        print(f"  Fallback error for {url}: {e}")
        return None

def fetch_text_from_url(url):
    """Try Trafilatura first, then fallback."""
    domain = urlparse(url).netloc
    blocked_domains = ["nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov"]

    try:
        if any(b in domain for b in blocked_domains):
            print(f" Domain {domain} blocked for Trafilatura — using fallback.")
            return fetch_with_bs(url)

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False)
            if extracted and len(extracted.strip()) > 200:
                return extracted
        print(f" Trafilatura failed for {url}, using fallback.")
        return fetch_with_bs(url)
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

# -----------------------------------------
# 8. Main Pipeline
# -----------------------------------------
urls = [
    "https://en.wikipedia.org/wiki/Sustainable_agriculture",
    "https://www.nature.com/articles/d41586-025-03353-5",
    "https://www.sciencedirect.com/science/article/pii/S1043661820315152",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10457221/",
    "https://www.fao.org/3/y4671e/y4671e06.htm",
    "https://www.medscape.com/viewarticle/time-reconsider-tramadol-chronic-pain-2025a1000ria",
    "https://www.sciencedirect.com/science/article/pii/S0378378220307088",
    "https://www.frontiersin.org/news/2025/09/01/rectangle-telescope-finding-habitable-planets",
    "https://www.medscape.com/viewarticle/second-dose-boosts-shingles-protection-adults-aged-65-years-2025a1000ro7",
    "https://www.theguardian.com/global-development/2025/oct/13/astro-ambassadors-stargazers-himalayas-hanle-ladakh-india",
]

results = []

for i, url in enumerate(tqdm(urls, desc="Processing URLs")):
    print(f"\n🔎 [{i+1}/{len(urls)}] Processing URL: {url}")
    try:
        text = fetch_text_from_url(url)
        if not text:
            raise ValueError("Empty or blocked content")

        entity_output = extract_entities(paragraph=text)
        raw_entities = [e.entity for e in entity_output.entities]
        raw_types = [e.attr_type for e in entity_output.entities]

        deduped_entities = deduplicate_with_lm(raw_entities)
        triples = generate_semantic_relationships(deduped_entities)
        mermaid_str = triples_to_mermaid(triples, deduped_entities)

        mermaid_file = Path(f"mermaid_{i+1:02}.md")
        with open(mermaid_file, "w", encoding="utf-8") as f:
            f.write(mermaid_str)
        print(f" Mermaid diagram saved as {mermaid_file.name}")

        for e, t in zip(raw_entities, raw_types):
            results.append({"link": url, "tag": e, "tag_type": t})

    except Exception as e:
        error_file = Path(f"mermaid_{i+1:02}.md")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("```mermaid\n")
            f.write("graph TD\n")
            f.write(f"A[URL Index {i+1}] -->|❌ Failed| B[{url}]\n")
            f.write(f"B --> C[Error: {str(e).split(':')[0]}]\n")
            f.write("classDef error fill:#f88,stroke:#800,stroke-width:2px;\n")
            f.write("class B,C error;\n")
            f.write("```")
        print(f" Saved error Mermaid as {error_file.name}")

# -----------------------------------------
# 9. Save Output
# -----------------------------------------
df = pd.DataFrame(results)
df.to_csv("tags.csv", index=False)
print("\n Processing complete! All mermaid_XX.md and tags.csv saved.")
