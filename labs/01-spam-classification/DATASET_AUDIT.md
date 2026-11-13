:::writing{variant="document" id="58321"}
# Dataset Audit: SMS Spam Collection

**Date:** 13 November 2026  
**Dataset:** [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection)  
**Status:** Data inspection complete. Model evaluation pending.

## 1. Scope

What the purpose of this audit was, was to examine the UCI SMS Spam Collection. Then I'd like to use it to train and evaluate spam classifiers (largely based of my learnings in the AI for Cybersecurity by John Hopkins). The objective is to establish the class distribution, identify duplicate records and check for inconsistencies that could affect the evaluation.

The dataset contains labelled SMS messages, not emails. 

## 2. Parsing and validation

First, I loaded the tab-separated source file using pandas. The initial run returned 5,572 messages, although the original file contained 5,574 lines. Both missing records I labelled as `ham`.

NOTE!!: NB!
An inconsistency came from pandas' default treatment of quotation marks. SMS messages contain quotation marks as ordinary text, but the CSV parser can interpret them as field delimiters. This caused two records to be combined during parsing.


I changed the reader to disable quote interpretation:

```python
import csv
import pandas as pd

df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "text"],
    encoding="utf-8",
    quoting=csv.QUOTE_NONE,
)
```

After that the next run returned 5,574 messages: 4,827 ham and 747 spam. These figures match the published dataset totals. 

## 3. Audit findings

| Check | Result |
|---|---:|
| Records parsed | 5,574 |
| Ham | 4,827 |
| Spam | 747 |
| Missing labels or text | 0 |
| Invalid labels | 0 |
| Redundant duplicate rows | 403 |
| Rows belonging to duplicate groups | 684 |
| Distinct duplicate groups | 281 |
| Conflicting labels for identical text | 0 |
| Unique message texts | 5,171 |

### Class distribution

Ham accounts for approximately 86.6% of the dataset, with spam making up the remaining 13.4%.

Findings: 

This posits accuracy as a poor standalone measure. Predicting `ham` for every message would produce approximately 86.6% accuracy while missing every spam message. (this can lead to an ambiguity between causation and correlation)

Therefore, accuracy alone won't tell us how well the models detect spam. I'll also measure precision, recall and F1(F1 score is a measure of how well a classification model balances precision and recall), then look at which messages were classified incorrectly.

False positives matter here. A legitimate bank alert or delivery notification marked as spam could mean someone misses an important message.

### Duplicate records

The audit found 403 redundant records. A further check identified 684 rows belonging to 281 groups of repeated messages. There were no cases where identical message text carried conflicting labels.

If identical messages appear in both training and testing partitions, the reported performance may be artificially high. To avoid this, exact duplicates will be removed before the dataset is split.

This does not address near-duplicates. Messages that differ only in a telephone number, URL or small wording change may still appear in separate partitions. That remains a limitation of the first evaluation.

After exact deduplication, 5,171 distinct message texts remain available for modelling.

## 4. Evaluation design

The first experiment will compare Multinomial Naïve Bayes and Logistic Regression using TF-IDF features.

Both models will use the same training and test records. The implementation will use a stratified split, record the random seed and fit the vectorizer on training data only. The split ratio and seed will be documented once implemented.

The comparison will report:

- Spam precision, recall and F1.
- True positives, true negatives, false positives and false negatives.
- Class support and overall accuracy for context.
- Examples and causes of classification errors, where the dataset permits meaningful inspection.

The goal is to determine how these two conventional classifiers perform on the same held-out messages, particularly where they disagree. More complex models are outside the scope of this first experiment.

## 5. Limitations

SMS Spam Collection is historical and does not represent contemporary enterprise email traffic. Its results cannot be used as evidence of effectiveness against modern phishing campaigns (only a local project for analysis and insight).

The simple dataset also lacks information needed to assess campaign-level separation, changes in attacker behaviour over time or operational false-positive rates. Exact deduplication reduces one source of leakage but does not eliminate all related-message overlap.

A single train/test split will provide an initial comparison rather than a definitive performance estimate. No classifier has been evaluated against this dataset.

## Reproduction

The audit was run locally using Python 3.12.3 and pandas. The exact installed package versions are recorded in the repository's `requirements.txt`.

From the repository root:

```bash
python labs/01-spam-classification/src/audit_dataset.py
```

The original dataset is excluded from Git. It can be downloaded from the UCI Machine Learning Repository using the source link above.
::