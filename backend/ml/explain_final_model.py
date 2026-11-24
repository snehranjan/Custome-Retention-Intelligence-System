"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 5: Model Explainability
Description: Extracts Logistic Regression coefficients and calculates odds ratios (exp(beta))
             from the refitted production pipeline (models/phase5/final_churn_pipeline.joblib).
             Generates feature coefficient rankings, visualizations of top positive/negative predictors,
             and exports an in-depth academic explainability report (reports/phase5/model_explainability_report.md).

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

# Set Matplotlib config directory to avoid permission warnings on Windows
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
os.environ["MPLCONFIGDIR"] = os.path.join(PROJECT_ROOT, "reports", "figures", ".mplconfig")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib.pyplot as plt
import seaborn as sns

# Paths
FINAL_PIPELINE_PATH = os.path.join(PROJECT_ROOT, "models", "phase5", "final_churn_pipeline.joblib")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures", "phase5")

COEFFICIENTS_CSV_PATH = os.path.join(REPORTS_DIR, "feature_coefficients.csv")
EXPLAINABILITY_REPORT_PATH = os.path.join(REPORTS_DIR, "model_explainability_report.md")

TOP15_PLOT_PATH = os.path.join(FIGURES_DIR, "feature_coefficients_top15.png")
OVERVIEW_PLOT_PATH = os.path.join(FIGURES_DIR, "feature_coefficients_overview.png")


