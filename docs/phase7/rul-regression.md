# Phase 7: Remaining Useful Life (RUL) Regression

## 1. Regression Formulation & Algorithm

Remaining Useful Life (RUL) estimation predicts the continuous time horizon (in seconds) remaining before an operating asset requires critical maintenance or reaches mechanical failure.

We employ `sklearn.ensemble.HistGradientBoostingRegressor` due to:
1. **Native Missing Value Handling**: Efficient binning without requiring synthetic multi-column imputers.
2. **Non-Linear Dynamics**: Excels at modeling complex non-linear degradation curves (exponential temperature rise, polynomial vibration growth).
3. **Execution Efficiency**: Orders of magnitude faster training and inference than traditional Random Forests or Neural Networks on multi-signal IoT tabular datasets.

### Model Hyperparameters
- `max_iter`: 100 boosting rounds
- `max_depth`: 8
- `learning_rate`: 0.1
- `min_samples_leaf`: 20
- `l2_regularization`: 0.1
- `random_state`: 42

---

## 2. Baseline Model Benchmark

To provide objective validation that the trained regressor extracts genuine physical patterns from telemetry rather than memorizing dataset biases, a `BaselineMedianRULModel` is trained concurrently. The baseline predictor outputs the constant historical median RUL:

$$\hat{y}_{\text{baseline}} = \text{median}(y_{\text{train}})$$

The primary evaluation objective is to demonstrate substantial error reduction ($>80\%$ MAE improvement) over the baseline median predictor.

---

## 3. Evaluation Metrics

Evaluated on the unseen chronological test set:
- **Mean Absolute Error (MAE)**: Average magnitude of prediction error in seconds:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE)**: Penalizes severe outlier predictions:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Coefficient of Determination ($R^2$)**: Proportion of variance explained by physical features:
  $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$
- **Median Absolute Error (MedAE)**: Robust to extreme temporal transitions.
- **Baseline MAE Improvement (%)**: Percentage reduction in MAE relative to median baseline.
