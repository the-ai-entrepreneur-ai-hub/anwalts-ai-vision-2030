import os
import json
import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from datasets import Dataset, DatasetDict
from tqdm import tqdm
import re
import spacy

# Load the German spaCy model
nlp = spacy.load("de_core_news_sm")

def scrape_gesetze_im_internet():
    """
    This function should be implemented to scrape data from
    https://www.gesetze-im-internet.de/
    
    It should return a list of dictionaries, where each dictionary
    represents a document and has a "text" key.
    
    Example:
    return [{"text": "Content of law 1..."}, {"text": "Content of law 2..."}]
    """
    print("Scraping 'Gesetze im Internet'...")
    # --- Your scraping logic here ---
    return []

def scrape_rechtsprechung_im_internet():
    """
    This function should be implemented to scrape data from
    https://www.rechtsprechung-im-internet.de/
    
    It should return a list of dictionaries, where each dictionary
    represents a document and has a "text" key.
    
    Example:
    return [{"text": "Content of court decision 1..."}, {"text": "Content of court decision 2..."}]
    """
    print("Scraping 'Rechtsprechung im Internet'...")
    # --- Your scraping logic here ---
    return []

def fetch_open_legal_data():
    """
    This function should be implemented to fetch data from 
    the Open Legal Data API (https://openlegaldata.io/).
    
    It should return a list of dictionaries, where each dictionary
    represents a document and has a "text" key.
    """
    print("Fetching from Open Legal Data API...")
    # --- Your API fetching logic here ---
    return []

def query_eur_lex():
    """
    This function should be implemented to query the EUR-Lex
    SPARQL endpoint.
    
    It should return a list of dictionaries, where each dictionary
    represents a document and has a "text" key.
    """
    print("Querying EUR-Lex SPARQL endpoint...")
    # --- Your SPARQL query logic here ---
    return []


def clean_text(text):
    """
    Cleans and normalizes the text.
    """
    if not isinstance(text, str):
        return ""
    text = re.sub(r'§\s*(\d+)\s*([a-zA-Z]+)', r'{LAW_REF}', text)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PER", "LOC"]:
            text = text.replace(ent.text, f"{{{ent.label_}}}")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_and_format(data):
    """
    Processes raw data and formats it into prompt-completion pairs.
    """
    processed_data = []
    for item in tqdm(data, desc="Processing data"):
        text_content = item.get('text', '')
        if not text_content:
            continue
        cleaned_text = clean_text(text_content)
        prompt = "Fasse den folgenden Rechtstext zusammen:"
        completion = cleaned_text[:200] + "..."
        formatted_text = f"<s>[INST] {prompt} [/INST] {completion} </s>"
        processed_data.append({"text": formatted_text})
    return processed_data

def main():
    output_dir = "./prepared_data"
    os.makedirs(output_dir, exist_ok=True)

    all_data = []
    all_data.extend(scrape_gesetze_im_internet())
    all_data.extend(scrape_rechtsprechung_im_internet())
    all_data.extend(fetch_open_legal_data())
    all_data.extend(query_eur_lex())

    if not all_data:
        print("No data was scraped or fetched. Please implement the data gathering functions.")
        return

    formatted_data = process_and_format(all_data)

    df = pd.DataFrame(formatted_data)
    dataset = Dataset.from_pandas(df)

    shuffled_dataset = dataset.shuffle(seed=42)
    train_end = int(len(shuffled_dataset) * 0.8)
    val_end = int(len(shuffled_dataset) * 0.9)

    final_datasets = DatasetDict({
        'train': shuffled_dataset.select(range(train_end)),
        'validation': shuffled_dataset.select(range(train_end, val_end)),
        'test': shuffled_dataset.select(range(val_end, len(shuffled_dataset)))
    })


    for split_name, ds in final_datasets.items():
        output_file = os.path.join(output_dir, f"{split_name}.jsonl")
        if len(ds) > 0:
            ds.to_json(output_file, orient="records", lines=True)
            print(f"Saved {split_name} split to {output_file}")
        else:
            print(f"Skipping empty split: {split_name}")


if __name__ == "__main__":
    main()