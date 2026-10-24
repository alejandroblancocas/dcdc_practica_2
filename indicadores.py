"""RoBERTuito, un LDA global y MATTR por intervención."""
import argparse
import os
from collections import Counter

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from tqdm import tqdm

from common import PROCESSED, MODELS, REPORTS, config, prepared_hash, require_file, save_json


def mattr(tokens, window):
    """Media de tipos/tokens en ventanas móviles; O(n), sin cruzar turnos."""
    if window < 1:
        raise ValueError("mattr_window debe ser positivo.")
    if len(tokens) < window:
        return np.nan
    counts = Counter(tokens[:window])
    total = len(counts)
    for i in range(window, len(tokens)):
        old = tokens[i - window]
        counts[old] -= 1
        if counts[old] == 0:
            del counts[old]
        counts[tokens[i]] += 1
        total += len(counts)
    return total / (window * (len(tokens) - window + 1))


def sentiment(df, cfg):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    torch.set_num_threads(min(8, os.cpu_count() or 1))
    torch.manual_seed(cfg["seed"])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    options = {"revision": cfg["sentiment_revision"]}
    tokenizer = AutoTokenizer.from_pretrained(cfg["sentiment_model"], **options)
    model = AutoModelForSequenceClassification.from_pretrained(
        cfg["sentiment_model"], use_safetensors=True, **options).to(device).eval()
    labels = {str(value).upper(): int(key) for key, value in model.config.id2label.items()}
    if set(labels) != {"NEG", "NEU", "POS"}:
        raise ValueError(f"Etiquetas inesperadas del modelo: {labels}")
    order = [labels[key] for key in ("NEG", "NEU", "POS")]
    max_length = min(tokenizer.model_max_length,
                     model.config.max_position_embeddings - model.config.pad_token_id - 1)
    batch_size = cfg["sentiment_batch_size"]
    if batch_size < 1:
        raise ValueError("sentiment_batch_size debe ser positivo.")
    columns = ["p_neg", "p_neu", "p_pos", "share_neg", "share_neu", "share_pos",
               "sentiment", "n_sentences", "n_chunks"]
    result = pd.DataFrame(np.nan, index=df.index, columns=columns)
    result[["n_sentences", "n_chunks"]] = 0
    print(f"RoBERTuito: {device}; máximo {max_length} tokens por fragmento.")
    for row in tqdm(df.itertuples(), total=len(df), desc="Sentimiento"):
        if not row.eligible_nlp or len(row.sentences) == 0:
            continue
        # overflow conserva toda la frase: no se descarta el final de un turno largo.
        encoded = tokenizer(list(row.sentences), truncation=True, max_length=max_length,
                            return_overflowing_tokens=True, padding=False)
        mapping = np.asarray(encoded.pop("overflow_to_sample_mapping"))
        weights = np.array([len(ids) - tokenizer.num_special_tokens_to_add()
                            for ids in encoded["input_ids"]], dtype=float)
        probabilities = []
        with torch.inference_mode():
            for start in range(0, len(mapping), batch_size):
                batch = tokenizer.pad({key: value[start:start + batch_size]
                                       for key, value in encoded.items()},
                                      padding=True, return_tensors="pt")
                batch = {key: value.to(device) for key, value in batch.items()}
                probabilities.append(model(**batch).logits.softmax(-1).cpu().numpy()[:, order])
        chunks = np.concatenate(probabilities)
        sentence_probs = np.zeros((len(row.sentences), 3))
        np.add.at(sentence_probs, mapping, chunks * weights[:, None])
        sentence_probs /= np.bincount(mapping, weights=weights)[:, None]
        probs = sentence_probs.mean(axis=0)
        shares = np.bincount(sentence_probs.argmax(axis=1), minlength=3) / len(sentence_probs)
        result.loc[row.Index] = [*probs, *shares, probs[2] - probs[0],
                                 len(sentence_probs), len(chunks)]
    result.insert(0, "id", df.id)
    result.to_parquet(PROCESSED / "sentiment.parquet", index=False)
    save_json(REPORTS / "sentiment_run.json", {
        "prepared_sha256": prepared_hash(), "model": cfg["sentiment_model"],
        "revision": cfg["sentiment_revision"], "max_length": int(max_length),
        "batch_size": batch_size, "device": device, "eligible_turns": int(result.sentiment.notna().sum()),
        "aggregation": "tokens dentro de frase; frases dentro de turno; turnos dentro de grupo"})


