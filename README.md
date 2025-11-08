Results - German Credit(classification)

Calibrated logistic regression (OHE+scaling) achieved ROC-AUC = 0.762 and Brier = 0.176 (vs base-rate 0.210).
Using a 5× cost for false negatives, the optimal threshold t* = 0.21 yields confusion matrix [[69, 71], [5, 55]], approval rate = 37%, default-capture (recall) = 91.7%, and expected cost ≈ 0.48 per applicant, a ~49.5% reduction vs the default 0.5 cutoff.