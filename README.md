# DSPy: Structuring Unstructured Data using LongCat API

This project extracts **semantic entities** and **relationships** from online articles using **DSPy** and the **LongCat API**.  
It automatically generates **Mermaid graph visualizations** (`.md` files) and a combined **CSV** file containing the extracted entities and their semantic types.

---

##  Features

-  Fetches article text using **Trafilatura** and **BeautifulSoup** (as fallback)
-  Extracts entities with **DSPy** + **LongCat**
-  Generates meaningful **semantic relationship triples**
-  Produces **Mermaid diagrams** for each URL
-  Creates **error Mermaid graphs** if a URL fails (e.g. `mermaid03.md`)
-  Exports structured data to `tags.csv`
-  Keeps your API key secure using `.env` and `.gitignore`

---

##  Requirements

Make sure you have **Python 3.9+** installed.

Install all dependencies with:

```bash
pip install dspy trafilatura pandas tqdm requests beautifulsoup4 python-dotenv
```
## Project Setup
1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. Create the .env File
In your project’s root directory, create a new file called .env and add the following:

```bash
OPENAI_API_KEY=your_longcat_api_key_here
OPENAI_API_BASE=https://api.longcat.chat/openai/v1
```

This file contains sensitive credentials — do not share or push it to GitHub.


3. Create the .gitignore File
In the same folder, create .gitignore and add this content:
```bash
# Environment and credentials
.env

# Byte-compiled / cache files
__pycache__/
*.pyc

# Output files
*.log
*.csv
*.md
```
This ensures that your API keys, generated Mermaid diagrams, and CSVs stay private and are not uploaded to your repo.

4️. Run the Script
If you’re running a local Python file:
```bash
python main.py
```
If you’re using Jupyter Notebook or Google Colab:
```bash
!python main.py
```

## Example of a Mermaid Graph
Below is a sample Mermaid graph that the program generates:
graph TD
  A[Crop Rotation] -->|enhances| B[Soil Fertility]
  B -->|supports| C[Sustainable Agriculture]

You can visualize these .md files in any Mermaid-compatible viewer (e.g. GitHub Markdown preview, VS Code with Mermaid plugin).

## How It Works

Fetch Content → Retrieves article text using trafilatura and BeautifulSoup
Extract Entities → Uses DSPy with LongCat API to identify entities and attributes
Deduplicate Entities → Ensures clean, unique entity lists
Generate Relationships → Builds logical links between entities
Create Mermaid Graphs → Saves visual diagrams for each URL
Save Structured Data → Exports entity data to tags.csv


## File Structure

```bash
 your-repo/
 ┣  main.py
 ┣  .env
 ┣  .gitignore
 ┣  README.md
 ┣  tags.csv
 ┣  mermaid_01.md
 ┣  mermaid_02.md
 ┣  mermaid_03.md
 ┗ ...
```

## License
This project is released under the MIT License.
You are free to use, modify, and distribute this code with proper attribution.

## Author
Gurpreet Kaur
B.Sc. (Hons) Computer Science, Delhi University
Minor in AI (IIT Ropar & Delhi University)

