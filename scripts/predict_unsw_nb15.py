from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from train_unsw_nb15 import UNSW_COLUMNS, preprocess_features


def load_unsw_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, header=None, names=UNSW_COLUMNS, low_memory=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict attack probabilities for UNSW-NB15 CSV.")
    parser.add_argument("--input-csv", required=True, help="Path to UNSW-NB15_X.csv")
    parser.add_argument(
        "--model-path",
        default="artifacts/unsw_nb15/unsw_nb15_binary_hgb.joblib",
        help="Path to saved model artifact",
    )
    parser.add_argument(
        "--output-csv",
        default="artifacts/unsw_nb15/predictions.csv",
        help="Output CSV path with predictions",
    )
    args = parser.parse_args()

    model_bundle = joblib.load(args.model_path)
    model = model_bundle["model"]
    feature_columns = model_bundle["feature_columns"]

    df = load_unsw_csv(Path(args.input_csv))
    X = preprocess_features(df[feature_columns])

    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)

    out = pd.DataFrame(
        {
            "srcip": df["srcip"].astype(str),
            "dstip": df["dstip"].astype(str),
            "proto": df["proto"].astype(str),
            "service": df["service"].astype(str),
            "pred_label": pred,
            "pred_attack_prob": proba,
        }
    )

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)

    summary = {
        "rows_scored": int(len(out)),
        "pred_attack_rate": float(round(float(out["pred_label"].mean()), 6)),
        "avg_attack_probability": float(round(float(out["pred_attack_prob"].mean()), 6)),
        "output_csv": str(output_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

