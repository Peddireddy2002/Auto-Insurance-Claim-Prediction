# 🚗 Auto Insurance Claim Prediction

This project aims to predict whether a customer will file an auto insurance claim using machine learning techniques. The model enables insurance companies to evaluate risk more effectively, set appropriate premiums, and improve claim management processes.

---

## 📊 Dataset Overview

The dataset includes customer-level information relevant to insurance risk assessment.

### Features Include:

- **Demographics**: Age, gender, income
- **Policy Details**: Policy type, vehicle age, vehicle type, past claims
- **Behavioral Data**: Customer activity and usage patterns
- **Target Variable**: Binary indicator of whether a claim was filed (`Yes`/`No`)

---

## 🧹 Data Preprocessing

- **Missing Values**: Handled using imputation or removal techniques
- **Encoding**: Applied one-hot encoding for categorical features
- **Normalization**: Scaled numerical data for consistent model input
- **Feature Selection**: Removed irrelevant or redundant features to improve performance

---

## 📈 Exploratory Data Analysis (EDA)

- Analyzed distribution of features and class balance of the target variable
- Examined correlations between independent variables and claims
- Visualized claim trends across features such as:
  - Customer age
  - Vehicle type
- Detected and addressed outliers for enhanced model accuracy

---

## 🤖 Model Building & Evaluation

### Algorithms Used:

- **Logistic Regression**
- **Decision Tree**
- **Random Forest**

### Evaluation Strategy:

- Split dataset into **training** and **testing** sets
- Assessed model performance using:
  - **Accuracy**
  - **Precision**
  - **Recall**
  - **F1-Score**
- Special focus on **reducing false negatives** to ensure high-risk customers are correctly identified

---

## ✅ Results & Insights

- **Best Model Accuracy**: ~[Insert Best Accuracy Value]%
- **Key Influential Features**:
  - Number of past claims
  - Vehicle age
  - Customer age
- **Business Value**:
  - Enhanced fraud detection
  - Risk-based pricing strategies
  - Improved customer segmentation for underwriting

---

## 🛠️ Tools & Technologies

- **Python**
  - `Pandas`, `NumPy` – Data processing
  - `Matplotlib`, `Seaborn` – Visualizations
  - `Scikit-learn` – Modeling and evaluation

---

## 📚 Conclusion

This project demonstrates how **predictive analytics** can be applied in the **insurance industry** to anticipate claim likelihood. By identifying high-risk customers, insurers can take proactive steps in pricing, policy design, and fraud mitigation — ultimately driving better decision-making and customer outcomes.

---

## 📌 Future Improvements

- Hyperparameter tuning for better accuracy
- Use of ensemble techniques like XGBoost or Gradient Boosting
- Incorporate time-series aspects of customer behavior
- Deploy the model using a web dashboard

---

