Results — German Credit (classification)
Calibrated logistic regression (one-hot encoded categorical features + standardized numeric features) achieved ROC-AUC = 0.762, AP = 0.562, Brier = 0.176 (base-rate = 0.210), and ECE ≈ 0.089.
With a cost ratio FN = 5× FP, the optimal threshold t* = 0.21 (from a sweep on calibrated probabilities) yields the validation confusion matrix [[TN, FP],[FN, TP]] = [[69, 71],[5, 55]], approval rate = 37%, default-capture (recall) = 91.7%, and expected cost ≈ 0.48 per applicant—a ~49.5% reduction versus the default 0.5 cutoff (cost 96 vs 190).

Methods — German Credit (classification)
Data & target. We used the OpenML German Credit dataset (credit-g, version-pinned), 1,000 rows × 20 features. The target is class with labels good/bad; we treat bad as the positive class (default risk).

Splits & validation. We performed an 80/20 stratified train/validation split (random_state=42) to preserve class balance, and used 5-fold StratifiedKFold (shuffle=True, random_state=42) for cross-validated performance estimates.

Preprocessing. A leak-safe Pipeline with a ColumnTransformer handled features:
• Numeric (7) → StandardScaler
• Categorical (13) → OneHotEncoder(handle_unknown="ignore")
All transforms were fit only on training folds inside CV.

Models. Baseline logistic regression (max_iter=1000, solver liblinear) was trained on the preprocessed data. We compared against a RandomForestClassifier (400 trees; class_weight="balanced") to check nonlinear gains. Logistic was selected for final reporting due to similar AUC and superior interpretability.

Calibration. To improve probability quality, we wrapped the logistic pipeline with Platt scaling (CalibratedClassifierCV(method="sigmoid", cv=5)), then generated calibrated probabilities on the validation set.

Threshold selection (business cost). We chose a decision threshold t* by minimizing expected misclassification cost with FN cost = 5× FP via a sweep over probability cutoffs. This reflects higher business impact of missed bads.

Evaluation & interpretation. We report ROC-AUC, Average Precision (PR-AUC), Brier score, and ECE (10 quantile bins), plus confusion matrices at t*. For interpretability, we converted logistic coefficients to odds ratios and summarized the top risk-increasing and protective factors.