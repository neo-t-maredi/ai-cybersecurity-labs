# ai-cybersecurity-labs
Reproducible experiments in AI-driven cybersecurity, threat detection, classification and model eval


# Lab 01: SMS Spam Classification

Baseline spam classification on the UCI SMS Spam Collection. The dataset audit is complete. No models have been trained yet.

## Status

- [x] Dataset audit
- [ ] Resolve row-count discrepancy (see below)
- [ ] Baseline: Multinomial Naïve Bayes vs Logistic Regression on TF-IDF features
- [ ] Error analysis of false positives and false negatives

## Dataset

SMS Spam Collection, UCI Machine Learning Repository:
https://archive.ics.uci.edu/dataset/228/sms+spam+collection

Each record is a label (`ham` or `spam`) and the message text, tab-separated. The raw file is not committed to this repository. Download it from UCI and place it at:

```
TODO: data/raw/SMSSpamCollection
```

Citation: Almeida, T. A., Gómez Hidalgo, J. M., and Yamakami, A. (2011). Contributions to the Study of SMS Spam Filtering: New Collection and Results. Proceedings of the 2011 ACM Symposium on Document Engineering.

## Setup

```bash
TODO: python version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the audit

From the repository root:

```bash
python labs/01-spam-classification/src/audit_dataset.py
```

The script reads the raw file without modifying it and reports class counts, missing values, invalid labels, duplicates and conflicting labels.

## Audit summary

| Metric | Result |
|---|---:|
| Messages parsed | 5,572 |
| Ham | 4,825 (86.6%) |
| Spam | 747 |
| Unique messages | 5,169 |
| Redundant duplicate rows | 403 |
| Conflicting labels | 0 |

Open issue: UCI lists 5,574 messages (4,827 ham). The parse returns two fewer ham messages, which suggests quote characters are merging lines during parsing. These figures may change once that is fixed.

Full audit write-up: TODO: link to audit document

## Planned method

1. Remove exact duplicate messages.
2. Split into training and test sets with stratification. Seed: TODO. Test fraction: TODO.
3. Fit TF-IDF on the training set only.
4. Train Multinomial Naïve Bayes and Logistic Regression on the same split.
5. Report precision, recall, F1 and confusion matrices. Accuracy is not the primary metric because predicting `ham` for every message scores about 86.6%.

## Limitations

The dataset is historical SMS traffic and does not represent current phishing campaigns or email. Removing exact duplicates does not catch near-duplicates or messages built from the same campaign template. A single train/test split gives a limited estimate of performance.
