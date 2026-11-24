"""
ML Training & Benchmarking Pipeline for In-Cabin Driver Fatigue & Distraction Detection.
Trains and evaluates Gradient Boosting and Random Forest classifiers on 5,000 synthetic driving episodes.
Outputs ROC-AUC, Precision, Recall, and Confusion Matrix charts to app/ml/artifacts.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
)
from sklearn.model_selection import train_test_split

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def generate_synthetic_driver_dataset(n_samples: int = 5000, random_state: int = 42):
    """
    Generates annotated feature vectors representing diverse driving states.
    Features:
    [0] ear_mean (0.10 to 0.45)
    [1] mar (0.10 to 0.85)
    [2] blink_duration_ms (100 to 1200)
    [3] head_yaw_deg (-45 to +45)
    [4] head_pitch_deg (-35 to +20)
    [5] phone_detected (0 or 1)
    [6] speed_kmh (0 to 120)
    [7] accel_longitudinal_g (-0.7 to +0.5)
    [8] accel_lateral_g (-0.6 to +0.6)
    """
    np.random.seed(random_state)
    
    # Half attentive, half fatigued/distracted
    n_attentive = n_samples // 2
    n_risky = n_samples - n_attentive

    # Attentive drivers
    ear_att = np.random.normal(0.32, 0.03, n_attentive).clip(0.24, 0.42)
    mar_att = np.random.normal(0.18, 0.04, n_attentive).clip(0.10, 0.35)
    blink_att = np.random.normal(160.0, 30.0, n_attentive).clip(100.0, 250.0)
    yaw_att = np.random.normal(0.0, 5.0, n_attentive).clip(-12.0, 12.0)
    pitch_att = np.random.normal(-2.0, 3.0, n_attentive).clip(-8.0, 5.0)
    phone_att = np.zeros(n_attentive)
    speed_att = np.random.normal(55.0, 15.0, n_attentive).clip(20.0, 95.0)
    long_g_att = np.random.normal(0.02, 0.08, n_attentive).clip(-0.25, 0.20)
    lat_g_att = np.random.normal(0.01, 0.06, n_attentive).clip(-0.18, 0.18)

    X_att = np.column_stack([
        ear_att, mar_att, blink_att, yaw_att, pitch_att, phone_att, speed_att, long_g_att, lat_g_att
    ])
    y_att = np.zeros(n_attentive)

    # Risky drivers (drowsy, microsleep, phone texting, harsh manoeuvres)
    ear_risk = np.random.normal(0.18, 0.05, n_risky).clip(0.08, 0.30)
    mar_risk = np.random.normal(0.55, 0.15, n_risky).clip(0.25, 0.90)
    blink_risk = np.random.normal(520.0, 180.0, n_risky).clip(220.0, 1400.0)
    yaw_risk = np.random.choice([-28.0, 26.0, 2.0], size=n_risky) + np.random.normal(0, 4, n_risky)
    pitch_risk = np.random.normal(-18.0, 8.0, n_risky).clip(-38.0, 0.0)
    phone_risk = np.random.choice([0, 1], size=n_risky, p=[0.45, 0.55])
    speed_risk = np.random.normal(68.0, 22.0, n_risky).clip(20.0, 120.0)
    long_g_risk = np.random.choice([-0.48, 0.38, 0.0], size=n_risky, p=[0.4, 0.3, 0.3]) + np.random.normal(0, 0.05, n_risky)
    lat_g_risk = np.random.choice([-0.42, 0.40, 0.0], size=n_risky, p=[0.35, 0.35, 0.3]) + np.random.normal(0, 0.05, n_risky)

    X_risk = np.column_stack([
        ear_risk, mar_risk, blink_risk, yaw_risk, pitch_risk, phone_risk, speed_risk, long_g_risk, lat_g_risk
    ])
    y_risk = np.ones(n_risky)

    X = np.vstack([X_att, X_risk])
    y = np.concatenate([y_att, y_risk])

    indices = np.arange(len(y))
    np.random.shuffle(indices)
    return X[indices], y[indices]


def train_and_evaluate():
    print("Generating 5,000 driving telemetry episodes...")
    X, y = generate_synthetic_driver_dataset(n_samples=5000)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    print(f"Dataset split: Train = {len(y_train)} samples, Test = {len(y_test)} samples.")

    # 1. Baseline: Heuristic Rule
    y_pred_rule = np.where((X_test[:, 0] < 0.21) | (X_test[:, 1] > 0.58) | (X_test[:, 5] == 1) | (X_test[:, 7] < -0.40), 1, 0)
    rule_acc = accuracy_score(y_test, y_pred_rule)
    rule_prec = precision_score(y_test, y_pred_rule)
    rule_rec = recall_score(y_test, y_pred_rule)
    rule_f1 = f1_score(y_test, y_pred_rule)
    rule_auc = roc_auc_score(y_test, y_pred_rule)

    # 2. Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    y_pred_rf = (y_prob_rf >= 0.5).astype(int)
    rf_acc = accuracy_score(y_test, y_pred_rf)
    rf_prec = precision_score(y_test, y_pred_rf)
    rf_rec = recall_score(y_test, y_pred_rf)
    rf_f1 = f1_score(y_test, y_pred_rf)
    rf_auc = roc_auc_score(y_test, y_prob_rf)

    # 3. Production Model: HistGradientBoostingClassifier
    hgb = HistGradientBoostingClassifier(max_iter=150, max_depth=6, random_state=42)
    hgb.fit(X_train, y_train)
    y_prob_hgb = hgb.predict_proba(X_test)[:, 1]
    y_pred_hgb = (y_prob_hgb >= 0.5).astype(int)
    hgb_acc = accuracy_score(y_test, y_pred_hgb)
    hgb_prec = precision_score(y_test, y_pred_hgb)
    hgb_rec = recall_score(y_test, y_pred_hgb)
    hgb_f1 = f1_score(y_test, y_pred_hgb)
    hgb_auc = roc_auc_score(y_test, y_prob_hgb)

    cm_hgb = confusion_matrix(y_test, y_pred_hgb)

    metrics = {
        "dataset_size": len(y),
        "test_size": len(y_test),
        "models": {
            "Rule_Heuristic_Baseline": {
                "accuracy": round(float(rule_acc), 4),
                "precision": round(float(rule_prec), 4),
                "recall": round(float(rule_rec), 4),
                "f1": round(float(rule_f1), 4),
                "roc_auc": round(float(rule_auc), 4),
            },
            "Random_Forest": {
                "accuracy": round(float(rf_acc), 4),
                "precision": round(float(rf_prec), 4),
                "recall": round(float(rf_rec), 4),
                "f1": round(float(rf_f1), 4),
                "roc_auc": round(float(rf_auc), 4),
            },
            "Drishti_Gradient_Boosting": {
                "accuracy": round(float(hgb_acc), 4),
                "precision": round(float(hgb_prec), 4),
                "recall": round(float(hgb_rec), 4),
                "f1": round(float(hgb_f1), 4),
                "roc_auc": round(float(hgb_auc), 4),
                "confusion_matrix": cm_hgb.tolist(),
            }
        }
    }

    metrics_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    # Generate Visualization Charts
    fpr_rf, tpr_rf, _ = roc_curve(y_test, y_prob_rf)
    fpr_hgb, tpr_hgb, _ = roc_curve(y_test, y_prob_hgb)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)
    fig.patch.set_facecolor("#0b1329")

    # Plot 1: ROC Curve
    ax1 = axes[0]
    ax1.set_facecolor("#111c38")
    ax1.plot(fpr_hgb, tpr_hgb, color="#00e5ff", lw=2.5, label=f"Drishti Gradient Boosting (AUC = {hgb_auc:.4f})")
    ax1.plot(fpr_rf, tpr_rf, color="#00ff88", lw=2.0, linestyle="--", label=f"Random Forest (AUC = {rf_auc:.4f})")
    ax1.plot([0, 1], [0, 1], color="#6b7280", lw=1.5, linestyle=":", label="Random Guess (AUC = 0.5000)")
    ax1.scatter([1 - rule_acc], [rule_rec], color="#ff9900", s=70, zorder=5, label=f"Heuristic Rule (Recall={rule_rec:.2f})")
    ax1.set_title("ROC Curves: Driver State Classification", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
    ax1.set_xlabel("False Positive Rate", color="#94a3b8")
    ax1.set_ylabel("True Positive Rate (Recall)", color="#94a3b8")
    ax1.tick_params(colors="#94a3b8")
    ax1.grid(True, color="#1e293b", linestyle="--", alpha=0.6)
    ax1.legend(loc="lower right", facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=9)

    # Plot 2: Metric Comparison Bar Chart
    ax2 = axes[1]
    ax2.set_facecolor("#111c38")
    categories = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
    rule_vals = [rule_acc * 100, rule_prec * 100, rule_rec * 100, rule_f1 * 100, rule_auc * 100]
    rf_vals = [rf_acc * 100, rf_prec * 100, rf_rec * 100, rf_f1 * 100, rf_auc * 100]
    hgb_vals = [hgb_acc * 100, hgb_prec * 100, hgb_rec * 100, hgb_f1 * 100, hgb_auc * 100]

    x = np.arange(len(categories))
    width = 0.26

    ax2.bar(x - width, rule_vals, width, label="Heuristic Baseline", color="#64748b", alpha=0.9)
    ax2.bar(x, rf_vals, width, label="Random Forest", color="#00ff88", alpha=0.9)
    ax2.bar(x + width, hgb_vals, width, label="Drishti Gradient Boost", color="#00e5ff", alpha=0.95)

    ax2.set_title("Model Benchmarking on Held-Out Test Set (n=1,250)", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, color="#94a3b8", fontsize=10)
    ax2.set_ylabel("Score Percentage (%)", color="#94a3b8")
    ax2.set_ylim(70, 102)
    ax2.tick_params(colors="#94a3b8")
    ax2.grid(True, color="#1e293b", linestyle="--", alpha=0.6, axis="y")
    ax2.legend(loc="lower right", facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=9)

    plt.tight_layout()
    chart_path = os.path.join(ARTIFACTS_DIR, "driver_model_metrics.png")
    plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Saved metric chart to {chart_path}")
    print(f"Drishti Gradient Boosting: Accuracy = {hgb_acc*100:.2f}%, Precision = {hgb_prec*100:.2f}%, Recall = {hgb_rec*100:.2f}%, ROC-AUC = {hgb_auc:.4f}")


if __name__ == "__main__":
    train_and_evaluate()
