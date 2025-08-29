# German Legal Dataset Preparation for LLM Fine-tuning

This project downloads and prepares German legal datasets for training large language models, specifically formatted for instruction-tuning with legal domain knowledge.

## 📁 Project Structure

```
.
├── prepared_data/          # Output directory for processed datasets
├── data_sources/          # Raw downloaded data storage
├── scripts/               # Data processing scripts
├── requirements.txt       # Python dependencies
├── run_preparation.py     # Main execution script
└── README.md             # This file
```

## 🎯 Datasets Processed

1. **Gesetze im Internet** - German federal laws (scraped)
2. **Rechtsprechung im Internet** - German court decisions (scraped)
3. **German Legal Sentences** - HuggingFace dataset
4. **Multi-EURLEX** - EU legal documents in German

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download de_core_news_sm
```

Or run the automated installer:
```bash
python scripts/install_dependencies.py
```

### 2. Run Data Preparation

```bash
python run_preparation.py
```

This will:
- Download datasets from HuggingFace
- Scrape German legal websites
- Clean and normalize all text
- Create instruction-tuned prompt-completion pairs
- Split into train/validation/test sets (80/10/10)
- Export as JSONL files

## 📊 Output Format

The processed data follows HuggingFace JSONL format with instruction-tuning structure:

```json
{"text": "<s>[INST] Fasse den folgenden Rechtstext zusammen: [/INST] Placeholder text from legal document... </s>"}
```

### Generated Files

- `prepared_data/train.jsonl` - Training set (80%)
- `prepared_data/validation.jsonl` - Validation set (10%)
- `prepared_data/test.jsonl` - Test set (10%)
- `prepared_data/metadata.json` - Dataset statistics and info

## 🔧 Data Processing Features

### Text Cleaning & Normalization
- Remove headers, footers, and formatting artifacts
- Normalize whitespace and line breaks
- Standardize legal references (§ 573 BGB → {LAW_REF_BGB_573})
- Replace PII with placeholders ({NAME}, {CITY}, {DATE})

### Instruction Pair Generation
- Legal text summarization tasks
- Legal concept explanation tasks
- Document analysis tasks
- Question-answering pairs

### Quality Assurance
- Language detection (German text only)
- Content length filtering
- Duplicate removal
- Legal domain validation

## 📈 Expected Output

- **Estimated file size**: 2-4 GB total
- **Sample count**: 10,000-50,000 instruction pairs
- **Languages**: German (de)
- **Domain**: Legal/Juridical

## 🛠️ System Requirements

- **Python**: 3.8+
- **RAM**: 8GB recommended
- **Storage**: 4GB free space
- **Network**: Internet connection for downloads
- **Hardware**: CPU sufficient, GPU optional

## 📝 Usage Notes

1. **Rate Limiting**: Web scraping includes delays to be respectful to servers
2. **Legal Compliance**: Only processes publicly available legal texts
3. **Privacy**: PII is automatically replaced with placeholders
4. **Customization**: Modify `scripts/data_preparation.py` for custom processing

## 🔍 Monitoring Progress

The pipeline provides detailed logging:
- Download progress bars
- Processing status updates
- Error handling and recovery
- Final statistics report

## 📄 License

This dataset preparation tool is for educational and research purposes. Please respect the original sources' terms of use and copyright.

## 🤝 Contributing

To add new data sources or improve processing:
1. Modify `GermanLegalDataProcessor` class
2. Add new scraping methods
3. Update instruction pair generation
4. Test with small datasets first

## ⚠️ Disclaimer

This tool processes publicly available German legal texts for research purposes. Users are responsible for complying with applicable laws and terms of service of data sources.