def explain_final_model():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 5 — MODEL EXPLAINABILITY & COEFFICIENT ANALYSIS")
    print("=" * 80)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # 1. Load Final Pipeline
    print(f"\n1. Loading final fitted pipeline from: {FINAL_PIPELINE_PATH}")
    assert os.path.exists(FINAL_PIPELINE_PATH), f"Missing final pipeline: {FINAL_PIPELINE_PATH}"
    pipeline = joblib.load(FINAL_PIPELINE_PATH)

    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    # 2. Extract Feature Names and Coefficients
    print("\n2. Extracting transformed feature names and coefficients...")
    feature_names = preprocessor.get_feature_names_out()
    coefs = classifier.coef_[0]
    intercept = classifier.intercept_[0]

    n_features = len(feature_names)
    assert len(coefs) == n_features, f"Mismatch: {len(coefs)} coefficients vs {n_features} features"
    print(f"   Total transformed features: {n_features}")
    print(f"   Model Intercept (beta_0)   : {intercept:.4f} (Base log-odds at reference)")

    # 3. Create DataFrame
    odds_ratios = np.exp(coefs)
    abs_coefs = np.abs(coefs)
    directions = ["Positive" if c > 0 else "Negative" for c in coefs]

    # Clean feature names for presentation
    clean_names = []
    feature_types = []
    for f in feature_names:
        if f.startswith("num__"):
            raw_f = f.replace("num__", "")
            if raw_f.startswith("missingindicator_"):
                clean_names.append(raw_f.replace("missingindicator_", "missing_") + " [Missing Indicator]")
                feature_types.append("Missingness Indicator")
            else:
                clean_names.append(raw_f + " (Standardized)")
                feature_types.append("Numerical (Standardized)")
        elif f.startswith("cat__"):
            clean_names.append(f.replace("cat__", ""))
            feature_types.append("Categorical (One-Hot)")
        else:
            clean_names.append(f)
            feature_types.append("Other")

    df_coefs = pd.DataFrame({
        "feature_name": feature_names,
        "clean_feature_name": clean_names,
        "feature_type": feature_types,
        "coefficient": np.round(coefs, 6),
        "absolute_coefficient": np.round(abs_coefs, 6),
        "direction": directions,
        "odds_ratio": np.round(odds_ratios, 6)
    })

    # Sort by absolute magnitude descending
    df_coefs_sorted = df_coefs.sort_values(by="absolute_coefficient", ascending=False).reset_index(drop=True)

    # Save to CSV
    df_coefs_sorted.to_csv(COEFFICIENTS_CSV_PATH, index=False)
    print(f"   Saved feature coefficients table ({len(df_coefs_sorted)} rows) to: {COEFFICIENTS_CSV_PATH}")

    # Top positive and negative predictors
    top_pos = df_coefs[df_coefs["coefficient"] > 0].sort_values(by="coefficient", ascending=False).head(15)
    top_neg = df_coefs[df_coefs["coefficient"] < 0].sort_values(by="coefficient", ascending=True).head(15)

    print("\n   TOP 5 POSITIVE CHURN PREDICTORS (Risk Factors — Higher Log-Odds of Churn):")
    for idx, (_, row) in enumerate(top_pos.head(5).iterrows(), 1):
        print(f"     {idx}. {row['clean_feature_name']:<45} | beta={row['coefficient']:+.4f} | OR={row['odds_ratio']:.4f}")

    print("\n   TOP 5 NEGATIVE CHURN PREDICTORS (Protective Factors — Lower Log-Odds of Churn):")
    for idx, (_, row) in enumerate(top_neg.head(5).iterrows(), 1):
        print(f"     {idx}. {row['clean_feature_name']:<45} | beta={row['coefficient']:+.4f} | OR={row['odds_ratio']:.4f}")

    # 4. Generate Visualizations
    print("\n3. Generating explainability visualizations...")

    # Plot 1: Top 15 Positive and Top 15 Negative Coefficients (Side by Side)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Positive chart
    y_pos = np.arange(len(top_pos))
    ax1.barh(y_pos, top_pos["coefficient"], color="#d62728", edgecolor="black", alpha=0.85)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(top_pos["clean_feature_name"], fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("Logistic Regression Coefficient (beta > 0)", fontsize=11)
    ax1.set_title("Top 15 Churn Risk Factors\n(Increases Log-Odds of Churn)", fontsize=12, pad=10, weight="bold")
    ax1.grid(axis="x", alpha=0.3)
    for i, (_, row) in enumerate(top_pos.iterrows()):
        ax1.text(row["coefficient"] + 0.005, i, f"beta={row['coefficient']:.3f} (OR={row['odds_ratio']:.2f})", va="center", fontsize=8)

    # Negative chart
    y_neg = np.arange(len(top_neg))
    ax2.barh(y_neg, np.abs(top_neg["coefficient"]), color="#1f77b4", edgecolor="black", alpha=0.85)
    ax2.set_yticks(y_neg)
    ax2.set_yticklabels(top_neg["clean_feature_name"], fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Absolute Coefficient Magnitude (|beta|, where beta < 0)", fontsize=11)
    ax2.set_title("Top 15 Retention Factors\n(Decreases Log-Odds of Churn)", fontsize=12, pad=10, weight="bold")
    ax2.grid(axis="x", alpha=0.3)
    for i, (_, row) in enumerate(top_neg.iterrows()):
        ax2.text(np.abs(row["coefficient"]) + 0.005, i, f"beta={row['coefficient']:.3f} (OR={row['odds_ratio']:.2f})", va="center", fontsize=8)

    plt.suptitle("Model Explainability: Feature Associations with Customer Churn\nFinal Logistic Regression Model (Config B)", fontsize=14, y=0.98, weight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(TOP15_PLOT_PATH, dpi=300)
    plt.close()
    print(f"   [Plot 1/2] Saved Top 15 positive/negative chart to: {TOP15_PLOT_PATH}")

    # Plot 2: Combined Top 25 Feature Overview by Absolute Magnitude
    top25 = df_coefs_sorted.head(25)
    plt.figure(figsize=(10, 10))
    bar_colors = ["#d62728" if d == "Positive" else "#1f77b4" for d in top25["direction"]]
    y_top25 = np.arange(len(top25))

    plt.barh(y_top25, top25["absolute_coefficient"], color=bar_colors, edgecolor="black", alpha=0.85)
    plt.yticks(y_top25, top25["clean_feature_name"], fontsize=9)
    plt.gca().invert_yaxis()
    plt.xlabel("Absolute Coefficient Magnitude (|beta|)", fontsize=11)
    plt.title("Top 25 Most Influential Features in Churn Prediction Model\nRed: Increases Churn Odds | Blue: Decreases Churn Odds", fontsize=12, pad=15, weight="bold")
    plt.grid(axis="x", alpha=0.3)

    for i, (_, row) in enumerate(top25.iterrows()):
        sign_str = "+" if row["direction"] == "Positive" else "-"
        plt.text(row["absolute_coefficient"] + 0.005, i, f"{sign_str}{row['absolute_coefficient']:.3f} (OR={row['odds_ratio']:.2f})", va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(OVERVIEW_PLOT_PATH, dpi=300)
    plt.close()
    print(f"   [Plot 2/2] Saved Top 25 feature overview chart to: {OVERVIEW_PLOT_PATH}")

    # 5. Generate Comprehensive Explainability Markdown Report
    print(f"\n4. Generating explainability report at: {EXPLAINABILITY_REPORT_PATH}")
    generate_markdown_report(df_coefs_sorted, intercept, top_pos, top_neg)
    print("   Explainability report generated successfully.")

    print("\n" + "=" * 80)
    print("MODEL EXPLAINABILITY COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    return df_coefs_sorted


def generate_markdown_report(df_coefs, intercept, top_pos, top_neg):
    """Generates the comprehensive academic explainability report."""
    md = []
    md.append("# Phase 5 Checkpoint 5: Supervised Model Explainability & Feature Association Report")
    md.append("\n**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  ")
    md.append("**Model Architecture:** Logistic Regression with $L_2$ Regularization ($C=0.01$), `class_weight='balanced'`, `solver='lbfgs'`  ")
    md.append("**Feature Set:** Configuration B (37 input features: 34 numerical + 3 categorical including RFM `cluster_id`)  ")
    md.append("**Fitted Population:** $N=5,950$ combined customers (Train + Validation)  ")
    md.append("**Evaluation Baseline:** Test Set ($N=1,050$), Fixed Threshold $t^* = 0.46$  ")
    md.append("\n---\n")

    md.append("## 1. Mathematical Framework for Logistic Regression Explainability")
    md.append("\nIn a binary Logistic Regression framework predicting customer churn ($y=1$), the model computes the linear score $\\eta$ for customer $i$ as:")
    md.append("$$\\eta_i = \\beta_0 + \\sum_{j=1}^{p} \\beta_j x_{ij}$$")
    md.append("The predicted posterior probability $p_i = P(y_i = 1 \\mid \\mathbf{x}_i)$ is given by the logistic sigmoid link function:")
    md.append("$$p_i = \\sigma(\\eta_i) = \\frac{1}{1 + e^{-\\eta_i}}$$")
    md.append("The model's log-odds (logit) of churn is strictly linear in the transformed features:")
    md.append("$$\\text{logit}(p_i) = \\ln\\left(\\frac{p_i}{1 - p_i}\\right) = \\beta_0 + \\sum_{j=1}^{p} \\beta_j x_{ij}$$")
    md.append(f"- **Fitted Intercept ($\\beta_0$):** `{intercept:.4f}`. This represents the baseline log-odds of churn when all standardized continuous features are at their sample means (0) and all one-hot categorical features are at their zero states.")
    md.append("- **Fitted Regularization:** $C = 0.01$ applies strong $L_2$ shrinkage (ridge penalty $\\frac{1}{2C} \\sum \\beta_j^2$), which shrinks coefficients toward zero to guard against multi-collinearity and high variance.")

    md.append("\n### 1.1 Interpretation of Fitted Coefficients & exp(beta)")
    md.append("In binary Logistic Regression, the exponentiated coefficient is computed as $\\exp(\\beta_j)$.")
    md.append("Proper statistical interpretation depends strictly on the feature type and encoding strategy:")
    md.append("1. **Continuous Standardized Features:** All numerical features were standardized using `StandardScaler` ($z = \\frac{x - \\mu}{\\sigma}$). For these features, each coefficient $\\beta_j$ represents the change in log-odds of churn per **one standard-deviation increase ($+1\\sigma$)**, holding all other independent features constant. Here, $\\exp(\\beta_j)$ represents the **Odds Ratio ($\\text{OR}$)**: a $+1\\sigma$ increase multiplies the churn odds ($\\frac{p}{1-p}$) by $\\exp(\\beta_j)$, ceteris paribus.")
    md.append("2. **One-Hot Categorical Features (`drop=None`):** The pipeline's `OneHotEncoder` was configured with `drop=None` and `handle_unknown='ignore'`, retaining indicator columns for all observed categories (e.g., all 5 RFM clusters, all cities, and all states).")
    md.append("   - **$L_2$ Regularization & Identifiability:** L2 regularization penalizes the categorical coefficients and helps resolve the non-identifiability associated with redundant one-hot indicators. Under the fitted model's regularized objective, this supports a unique coefficient solution. It does not imply that the resulting coefficients are independent of the encoding or regularization strength, nor does it guarantee good numerical conditioning.")
    md.append("   - **Regularized Linear Score Parameters:** Categorical coefficients $\\beta_j$ are regularized parameters that contribute $\\beta_j \\cdot x_j$ directly to the model's linear prediction score $\\eta$. They must **not** be described as direct comparisons against an omitted reference category.")
    md.append("   - **Invalidity of Single-Indicator Ceteris Paribus Transitions:** Changing one category indicator while holding all other category indicators within the same feature constant is **not** a valid counterfactual or *ceteris paribus* transition. Because categories within a group are mutually exclusive and collectively exhaustive ($\\sum x_k = 1$), activating one indicator necessarily requires deactivating another.")
    md.append("   - **Shrinkage & Absence of Inherent Bias Elimination:** Full one-hot encoding does not inherently eliminate reference-category bias. The extent of shrinkage depends on the design matrix, feature correlations, category frequencies, and regularization strength, penalizing coefficient magnitudes toward zero under the regularized loss objective.")
    md.append("   - **Exponentiated Parameter ($\\exp(\\beta)$):** For categorical indicators, $\\exp(\\beta_j)$ represents the mathematical exponentiation of the fitted parameter $\\beta_j$, not a standalone odds ratio relative to a baseline reference category under this encoding.")
    md.append("3. **Missingness Indicators:** Binary indicators generated by `SimpleImputer(add_indicator=True)` represent whether the underlying historical feature was unrecorded ($x_j \\in \\{0, 1\\}$). The coefficient represents the additive contribution to the linear score when the metric was missing.")
    md.append("\n> [!IMPORTANT]\n> **Critical Statistical Disclaimer on Causation:** Logistic Regression coefficients quantify **statistical associations (conditional dependencies)** learned from the data, **NOT causal effects**. A positive coefficient indicates that customers with higher values of this feature have higher odds of churning in the training distribution; it does *not* imply that changing this feature will cause churn.")

    md.append("\n---\n")
    md.append("## 2. Top Churn Risk Factors (Positive Coefficients: $\\beta > 0, \\text{OR} > 1$)")
    md.append("\nFeatures that are positively associated with churn log-odds. Customers with higher values on these features exhibit higher estimated churn probabilities:\n")

    md.append("| Rank | Transformed Feature | Feature Category | Coefficient ($\\beta$) | $\\exp(\\beta)$ | Statistical Interpretation |")
    md.append("| :---: | :--- | :--- | :---: | :---: | :--- |")
    for r, (_, row) in enumerate(top_pos.iterrows(), 1):
        if row["feature_type"] == "Numerical (Standardized)":
            interp = f"Standardized numerical: each $+1\\sigma$ is conditionally associated with {row['coefficient']:+.4f} higher churn log-odds (OR = {row['odds_ratio']:.2f}), holding other inputs constant."
        elif row["feature_type"] == "Categorical (One-Hot)":
            interp = f"Categorical indicator: contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score under full one-hot encoding; not a standalone category-vs-reference odds ratio."
        elif row["feature_type"] == "Missingness Indicator":
            interp = f"Missingness indicator: absence of recorded values contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score."
        else:
            interp = f"Model parameter: contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score."
        md.append(f"| **{r}** | `{row['clean_feature_name']}` | {row['feature_type']} | `{row['coefficient']:+.4f}` | `{row['odds_ratio']:.4f}` | {interp} |")

    md.append("\n---\n")
    md.append("## 3. Top Retention Factors (Negative Coefficients: $\\beta < 0, \\text{OR} < 1$)")
    md.append("\nFeatures that are inversely associated with churn log-odds. Customers with higher values on these features exhibit lower estimated churn probabilities (higher retention):\n")

    md.append("| Rank | Transformed Feature | Feature Category | Coefficient ($\\beta$) | $\\exp(\\beta)$ | Statistical Interpretation |")
    md.append("| :---: | :--- | :--- | :---: | :---: | :--- |")
    for r, (_, row) in enumerate(top_neg.iterrows(), 1):
        if row["feature_type"] == "Numerical (Standardized)":
            interp = f"Standardized numerical: each $+1\\sigma$ is conditionally associated with {row['coefficient']:+.4f} lower churn log-odds (OR = {row['odds_ratio']:.2f}), holding other inputs constant."
        elif row["feature_type"] == "Categorical (One-Hot)":
            interp = f"Categorical indicator: contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score under full one-hot encoding; not a standalone category-vs-reference odds ratio."
        elif row["feature_type"] == "Missingness Indicator":
            interp = f"Missingness indicator: absence of recorded values contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score."
        else:
            interp = f"Model parameter: contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to the linear prediction score."
        md.append(f"| **{r}** | `{row['clean_feature_name']}` | {row['feature_type']} | `{row['coefficient']:+.4f}` | `{row['odds_ratio']:.4f}` | {interp} |")

    md.append("\n---\n")
    md.append("## 4. Impact of Phase 4 RFM Clustering Personas (`cluster_id`)")
    md.append("\nConfiguration B integrated the unsupervised customer personas derived from Phase 4 K-Means clustering. Because `OneHotEncoder(drop=None)` was used, each cluster persona receives its own binary indicator variable and is regularized under the $L_2$ penalty. These coefficients are regularized linear score parameters under the full dummy encoding, rather than direct comparisons against an omitted reference persona:\n")

    cluster_rows = df_coefs[df_coefs["feature_name"].str.contains("cluster_id")].copy()
    persona_names = {
        "cluster_id_0": "At-Risk Low-Value One-Time Buyers",
        "cluster_id_1": "High-Value Frequent Shoppers",
        "cluster_id_2": "Occasional Moderate-Value Shoppers",
        "cluster_id_3": "High-Friction Never-Delivered Registrants",
        "cluster_id_4": "Recent Single-Purchase Try-Outs"
    }

    md.append("| Cluster Feature | Associated Persona Name | Coefficient ($\\beta$) | $\\exp(\\beta)$ | Churn Association Tendency | Statistical Interpretation |")
    md.append("| :--- | :--- | :---: | :---: | :--- | :--- |")
    for _, row in cluster_rows.iterrows():
        raw_key = row["feature_name"].replace("cat__", "")
        p_name = persona_names.get(raw_key, "RFM Persona")
        tendency = "Elevated Churn Risk" if row["coefficient"] > 0 else "Retention-Oriented"
        md.append(f"| `{row['clean_feature_name']}` | **{p_name}** | `{row['coefficient']:+.4f}` | `{row['odds_ratio']:.4f}` | {tendency} | Contributes {row['coefficient']:+.4f} ($\\exp(\\beta) = {row['odds_ratio']:.2f}$) to linear score under full one-hot encoding; regularized indicator parameter, not a comparison to an omitted cluster. |")

    md.append("\n---\n")
    md.append("## 5. Academic Discussion for Viva Voce")
    md.append("\n### Q1: Why did you report odds ratios rather than feature percentage probabilities?")
    md.append("> **Answer:** In Logistic Regression, the model is linear in the log-odds space, not in probability space. Because the sigmoid transformation is non-linear, the change in probability associated with a one-unit change in a feature depends on the starting probability $\\Delta p = \\sigma(\\eta + \\beta) - \\sigma(\\eta)$. Odds Ratios ($\\text{OR} = \\exp(\\beta)$) are constant multiplicative factors on the *odds* ratio, making them mathematically precise and invariant across baseline risk levels.")
    md.append("\n### Q2: Why are continuous features interpreted per one standard deviation?")
    md.append("> **Answer:** During preprocessing, all continuous features were passed through `StandardScaler()`, subtracting the mean and dividing by the standard deviation ($z = \\frac{x - \\mu}{\\sigma}$). Consequently, a one-unit increase in the transformed feature corresponds exactly to a one standard-deviation increase in the original e-commerce metric.")
    md.append("\n### Q3: Can marketing teams assume that offering discounts will prevent churn because of negative coefficients on discounts?")
    md.append("> **Answer:** No. That would confuse correlation with causation. Observational data shows that customers who received discounts engaged more, but unobserved confounding (e.g., promotional eligibility, customer willingness to buy) may drive both discount receipt and retention. Controlled A/B testing would be necessary to establish causal efficacy.")
    md.append("\n### Q4: Why did the OneHotEncoder retain all categories without dropping a reference level (`drop=None`)?")
    md.append("> **Answer:** In unregularized linear models, omitting a reference category is mathematically required to prevent the 'dummy variable trap' (exact multicollinearity where indicator columns sum to 1). In regularized Logistic Regression, however, L2 regularization penalizes the categorical coefficients and helps resolve the non-identifiability associated with redundant one-hot indicators. Under the fitted model's regularized objective, this supports a unique coefficient solution. It does not imply that the resulting coefficients are independent of the encoding or regularization strength, nor does it guarantee good numerical conditioning. Full one-hot encoding does not inherently eliminate reference-category bias; rather, shrinkage depends on the design matrix, feature correlations, category frequencies, and regularization strength. Categorical coefficients are regularized linear parameters contributing $\\beta_j \\cdot x_j$ to the prediction score, not comparisons against an omitted baseline category. Crucially, changing one category indicator while holding all other category indicators within the same feature constant is not a valid counterfactual or *ceteris paribus* transition, because mutually exclusive categories must sum to 1. Consequently, $\\exp(\\beta_j)$ represents the mathematical exponentiation of parameter $\\beta_j$, not a standalone odds ratio relative to an omitted baseline.")

    with open(EXPLAINABILITY_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    explain_final_model()
