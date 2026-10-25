"""Tablas y gráficos mensuales; legislaturas como salida opcional."""
import argparse
import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import PROCESSED, REPORTS, config, prepared_hash, require_file

METRICS = ["sentiment", "p_neg", "p_neu", "p_pos", "share_neg", "share_neu", "share_pos", "mattr"]


def aggregate(df, keys, topics, calendar=None):
    groups = df.groupby(keys, observed=True)
    counts = groups.agg(n_turns=("id", "size"), n_sessions=("session_id", "nunique"),
                        n_speakers=("speaker_name", "nunique"),
                        n_sentiment=("sentiment", "count"), n_mattr=("mattr", "count"),
                        n_topics=(topics[0], "count"))
    result = counts.join(groups[METRICS + topics].mean())
    if calendar is not None:
        if keys == ["month"]:
            index = pd.Index(calendar, name="month")
        else:
            index = pd.MultiIndex.from_product([calendar, sorted(df.party.unique())], names=keys)
        result = result.reindex(index)
    result[counts.columns] = result[counts.columns].fillna(0).astype(int)
    result["coverage"] = np.where(result.n_turns.eq(0), "sin_registros_en_muestra", "con_registros")
    return result.reset_index()


def plot_lines(monthly, by_party):
    specs = [("n_turns", "Turnos de la muestra"), ("sentiment", "Sentimiento medio"),
             ("mattr", "MATTR medio")]

    def draw(ax, data, metric, title):
        ax.plot(pd.to_datetime(data.month), data[metric], marker="o", markersize=2, linewidth=1)
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=.2)
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        if metric == "sentiment":
            ax.set_ylim(-1, 1)
            ax.axhline(0, color="gray", linewidth=.6)
        elif metric == "mattr":
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(bottom=0)

    fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True, layout="constrained")
    for ax, (metric, label) in zip(axes, specs):
        draw(ax, monthly, metric, label)
    fig.suptitle("Indicadores mensuales · muestra de la Entrega 1")
    fig.savefig(REPORTS / "graficas" / "monthly_overview.png", dpi=160)
    plt.close(fig)
    parties = sorted(by_party.party.unique())
    fig, axes = plt.subplots(len(parties), 3, figsize=(15, 2.5 * len(parties)),
                             squeeze=False, sharex=True, layout="constrained")
    for i, party in enumerate(parties):
        data = by_party.loc[by_party.party.eq(party)]
        for ax, (metric, label) in zip(axes[i], specs):
            draw(ax, data, metric, f"{party} · {label}")
    fig.suptitle("Indicadores mensuales por familia de partido")
    fig.savefig(REPORTS / "graficas" / "monthly_by_party.png", dpi=160)
    plt.close(fig)


def plot_topics(monthly, by_party, topics):
    labels = pd.read_csv(REPORTS / "topic_labels.csv").fillna("").set_index("topic")
    names = []
    for topic in topics:
        row = labels.loc[topic]
        label = row.label.strip() or ", ".join(row.top_words.split(", ")[:3])
        names.append(textwrap.fill(f"{topic}: {label}", 42))
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad("#dddddd")

    def draw(ax, data, title):
        matrix = np.ma.masked_invalid(data[topics].to_numpy(dtype=float).T)
        image = ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=1)
        ticks = np.unique(np.linspace(0, len(data) - 1, min(15, len(data))).astype(int))
        ax.set_xticks(ticks, data.month.iloc[ticks], rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(topics)), names, fontsize=8)
        ax.set_title(title, fontsize=11)
        return image

    fig, ax = plt.subplots(figsize=(15, 7), layout="constrained")
    image = draw(ax, monthly, "Proporción media de tópicos por mes · gris = sin estimación")
    fig.colorbar(image, ax=ax, label="Proporción media por turno")
    fig.savefig(REPORTS / "topics_monthly.png", dpi=160)
    plt.close(fig)
    parties = sorted(by_party.party.unique())
    fig, axes = plt.subplots(len(parties), 1, figsize=(15, 4 * len(parties)),
                             squeeze=False, layout="constrained")
    for ax, party in zip(axes[:, 0], parties):
        image = draw(ax, by_party.loc[by_party.party.eq(party)], party)
    fig.colorbar(image, ax=list(axes[:, 0]), label="Proporción media por turno")
    fig.suptitle("Tópicos mensuales por partido · gris = sin estimación")
    fig.savefig(REPORTS / "topics_by_party.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legislaturas", action="store_true", help="Añade dos tablas por legislatura")
    args = parser.parse_args()
    config()
    df = pd.read_parquet(require_file(PROCESSED / "corpus_clean.parquet"))
    fingerprint = prepared_hash()
    for filename in ("sentiment_run.json", "topics_run.json"):
        run = json.loads(require_file(REPORTS / filename).read_text(encoding="utf-8"))
        if run["prepared_sha256"] != fingerprint:
            raise ValueError(f"{filename} pertenece a otra preparación. Recalcula sus indicadores.")
    for filename in ("sentiment.parquet", "topics_mattr.parquet"):
        indicators = pd.read_parquet(require_file(PROCESSED / filename))
        if set(df.id) != set(indicators.id):
            raise ValueError(f"Los IDs de {filename} no coinciden con los datos preparados.")
        df = df.merge(indicators, on="id", how="left", validate="one_to_one")
    topics = sorted(column for column in df if column.startswith("topic_") and column != "topic_tokens")
    calendar = pd.period_range(df.month.min(), df.month.max(), freq="M").astype(str)
    monthly = aggregate(df, ["month"], topics, calendar)
    by_party = aggregate(df, ["month", "party"], topics, calendar)
    df.to_parquet(PROCESSED / "interventions_indicators.parquet", index=False)
    monthly.to_csv(PROCESSED / "monthly.csv", index=False)
    by_party.to_csv(PROCESSED / "monthly_party.csv", index=False)
    if args.legislaturas:
        aggregate(df, ["legislature"], topics).to_csv(PROCESSED / "legislature.csv", index=False)
        aggregate(df, ["legislature", "party"], topics).to_csv(PROCESSED / "legislature_party.csv", index=False)
    plot_lines(monthly, by_party)
    plot_topics(monthly, by_party, topics)
    print("Tablas en data/processed/ y cuatro gráficos en reports/.")


if __name__ == "__main__":
    main()
