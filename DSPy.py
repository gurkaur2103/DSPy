# =========================================
# DSPy: Structuring Unstructured Data Assignment
# Fixed + Hybrid Fetcher + LongCat Integration
# =========================================

# Install necessary dependencies
!pip install dspy trafilatura pandas tqdm requests beautifulsoup4

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

# -----------------------------------------
# 2. Configure LongCat API
# -----------------------------------------
os.environ["OPENAI_API_KEY"] = "ak_1Oc6C50ID7OZ1hS84z4iK7Zb5Sf2M"   
os.environ["OPENAI_API_BASE"] = "https://api.longcat.chat/openai/v1"

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
# 4. Deduplication with Confidence Loop
# -----------------------------------------
class DeduplicateEntities(dspy.Signature):
    items: List[str] = dspy.InputField()
    deduplicated: List[str] = dspy.OutputField()
    confidence: float = dspy.OutputField()

dedup_predictor = dspy.ChainOfThought(DeduplicateEntities)

def deduplicate_with_lm(items, target_confidence=0.9):
    for _ in range(5):  # retry up to 5 times
        pred = dedup_predictor(items=items)
        if pred.confidence and pred.confidence >= target_confidence:
            return pred.deduplicated
    return list(set(items))  # fallback if confidence loop fails

# -----------------------------------------
# 5. Mermaid Graph Generator
# -----------------------------------------
def triples_to_mermaid(triples, entity_list):
    entity_set = {e.strip().lower() for e in entity_list}
    lines = ["graph TD"]
    def _clean(s): return s.replace(" ", "_").replace("-", "_")[:40]
    for src, lbl, dst in triples:
        if src.lower() in entity_set and dst.lower() in entity_set:
            lines.append(f"  {_clean(src)} -- {lbl[:40]} --> {_clean(dst)}")
    return "\n".join(lines)

# -----------------------------------------
# 6. Hybrid Fetcher (Trafilatura + Fallback)
# -----------------------------------------
def fetch_with_bs(url):
    """Fallback: Use BeautifulSoup to extract readable text."""
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
            print(f" Fallback failed ({res.status_code}) for {url}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = " ".join(soup.get_text().split())
        return text[:10000]  # Limit to avoid memory issues

    except Exception as e:
        print(f" Fallback error for {url}: {e}")
        return None


def fetch_text_from_url(url):
    """Try Trafilatura first, then fallback to BeautifulSoup if blocked."""
    domain = urlparse(url).netloc
    blocked_domains = ["nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov"]

    try:
        if any(blocked in domain for blocked in blocked_domains):
            print(f" Using fallback for {domain}")
            return fetch_with_bs(url)

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False)
            if extracted and len(extracted.strip()) > 200:
                return extracted

        print(f" Trafilatura failed for {url}, using fallback.")
        return fetch_with_bs(url)

    except Exception as e:
        print(f" Error fetching {url}: {e}")
        return None

# -----------------------------------------
# 7. Main Processing Pipeline
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
    try:
        text = fetch_text_from_url(url)
        if not text:
            print(f" Skipping empty text from {url}")
            continue

        # Extract entities
        entity_output = extract_entities(paragraph=text)
        raw_entities = [e.entity for e in entity_output.entities]
        raw_types = [e.attr_type for e in entity_output.entities]

        # Deduplicate
        deduped_entities = deduplicate_with_lm(raw_entities)

        # Generate dummy triples (for demonstration)
        triples = [(deduped_entities[i], "related_to", deduped_entities[i+1])
                   for i in range(min(len(deduped_entities)-1, 5))]

        # Save Mermaid Diagram
        mermaid_str = triples_to_mermaid(triples, deduped_entities)
        with open(f"mermaid_{i+1}.md", "w") as f:
            f.write(mermaid_str)

        # Save structured tags
        for e, t in zip(raw_entities, raw_types):
            results.append({"link": url, "tag": e, "tag_type": t})

    except Exception as e:
        print(f" Error processing {url}: {e}")

# -----------------------------------------
# 8. Save CSV Output
# -----------------------------------------
df = pd.DataFrame(results)
df.to_csv("tags.csv", index=False)
print(" Processing complete! Files saved as mermaid_*.md and tags.csv")
