# Language classification


## Step 1: Predict languages for "all" works
`01_predict_lang.py` iterates through the database and uses fasttext to classify the language by title.
You need to [download the full model](https://fasttext.cc/docs/en/language-identification.html) into this directory.
It is assumed to be executed from the scripts repository

```bash
export PYTHONPATH=/home/tim/workspace/nacsos-academic-search/scripts; python -u sampling/language/predict_lang_cursor.py 2> ../data/log.txt
```

## Step 2: Update the schema


## Step 3: Add data to column


## Step 4: Create down-sampled English-only table (optional)