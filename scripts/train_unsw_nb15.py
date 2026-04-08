from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split


UNSW_COLUMNS = [
    "srcip",
    "sport",
    "dstip",
    "dsport",
    "proto",
    "state",
    "dur",
    "sbytes",
    "dbytes",
    "sttl",
    "dttl",
    "sloss",
    "dloss",
    "service",
    "sload",
    "dload",
    "spkts",
    "dpkts",
    "swin",
    "dwin",
    "stcpb",
    "dtcpb",
    "smeansz",
    "dmeansz",
    "trans_depth",
    "res_bdy_len",
    "sjit",
    "djit",
    "stime",
    "ltime",
    "sintpkt",
    "dintpkt",
    "tcprtt",
    "synack",
    "ackdat",
    "is_sm_ips_ports",
    "ct_state_ttl",
    "ct_flw_http_mthd",
    "is_ftp_login",
    "ct_ftp_cmd",
    "ct_srv_src",
    "ct_srv_dst",
    "ct_dst_ltm",
    "ct_src_ltm",
    "ct_src_dport_ltm",
    "ct_dst_sport_ltm",
    "ct_dst_src_ltm",
    "attack_cat",
    "label",
]


def load_data(csv_paths: list[str]) -> pd.DataFrame:
    frames = []
    for path in csv_paths:
        df = pd.read_csv(path, header=None, names=UNSW_COLUMNS, low_memory=False)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Hash high-cardinality IP strings into stable numeric buckets.
    for col in ["srcip", "dstip"]:
        out[col] = pd.util.hash_pandas_object(out[col].astype(str), index=False).astype("uint64") % 1_000_003

    # Low-cardinality categorical protocol/state/service to integer codes.
    for col in ["proto", "state", "service"]:
        out[col] = out[col].astype("category").cat.codes

    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.fillna(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train UNSW-NB15 binary threat classifier.")
    parser.add_argument(
        "--data-dir",
        default=r"c:\Users\Tanish Ramgopal\Documents\Tanish\Meta hackathon  docs",
        help="Directory containing UNSW-NB15_1..4.csv",
    )
    parser.add_argument("--output-dir", default="artifacts/unsw_nb15", help="Directory to save model and metrics")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    csv_paths = [str(data_dir / f"UNSW-NB15_{i}.csv") for i in [1, 2, 3, 4]]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(csv_paths)
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)

    feature_cols = [c for c in df.columns if c not in ("label", "attack_cat")]
    X = preprocess_features(df[feature_cols])
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    model = HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_depth=8,
        max_iter=250,
        min_samples_leaf=40,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(round(accuracy_score(y_test, y_pred), 6)),
        "f1": float(round(f1_score(y_test, y_pred), 6)),
        "roc_auc": float(round(roc_auc_score(y_test, y_prob), 6)),
        "rows_total": int(len(df)),
        "rows_train": int(len(X_train)),
        "rows_test": int(len(X_test)),
        "positive_rate": float(round(y.mean(), 6)),
        "class_report": classification_report(y_test, y_pred, output_dict=True),
    }

    model_path = output_dir / "unsw_nb15_binary_hgb.joblib"
    metrics_path = output_dir / "metrics.json"
    joblib.dump({"model": model, "feature_columns": feature_cols}, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps({"model_path": str(model_path), "metrics_path": str(metrics_path), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()

