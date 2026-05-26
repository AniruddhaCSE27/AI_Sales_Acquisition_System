import json
from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None

DATA = Path("../datasets/dummy_leads.csv")
REGISTRY = Path("registry")
REGISTRY.mkdir(exist_ok=True)


def main():
    df = pd.read_csv(DATA)
    features = ["budget", "engagement_score", "sentiment_score", "source_quality", "response_minutes"]
    x = df[features]
    y = df["converted"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)
    models = {
        "logistic_regression": Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=500))]),
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=42),
    }
    if XGBClassifier:
        models["xgboost"] = XGBClassifier(n_estimators=120, max_depth=4, learning_rate=0.08, eval_metric="logloss")
    scores = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict_proba(x_test)[:, 1]
        scores[name] = float(roc_auc_score(y_test, pred))
    (REGISTRY / "metrics.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")
    print(scores)


if __name__ == "__main__":
    main()

