"""
Indian E-Commerce Customer Retention Intelligence System
Module: Advanced Feature Engineering & Pipeline Components
Description: Implements advanced behavioral features (momentum ratios, friction index,
             missingness indicators), custom scikit-learn transformers (Log1pTransformer,
             CorrelationPruner), and pipeline construction factory for Phase 5.1 model
             optimization experiments.

Author: Senior Machine Learning Engineer (BCA AI & ML Project)
Cutoff Date: 2025-12-31 (Strict zero future data leakage)
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Constants
SNAPSHOT_DATE_STR = "2025-12-31"
EPSILON_MOMENTUM = 0.1
DEFAULT_CORRELATION_THRESHOLD = 0.85

# Candidate skewed columns suitable for log1p transformation (strictly non-negative)
CANDIDATE_LOG1P_COLUMNS = [
    "customer_tenure_days",
    "recency_days",
    "recency_delivered_days",
    "hist_total_order_value_inr",
    "hist_delivered_order_value_inr",
    "hist_total_recorded_discount_inr",
    "hist_average_order_value_inr",
]

# Baseline Phase 5 Configuration B feature columns
BASELINE_NUMERICAL_COLS = [
    "customer_tenure_days",
    "has_historical_orders",
    "recency_days",
    "recency_delivered_days",
    "has_delivered_order",
    "hist_order_count",
    "hist_delivered_order_count",
    "hist_returned_order_count",
    "hist_cancelled_order_count",
    "hist_total_order_value_inr",
    "hist_delivered_order_value_inr",
    "hist_total_recorded_discount_inr",
    "hist_average_order_value_inr",
    "orders_last_30_days",
    "orders_last_90_days",
    "orders_last_180_days",
    "delivered_orders_last_30_days",
    "delivered_orders_last_90_days",
    "delivered_orders_last_180_days",
    "hist_return_rate",
    "hist_cancellation_rate",
    "hist_average_delivery_delay_days",
    "hist_delivery_delay_missing_count",
    "hist_delivery_delay_missing_rate",
    "hist_average_discount_amount_inr",
    "hist_discounted_order_count",
    "hist_discount_missing_count",
    "hist_discount_missing_rate",
    "hist_payment_missing_count",
    "hist_payment_missing_rate",
    "hist_cod_order_count",
    "hist_cod_usage_rate",
    "hist_upi_order_count",
    "hist_upi_usage_rate"
]

BASELINE_CATEGORICAL_COLS = [
    "city",
    "state",
    "cluster_id"
]

ADVANCED_NUMERICAL_COLS = [
    "velocity_ratio_30_90",
    "velocity_ratio_90_180",
    "has_orders_last_90_days",
    "has_orders_last_180_days",
    "delay_friction_score",
    "missing_friction_score"
]


def compute_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes advanced behavioral features from a dataset containing baseline metrics.
    
    Features computed:
    1. velocity_ratio_30_90:
       (orders_last_30_days + 0.1) / (orders_last_90_days / 3.0 + 0.1)
       Missingness rule: If orders_last_90_days == 0, set to np.nan (dormant accounts).
       Binary indicator: has_orders_last_90_days (1 if orders_last_90_days > 0 else 0).
       
    2. velocity_ratio_90_180:
       (orders_last_90_days + 0.1) / (orders_last_180_days / 2.0 + 0.1)
       Missingness rule: If orders_last_180_days == 0, set to np.nan (dormant accounts).
       Binary indicator: has_orders_last_180_days (1 if orders_last_180_days > 0 else 0).
       
    3. delay_friction_score:
       hist_average_delivery_delay_days * (1.0 + hist_return_rate + hist_cancellation_rate)
       Missingness rule: When hist_average_delivery_delay_days is NaN (zero delivered orders),
       delay_friction_score is preserved as NaN.
       Binary indicator: missing_friction_score (1 if delay_friction_score is NaN else 0).
       
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing baseline behavioral columns.
        
    Returns:
    --------
    pd.DataFrame: Augmented DataFrame with advanced feature columns.
    """
    df = df.copy()

    # Required constituent columns
    req_cols = [
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        "hist_average_delivery_delay_days", "hist_return_rate", "hist_cancellation_rate"
    ]
    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for advanced feature engineering: {missing}")

    # 1. Momentum Ratio 30/90
    has_90 = (df["orders_last_90_days"] > 0).astype(int)
    denom_30_90 = (df["orders_last_90_days"] / 3.0) + EPSILON_MOMENTUM
    numer_30_90 = df["orders_last_30_days"] + EPSILON_MOMENTUM
    raw_ratio_30_90 = numer_30_90 / denom_30_90

    # Explicit missingness when baseline window has zero activity
    df["velocity_ratio_30_90"] = np.where(has_90 == 1, raw_ratio_30_90.round(4), np.nan)
    df["has_orders_last_90_days"] = has_90

    # 2. Momentum Ratio 90/180
    has_180 = (df["orders_last_180_days"] > 0).astype(int)
    denom_90_180 = (df["orders_last_180_days"] / 2.0) + EPSILON_MOMENTUM
    numer_90_180 = df["orders_last_90_days"] + EPSILON_MOMENTUM
    raw_ratio_90_180 = numer_90_180 / denom_90_180

    # Explicit missingness when baseline window has zero activity
    df["velocity_ratio_90_180"] = np.where(has_180 == 1, raw_ratio_90_180.round(4), np.nan)
    df["has_orders_last_180_days"] = has_180

    # 3. Customer Friction Index
    # Friction = AverageDeliveryDelay * (1 + ReturnRate + CancellationRate)
    friction_multiplier = 1.0 + df["hist_return_rate"].fillna(0.0) + df["hist_cancellation_rate"].fillna(0.0)
    delay_series = df["hist_average_delivery_delay_days"]

    # When delivery delay is NaN (e.g. customer with 0 delivered orders), friction score must be NaN
    raw_friction = delay_series * friction_multiplier
    df["delay_friction_score"] = np.where(delay_series.notnull(), raw_friction.round(4), np.nan)
    df["missing_friction_score"] = df["delay_friction_score"].isnull().astype(int)

    return df


