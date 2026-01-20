# Email Extraction - Output Files

## Overview
LLM-powered extraction of shipment details from freight forwarding emails using Groq API.

## Code Flow

```
emails_input.json → main.py → Groq LLM → output.json → evaluate.py → accuracy
```

1. **Load emails** from `emails_input.json`
2. **Format prompt** with email subject + body
3. **Call Groq API** with retry logic for rate limits
4. **Parse JSON response** and validate with Pydantic
5. **Save results** to `output.json`
6. **Evaluate** against `ground_truth.json`

## Approach & Intuition

### Prompt Evolution
- **V1 (66.78%)**: Basic extraction prompt - failed on port code formats and abbreviations
- **V2 (83.56%)**: Added port abbreviation mappings and multi-shipment handling rules
- **V3 (83.78%)**: Embedded full port reference table with explicit code→name mappings

### Key Learnings
- LLM needs **explicit port code reference** to output correct 5-letter UN/LOCODEs
- **Multi-shipment emails** require clear rules (use first shipment's codes, combine names)
- **RT (Revenue Ton)** handling needed explicit conversion rules
- Temperature=0 ensures reproducible results

## Files

| File | Description |
|------|-------------|
| `main.py` | Main extraction script |
| `prompts.py` | Prompt versions (V1, V2, V3) |
| `schemas.py` | Pydantic models |
| `evaluate.py` | Accuracy evaluation |
| `output.json` | Extracted results |
| `stats.txt` | Accuracy metrics |

## Usage

```bash
python main.py      # Run extraction
python evaluate.py  # Check accuracy
```

## Results

| Prompt | Accuracy | Correct |
|--------|----------|---------|
| V1 | 66.78% | 301/450 |
| V2 | 83.56% | 376/450 |
| V3 | 83.78% | 377/450 |

## Model
- **LLM**: Groq (llama-3.1-8b-instant)
- **Temperature**: 0

### Model Choice & Constraints

- Primary target model: `llama-3.1-70b-versatile` (as recommended)
- Practical constraint: Groq free tier frequently hit token exhaustion / rate limits during batch processing of 50 emails.
- Final extraction was run using `llama-3.1-8b-instant` to ensure:
  - Full dataset completion
  - Reproducible results
  - No skipped emails

The code is model-agnostic and can be switched back to 70B by changing a single configuration value.

---

## System Design Questions

### 1. Scale: 10,000 emails/day, 99% in 5 min, $500/month budget

**Architecture:**
- **Queue**: AWS SQS or Redis for email ingestion
- **Workers**: Auto-scaling Lambda/ECS workers pulling from queue
- **LLM**: Batch API calls to Groq/OpenAI (~$100/month for 10K emails)
- **Storage**: PostgreSQL for results + S3 for raw emails

**Why it works:**
- Queue decouples ingestion from processing, handles spikes
- Parallel workers meet 5-min SLA
- Total cost: ~$200/month (well under budget)

---

### 2. Monitoring: Accuracy drops 90% → 70%

**Detection:**
- Sample 5% of daily extractions for human review
- Track field-level accuracy metrics daily
- Alert on >5% drop in any metric
- Monitor null rates and confidence scores

**Investigation:**
1. Check if LLM provider changed models
2. Analyze error patterns by field (port codes? incoterms?)
3. Compare failing emails to training data - new patterns?
4. A/B test prompt fixes on problematic samples before deploying

---

### 3. Multilingual: 30% Mandarin, 20% Hindi

**Changes:**
- Add language detection (langdetect or LLM-based)
- Create language-specific prompts with local port names
- Expand port reference with transliterations
- Option: Translate to English first, then extract

**Evaluation:**
- Separate ground truth datasets per language
- Native speaker review for annotation
- Report per-language accuracy metrics
- Accept lower initial accuracy for new languages, iterate
