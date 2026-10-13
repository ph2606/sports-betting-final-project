"""Training-only shift/redundancy filters and chronological forward selection."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import softmax
from scipy.stats import ks_2samp, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .metrics import classification_metrics, encode_results, estimator_logits


def bh_adjust(p_values):
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted = np.minimum.accumulate((p[order] * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty_like(p)
    result[order] = np.minimum(adjusted, 1)
    return result


def filter_features(train, *, missing_limit=0.4, correlation_limit=0.9, shift_alpha=0.01, shift_effect=0.15):
    """Use early versus late *training* seasons for KS; never inspect held-out seasons."""
    candidates = [name for name in train if name.startswith("feat_")]
    seasons = sorted(train.season.unique())
    early = train.season.isin(seasons[: max(1, len(seasons) // 2)])
    late = train.season.isin(seasons[max(1, len(seasons) // 2):])
    y = encode_results(train.result)
    records = []
    for name in candidates:
        values = pd.to_numeric(train[name], errors="coerce").replace([np.inf, -np.inf], np.nan)
        a, b = values[early].dropna(), values[late].dropna()
        if len(a) >= 30 and len(b) >= 30:
            ks = ks_2samp(a, b, method="asymp")
            statistic, pvalue = float(ks.statistic), float(ks.pvalue)
        else:
            statistic, pvalue = 0.0, 1.0
        association = 0.0
        if values.nunique() > 1:
            filled = values.fillna(values.median())
            association = max(abs(float(spearmanr(filled, y == k).statistic)) for k in range(3))
        records.append({"feature": name, "train_missing_rate": float(values.isna().mean()),
                        "n_distinct": int(values.nunique()), "ks_statistic": statistic,
                        "ks_pvalue": pvalue, "target_association": association,
                        "drop_reason": "", "redundant_with": ""})
    audit = pd.DataFrame(records)
    audit["ks_qvalue"] = bh_adjust(audit.ks_pvalue)
    for idx, row in audit.iterrows():
        if row.train_missing_rate > missing_limit:
            audit.at[idx, "drop_reason"] = "excess_training_missingness"
        elif row.n_distinct <= 1:
            audit.at[idx, "drop_reason"] = "constant_in_training"
        elif row.ks_qvalue < shift_alpha and row.ks_statistic > shift_effect:
            audit.at[idx, "drop_reason"] = "early_late_training_distribution_shift"
    available = audit.loc[audit.drop_reason.eq("")].sort_values(
        ["target_association", "feature"], ascending=[False, True]
    ).feature.tolist()
    if not available:
        raise ValueError("Training-only filters removed every feature")
    correlations = train[available].corr(method="spearman").abs()
    kept = []
    for name in available:
        redundant = next((other for other in kept if correlations.at[name, other] >= correlation_limit), None)
        if redundant:
            idx = audit.index[audit.feature.eq(name)][0]
            audit.at[idx, "drop_reason"] = "spearman_redundancy"
            audit.at[idx, "redundant_with"] = redundant
        else:
            kept.append(name)
    audit["eligible_after_filters"] = audit.drop_reason.eq("")
    return kept, audit


def chronological_folds(train):
    seasons = sorted(train.season.unique())
    if len(seasons) < 4:
        raise ValueError("Forward selection requires at least four training seasons")
    folds = []
    for season in seasons[-2:]:
        a = train.season.lt(season).to_numpy()
        b = train.season.eq(season).to_numpy()
        if train.loc[a, "match_date"].max() >= train.loc[b, "match_date"].min():
            raise ValueError("Forward-selection fold dates overlap")
        folds.append((a, b, season))
    return folds


def forward_select(train, candidates, *, objective, max_features=8, candidate_limit=18):
    """Budgeted greedy wrapper using logistic regression and two expanding season folds."""
    pool = list(candidates[:candidate_limit])
    folds = chronological_folds(train)
    y = encode_results(train.result)
    selected, audit = [], []
    previous = -np.inf
    for step in range(min(max_features, len(pool))):
        scores = []
        for name in pool:
            names = selected + [name]
            results = []
            for earlier, validation, season in folds:
                estimator = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                                          LogisticRegression(C=1, max_iter=1000, random_state=42))
                estimator.fit(train.loc[earlier, names], y[earlier])
                p = softmax(estimator_logits(estimator, train.loc[validation, names]), axis=1)
                metrics = classification_metrics(y[validation], p)
                score = metrics["accuracy"] if objective == "accuracy" else -metrics["classwise_ece_10"]
                results.append(score)
            score = float(np.mean(results))
            scores.append((score, name))
            audit.append({"objective": objective, "step": step + 1, "candidate": name,
                          "mean_forward_score": score, "selected": False,
                          "validation_seasons": ",".join(f[2] for f in folds)})
        score, name = sorted(scores, key=lambda item: (-item[0], item[1]))[0]
        if selected and score <= previous + 1e-4:
            break
        selected.append(name)
        pool.remove(name)
        previous = score
        for row in audit:
            if row["step"] == step + 1 and row["candidate"] == name:
                row["selected"] = True
    return selected, pd.DataFrame(audit)