def _safe_corr(a, b):
    """Compute absolute Pearson correlation cleanly without runtime warnings."""
    mask = ~np.isnan(a) & ~np.isnan(b)
    if np.sum(mask) < 3:
        return 0.0
    a_m = a[mask]
    b_m = b[mask]
    std_a = np.std(a_m)
    std_b = np.std(b_m)
    if std_a < 1e-8 or std_b < 1e-8:
        return 0.0
    r = np.corrcoef(a_m, b_m)[0, 1]
    return abs(r) if not np.isnan(r) else 0.0


class Log1pTransformer(BaseEstimator, TransformerMixin):
    """
    Custom scikit-learn transformer applying natural log(1 + x) to specified non-negative columns.
    Preserves NaN values intact so downstream SimpleImputer can handle missingness cleanly.
    """
    def __init__(self, columns=None):
        self.columns = columns

    def fit(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = np.asarray(X.columns, dtype=object)
            self.n_features_in_ = len(X.columns)
            if self.columns is None:
                self.columns_ = [c for c in CANDIDATE_LOG1P_COLUMNS if c in X.columns]
            else:
                self.columns_ = [c for c in self.columns if c in X.columns]
                
            # Verify non-negativity
            for col in self.columns_:
                valid_vals = X[col].dropna()
                if (valid_vals < 0).any():
                    min_val = valid_vals.min()
                    raise ValueError(f"Log1pTransformer cannot transform negative values in '{col}': min value is {min_val}")
        else:
            # Array-like: columns should be a list of integer indices
            X_arr = np.asarray(X)
            self.n_features_in_ = X_arr.shape[1]
            self.feature_names_in_ = np.asarray([f"x{i}" for i in range(self.n_features_in_)], dtype=object)
            self.columns_ = list(self.columns) if self.columns is not None else []
            if len(self.columns_) > 0:
                for idx in self.columns_:
                    valid_vals = X_arr[:, idx][~np.isnan(X_arr[:, idx])]
                    if (valid_vals < 0).any():
                        raise ValueError(f"Log1pTransformer cannot transform negative values at index {idx}")
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X_out = X.copy()
            for col in self.columns_:
                X_out[col] = np.log1p(X_out[col].astype(float))
            return X_out
        else:
            X_out = np.array(X, copy=True, dtype=float)
            for idx in self.columns_:
                valid_mask = ~np.isnan(X_out[:, idx])
                X_out[valid_mask, idx] = np.log1p(X_out[valid_mask, idx])
            return X_out

    def get_feature_names_out(self, input_features=None):
        """Preserves and passes through feature names conforming to scikit-learn standard."""
        if input_features is not None:
            return np.asarray(input_features, dtype=object)
        if hasattr(self, "feature_names_in_"):
            return np.asarray(self.feature_names_in_, dtype=object)
        return np.asarray([f"x{i}" for i in range(self.n_features_in_)], dtype=object)


class CorrelationPruner(BaseEstimator, TransformerMixin):
    """
    Leakage-safe correlation pruner for numerical feature selection.
    
    Identifies pairs of numerical features with Pearson correlation |r| > threshold during fit().
    For each collinear pair:
    - If target `y` is provided: drops the feature with lower Pearson correlation to `y`.
    - If `y` is None: drops the second feature in column order.
    - Never drops features specified in `protected_cols`.
    
    CRITICAL: fit() must only be called on training folds. It must NEVER see validation or test folds.
    """
    def __init__(self, threshold=DEFAULT_CORRELATION_THRESHOLD, protected_cols=None):
        self.threshold = threshold
        self.protected_cols = protected_cols

    def fit(self, X, y=None):
        protected_set = set(self.protected_cols) if self.protected_cols is not None else set()
        is_df = isinstance(X, pd.DataFrame)
        
        if is_df:
            self.feature_names_in_ = list(X.columns)
            self.n_features_in_ = len(self.feature_names_in_)
            df_num = X.select_dtypes(include=[np.number])
            col_names = list(df_num.columns)
            X_arr = df_num.values
        else:
            X_arr = np.asarray(X, dtype=float)
            self.n_features_in_ = X_arr.shape[1]
            self.feature_names_in_ = [f"feat_{i}" for i in range(self.n_features_in_)]
            col_names = self.feature_names_in_

        n_cols = len(col_names)
        
        # Compute correlation matrix cleanly
        corr_matrix = np.eye(n_cols, dtype=float)
        for i in range(n_cols):
            for j in range(i + 1, n_cols):
                r = _safe_corr(X_arr[:, i], X_arr[:, j])
                corr_matrix[i, j] = r
                corr_matrix[j, i] = r

        # Compute target correlation if y provided
        y_corr = {}
        if y is not None:
            y_arr = np.asarray(y, dtype=float)
            for idx, col in enumerate(col_names):
                y_corr[idx] = _safe_corr(X_arr[:, idx], y_arr)

        to_drop = set()
        for i in range(n_cols):
            if i in to_drop:
                continue
            for j in range(i + 1, n_cols):
                if j in to_drop:
                    continue
                r_val = corr_matrix[i, j]
                if r_val > self.threshold:
                    # Check protected status
                    col_i_name = col_names[i]
                    col_j_name = col_names[j]
                    
                    i_protected = (i in protected_set) or (col_i_name in protected_set)
                    j_protected = (j in protected_set) or (col_j_name in protected_set)
                    
                    if i_protected and not j_protected:
                        to_drop.add(j)
                    elif j_protected and not i_protected:
                        to_drop.add(i)
                    elif not i_protected and not j_protected:
                        if y is not None:
                            # Drop feature with lower target correlation
                            corr_i = y_corr.get(i, 0.0)
                            corr_j = y_corr.get(j, 0.0)
                            if corr_i < corr_j:
                                to_drop.add(i)
                                break  # feature i dropped, proceed to next i
                            else:
                                to_drop.add(j)
                        else:
                            # Drop second feature (j)
                            to_drop.add(j)

        self.keep_indices_ = [i for i in range(self.n_features_in_) if i not in to_drop]
        self.drop_indices_ = sorted(list(to_drop))
        if is_df:
            self.columns_to_drop_ = [col_names[idx] for idx in self.drop_indices_]
            self.columns_to_keep_ = [col_names[idx] for idx in self.keep_indices_]
        else:
            self.columns_to_drop_ = self.drop_indices_
            self.columns_to_keep_ = self.keep_indices_

        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            return X.drop(columns=[c for c in self.columns_to_drop_ if c in X.columns])
        else:
            X_arr = np.asarray(X)
            return X_arr[:, self.keep_indices_]

    def get_feature_names_out(self, input_features=None):
        """Returns names of kept features conforming to scikit-learn standard."""
        if input_features is not None:
            names_in = np.asarray(input_features, dtype=object)
        elif hasattr(self, "feature_names_in_"):
            names_in = np.asarray(self.feature_names_in_, dtype=object)
        else:
            names_in = np.asarray([f"feat_{i}" for i in range(self.n_features_in_)], dtype=object)
        return names_in[self.keep_indices_]


def build_advanced_preprocessor(
    categorical_cols=None,
    numerical_cols=None,
    scale_numerical=True,
    use_log1p=False,
    log1p_cols=None,
    use_correlation_pruner=False,
    correlation_threshold=DEFAULT_CORRELATION_THRESHOLD,
    protected_cols=None
):
    """
    Constructs a leakage-free preprocessing pipeline supporting:
    - Numerical: Optional Log1p, Median Imputation with indicators, Optional StandardScaler, Optional CorrelationPruner.
    - Categorical: Most-frequent Imputation, OneHotEncoder(drop=None, handle_unknown='ignore').
    
    Returns:
    --------
    ColumnTransformer: Fully integrated scikit-learn preprocessor.
    """
    if categorical_cols is None:
        categorical_cols = BASELINE_CATEGORICAL_COLS
    if numerical_cols is None:
        numerical_cols = BASELINE_NUMERICAL_COLS + ADVANCED_NUMERICAL_COLS

    num_steps = []
    
    # Optional log1p transformation on skewed features
    if use_log1p:
        cols_to_log = log1p_cols if log1p_cols is not None else [c for c in CANDIDATE_LOG1P_COLUMNS if c in numerical_cols]
        num_steps.append(("log1p", Log1pTransformer(columns=cols_to_log)))

    # Median imputation with missingness indicators
    num_steps.append(("imputer", SimpleImputer(strategy="median", add_indicator=True)))

    # Optional scaling
    if scale_numerical:
        num_steps.append(("scaler", StandardScaler()))

    # Optional within-fold correlation pruning
    if use_correlation_pruner:
        # Convert protected column names to indices if passed as names
        protected_indices = []
        if protected_cols:
            for c in protected_cols:
                if isinstance(c, int):
                    protected_indices.append(c)
                elif c in numerical_cols:
                    protected_indices.append(numerical_cols.index(c))
                else:
                    protected_indices.append(c)
        num_steps.append(("pruner", CorrelationPruner(
            threshold=correlation_threshold,
            protected_cols=protected_indices
        )))

    num_pipeline = Pipeline(num_steps)

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(drop=None, handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, numerical_cols),
            ("cat", cat_pipeline, categorical_cols)
        ],
        remainder="drop"
    )

    return preprocessor
