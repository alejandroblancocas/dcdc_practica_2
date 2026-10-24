"""Descarga la muestra de la Entrega 1 y prepara tres representaciones del texto."""
import json
import re
import shutil
import unicodedata

import pandas as pd
import spacy
from huggingface_hub import hf_hub_download
from tqdm import tqdm

from common import ROOT, RAW, PROCESSED, REPORTS, config, save_json

HEADER = re.compile(r"^(?:El|La) señor(?:a)?\s+[^:\n]{1,350}:\s*")
LANGUAGE = re.compile(r"\ben\s+(?:catalán|euskera|vasco|gallego|bable|asturiano|aragonés|valenciano)\b", re.I)
TYPOGRAPHY = str.maketrans({"\x85": "…", "\x91": "‘", "\x92": "’", "\x93": "“", "\x94": "”", "\x96": "–", "\x97": "—"})
COURTESY = {"señor", "señora", "señoría", "presidente", "presidenta", "gracia"}
NEGATION = {"no", "ni", "nunca", "jamás", "tampoco", "sin"}


def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).translate(TYPOGRAPHY)).strip()


def clean_text(text, notes):
    """Quita solo la cabecera inicial y las acotaciones registradas por la fuente."""
    if pd.isna(notes) or not str(notes).strip():
        notes = {}
    else:
        notes = json.loads(notes)  # Un JSON mal formado requiere revisión, no se ignora.
    annotations = notes.get("inline", []) + notes.get("paragraphs", [])
    text = normalize(text)
    text, header_count = HEADER.subn("", text, count=1)
    language_review = any(LANGUAGE.search(note) for note in annotations)
    for note in sorted(set(annotations), key=len, reverse=True):
        if note.strip():
            text = text.replace(normalize(note), " ")
    return normalize(text), header_count == 0, language_review


def lexical_tokens(doc):
    """Lemas alfabéticos; descompone las contracciones españolas al y del."""
    tokens = []
    for token in doc:
        if not token.is_alpha:
            continue
        if token.lower_ in {"al", "del"}:
            tokens.extend(["a" if token.lower_ == "al" else "de", "el"])
        else:
            lemma = token.lemma_.lower().strip()
            if lemma.isalpha():
                tokens.append(lemma)
    return tokens


def main():
    cfg = config()
    source = hf_hub_download(repo_id=cfg["dataset"], repo_type="dataset",
                             filename="data/raw/political_corpus_es.parquet",
                             revision=cfg["dataset_revision"])
    raw_path = RAW / "political_corpus_es.parquet"
    shutil.copyfile(source, raw_path)
    df = pd.read_parquet(raw_path)
    required = {"id", "timestamp", "text", "party", "legislature", "session_id",
                "speaker_name", "text_editorial_notes", "source_url"}
    if missing := required - set(df):
        raise ValueError(f"Faltan columnas: {sorted(missing)}")
    n_raw = len(df)
    df = df.drop_duplicates().copy()
    n_duplicates = n_raw - len(df)
    dates = pd.to_datetime(df.timestamp, format="%Y-%m-%d", errors="coerce")
    valid = dates.notna() & df.legislature.notna()
    for column in ("id", "text", "party", "session_id"):
        valid &= df[column].notna() & df[column].astype(str).str.strip().ne("")
    df.loc[~valid].to_csv(REPORTS / "excluded_invalid.csv", index=False)
    n_invalid = int((~valid).sum())
    df = df.loc[valid].copy()
    if df.empty:
        raise ValueError("No quedan registros válidos.")
    if df.id.duplicated().any():
        raise ValueError("Hay IDs repetidos con contenido distinto; revisar antes de continuar.")
    df["date"] = dates.loc[valid].dt.strftime("%Y-%m-%d")
    df["month"] = dates.loc[valid].dt.strftime("%Y-%m")
    cleaned = [clean_text(t, n) for t, n in zip(df.text, df.text_editorial_notes)]
    df[["text_clean", "header_review", "language_review"]] = pd.DataFrame(cleaned, index=df.index)
    df["eligible_nlp"] = ~(df.header_review | df.language_review) & df.text_clean.ne("")
    df = df.sort_values(["date", "id"]).reset_index(drop=True)

    nlp = spacy.load(cfg["spacy_model"], disable=["ner", "parser"])
    nlp.add_pipe("sentencizer")
    stopwords = (set(nlp.Defaults.stop_words) | COURTESY) - NEGATION
    (REPORTS / "stopwords_lda.txt").write_text("\n".join(sorted(stopwords)) + "\n", encoding="utf-8")
    sentences, lemmas, topic_tokens = [], [], []
    inputs = df.text_clean.where(df.eligible_nlp, "")
    for doc in tqdm(nlp.pipe(inputs, batch_size=64), total=len(df), desc="Preparación"):
        tokens = lexical_tokens(doc)
        sentences.append([s.text.strip() for s in doc.sents if any(t.is_alpha for t in s)])
        lemmas.append(tokens)
        topic_tokens.append([t for t in tokens if t not in stopwords])
    df["sentences"], df["lemmas"], df["topic_tokens"] = sentences, lemmas, topic_tokens
    df["n_tokens"] = [len(tokens) for tokens in lemmas]
    df.to_parquet(PROCESSED / "corpus_clean.parquet", index=False)
    df.loc[~df.eligible_nlp, ["id", "date", "party", "header_review", "language_review",
                            "text_clean", "source_url"]].to_csv(REPORTS / "review_texts.csv", index=False)
    summary = {"dataset": cfg["dataset"], "revision": cfg["dataset_revision"],
               "raw_rows": n_raw, "exact_duplicates_removed": n_duplicates,
               "invalid_rows_excluded": n_invalid, "retained_rows": len(df),
               "eligible_nlp": int(df.eligible_nlp.sum()),
               "language_review": int(df.language_review.sum()),
               "header_review": int(df.header_review.sum()),
               "date_min": df.date.min(), "date_max": df.date.max(),
               "spacy_version": spacy.__version__, "spacy_model_version": nlp.meta["version"]}
    save_json(REPORTS / "cleaning_summary.json", summary)
    doc_path = ROOT / "data_cleaning.md"
    marker = "<!-- RESUMEN_AUTOMATICO -->"
    base = doc_path.read_text(encoding="utf-8").split(marker)[0]
    doc_path.write_text(base + marker + "\n\n## Resultado de la ejecución\n\n```json\n"
                        + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    print(f"Preparados {len(df):,} turnos; {df.eligible_nlp.sum():,} aptos para indicadores lingüísticos.")


if __name__ == "__main__":
    main()