def topics_mattr(df, cfg):
    result = df[["id"]].copy()
    result["mattr"] = [mattr(tokens, cfg["mattr_window"]) for tokens in df.lemmas]
    candidates = df.eligible_nlp & df.topic_tokens.map(len).gt(0)
    documents = df.loc[candidates, "topic_tokens"].map(lambda x: " ".join(x))
    vectorizer = CountVectorizer(tokenizer=str.split, token_pattern=None, lowercase=False,
                                min_df=cfg["lda_min_df"], max_df=cfg["lda_max_df"],
                                max_features=cfg["lda_max_features"])
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError as error:
        raise ValueError("LDA no tiene vocabulario suficiente. Revisa los datos y min_df/max_df.") from error
    nonempty = np.asarray(matrix.sum(axis=1)).ravel() > 0
    indices = documents.index[nonempty]
    matrix = matrix[nonempty]
    lda = LatentDirichletAllocation(n_components=cfg["lda_topics"],
        max_iter=cfg["lda_max_iter"], learning_method="online", batch_size=256,
        random_state=cfg["seed"], n_jobs=cfg["lda_n_jobs"])
    mixtures = lda.fit_transform(matrix)
    topic_columns = [f"topic_{i:02d}" for i in range(cfg["lda_topics"])]
    for i, column in enumerate(topic_columns):
        result[column] = np.nan
        result.loc[indices, column] = mixtures[:, i]
    result.to_parquet(PROCESSED / "topics_mattr.parquet", index=False)
    joblib.dump({"vectorizer": vectorizer, "lda": lda}, MODELS / "lda.joblib")
    vocabulary = vectorizer.get_feature_names_out()
    labels, examples = [], []
    for i, column in enumerate(topic_columns):
        terms = vocabulary[np.argsort(lda.components_[i])[-15:][::-1]].tolist()
        labels.append({"topic": column, "label": "", "top_words": ", ".join(terms)})
        for position in np.argsort(mixtures[:, i])[-3:][::-1]:
            row = df.loc[indices[position]]
            examples.append({"topic": column, "weight": mixtures[position, i], "id": row.id,
                             "party": row.party, "month": row.month, "source_url": row.source_url,
                             "excerpt": row.text_clean[:1500]})
    pd.DataFrame(labels).to_csv(REPORTS / "topic_labels.csv", index=False)
    pd.DataFrame(examples).to_csv(REPORTS / "topic_examples.csv", index=False)
    save_json(REPORTS / "topics_run.json", {
        "prepared_sha256": prepared_hash(),
        "parameters": {key: value for key, value in cfg.items() if key.startswith("lda_") or key in {"mattr_window", "seed"}},
        "modeled_turns": int(len(indices)), "vocabulary_size": int(len(vocabulary))})
    print(f"LDA: {len(indices):,} turnos, {len(vocabulary):,} términos, {cfg['lda_topics']} tópicos.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", choices=["sentimiento", "topicos"], help="topicos también calcula MATTR")
    args = parser.parse_args()
    cfg = config()
    df = pd.read_parquet(require_file(PROCESSED / "corpus_clean.parquet"))
    if args.solo in (None, "sentimiento"):
        sentiment(df, cfg)
    if args.solo in (None, "topicos"):
        topics_mattr(df, cfg)
    print("Indicadores guardados en data/processed/.")


if __name__ == "__main__":
    main()
