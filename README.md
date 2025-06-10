# Auto-Insurance-Claim-Prediction

## Project Overview
This project aims to predict whether a customer will file an auto insurance claim using machine learning techniques. The model helps insurance companies evaluate risk, set appropriate premiums, and improve claim management processes.

## Dataset
The dataset includes:

Customer demographics (age, gender, income, etc.)

Policy details (policy type, vehicle age, vehicle type, past claims)

Vehicle characteristics and customer behavior

Target variable: binary indicator of claim filed (yes/no)

## Data Preprocessing
Handled missing values by imputation or removal

Encoded categorical variables using techniques like one-hot encoding

Normalized numerical features for better model performance

Performed feature selection to reduce irrelevant data and dimensionality

## Exploratory Data Analysis (EDA)
Analyzed feature distributions and target variable balance

Explored correlations between features and claim occurrences

Visualized key patterns such as claim frequency by customer age and vehicle type

Identified and managed outliers to enhance model accuracy

## Model Building & Evaluation
Implemented machine learning models:

Logistic Regression

Decision Trees

Random Forests

Split data into training and testing sets to ensure unbiased evaluation

Used metrics such as accuracy, precision, recall, and F1-score to assess models

Focused on minimizing false negatives to better capture potential claims

## Results & Insights
Achieved best model accuracy of approximately [insert value]%

Identified important features: past claims, vehicle age, customer age

Model can assist in identifying high-risk customers for policy adjustments

Supports operational improvements like fraud detection and dynamic pricing

## Tools & Technologies
Python (Pandas, NumPy) for data manipulation and cleaning

Matplotlib, Seaborn for data visualization

Scikit-learn for machine learning modeling and evaluation

## Conclusion
This project demonstrates how predictive analytics can improve decision-making in the insurance industry by accurately forecasting claim likelihood and enabling targeted risk management.
