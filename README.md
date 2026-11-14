# Accident Severity Flagger for UK Road Safety Officers
**Academic Project Document — Project-I (Semester 1)**  
**Student Name**: Kunche Abhishek  
**GitHub Repository**: [kuncheabhishek015/ACCIDENT-SEVERITY-FLAGGER-FOR-UK-ROAD-SAFETY-OFFICERS](https://github.com/kuncheabhishek015/ACCIDENT-SEVERITY-FLAGGER-FOR-UK-ROAD-SAFETY-OFFICERS)  
**Live Application (Firebase)**: [https://mark999-143.web.app](https://mark999-143.web.app)  

---

## 📌 Problem Statement & Overview
Local council road safety officers in the UK operate under tight budget constraints, funding roughly **20–30 safety interventions per year** (such as speed cameras, junction redesigns, barriers, or street lighting). Without data-driven predictive tools, officers lack quantitative evidence to determine which specific road, junction, weather, and light conditions are most prone to producing serious or fatal collisions rather than minor ones.

This project delivers an **All-in-One Full-Stack Data Science & Software System** that:
1. Decodes one full year of official **DfT STATS19 collision data (101,525 records)**.
2. Conducts exploratory **Data Visualization** (Matplotlib & Seaborn distribution charts, risk heatmaps, speed limit risk curves).
3. Conducts rigorous **Mathematics of Probability & Statistical Independence Testing** ($\chi^2$, Cramér's V, Bayesian conditional probabilities).
4. Trains and evaluates **5 Machine Learning Classifiers** alongside **2 Non-ML Baselines** using budget-constrained **Precision@K** and **Recall@K** ($K \in \{20, 25, 30\}$) with **Bootstrapped 95% Confidence Intervals**.
5. Provides local explainability using **SHAP-based feature attributions**.
6. Serves predictions through a **Flask REST API** backed by an **SQLite Audit Logging Database**.
7. Surfaces results in a **Modern Officer Web Dashboard** with real-time risk gauges, historical collision evidence cards, top-$K$ council prioritized shortlists, and statistical insights.

---

## 🔬 Core Academic Components

### 1. Mathematics of Probability & Statistics
- **Chi-Square Test of Independence ($\chi^2$)**:
  $$\chi^2 = \sum \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$
  - **Weather vs. Severity**: $\chi^2 = 321.55$, $p < 0.0001$, $df = 8$, Cramér's V = $0.0563$ (Statistically Significant).
  - **Light vs. Severity**: $\chi^2 = 340.38$, $p < 0.0001$, $df = 4$, Cramér's V = $0.0579$ (Statistically Significant).
- **Cramér's V Effect Size**:
  $$V = \sqrt{\frac{\chi^2}{N \cdot \min(r-1, c-1)}}$$
- **Bayesian Risk Multipliers**:
  $$R = \frac{P(\text{Severe} \mid \mathbf{X})}{P(\text{Severe})}$$

---

### 2. Machine Learning & Budget-Constrained Evaluation ($\text{Precision@K}$)
- **Models Implemented**:
  - Non-ML Baseline 1: Predict Majority Class
  - Non-ML Baseline 2: Group-by Road Type Majority Rate
  - Model 1: **Logistic Regression** (Balanced Class Weighting)
  - Model 2: **Decision Tree Classifier** (Depth = 8)
  - Model 3: **Bagging Classifier** (Ensemble of Decision Trees)
  - Model 4: **AdaBoost Classifier** (Adaptive Boosting)
  - Model 5: **Naive Bayes** (GaussianNB)
- **Primary Metric**: **Precision@K** where $K$ matches council budget ($K = 25$ interventions):
  $$\text{Precision@K} = \frac{\sum_{i \in \text{Top } K} y_i}{K}$$
- **Bootstrapping**: 1,000 bootstrap resamples on test set metrics establishing 95% Confidence Intervals $[Lower_{95\%}, Upper_{95\%}]$.

#### Model Performance Comparison ($K = 25$ Interventions)

| Model Name | Type | ROC-AUC | Precision@25 (%) | Precision@25 (95% CI) | Recall@25 (%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Baseline 1: Majority Class** | Non-ML | 0.5000 | 44.0% | [8.0%, 44.1%] | 0.21% |
| **Baseline 2: Group-By Road Type** | Non-ML | 0.5415 | 32.0% | [12.0%, 48.0%] | 0.15% |
| **Logistic Regression (Balanced)** | ML Model | **0.5881** | **32.0%** | **[16.0%, 56.0%]** | **0.15%** |
| **AdaBoost Classifier** | ML Model | 0.5679 | **40.0%** | **[19.9%, 56.0%]** | **0.19%** |
| **Bagging Classifier** | ML Model | 0.5834 | 36.0% | [12.0%, 48.0%] | 0.17% |
| **Decision Tree (Depth=8)** | ML Model | 0.5801 | 20.0% | [8.0%, 40.0%] | 0.09% |
| **Naive Bayes (GaussianNB)** | ML Model | 0.5747 | 24.0% | [15.9%, 52.0%] | 0.11% |

---

### 3. Software Engineering (SE) Architecture & Audit Logging
- **Clean Separation of Concerns**: Modular packages for decoding, statistical testing, ML modeling, evaluation, explainability, DB access, API serving, and frontend.
- **SQLite Database Persistence**: Every officer query is logged in an SQLite table (`query_logs`) via SQLAlchemy ORM with timestamp, road conditions, predicted risk, category, historical matches, and the serving model identifier.
- **Automated Unit Testing Suite**: **15 Pytest tests** covering API endpoints, SQLite transactions, decoder lookups, $\chi^2$ calculations, baseline predictions, and metrics with 100% pass rate.

---

### 4. Interactive Web Application & Officer Dashboard
- **Dynamic Classifier Switcher**: Live dropdown to evaluate and compare risk scores using any of the 5 trained ML models (Logistic Regression, Decision Tree, Bagging, AdaBoost, Naive Bayes).
- **Form Evaluator**: Dropdown selection for Road Type, Junction, Weather, Light, and Speed Limit.
- **Real-Time Risk Gauge**: Visual Plotly gauge indicator with risk categories (Low, Moderate, High, Critical).
- **Historical Evidence Breakdown**: Real collision counts (Total, Severe, Fatal, Serious, Severe Rate %).
- **SHAP Factor List**: Transparent explanation of features increasing or decreasing risk.
- **Council Shortlist Table & CSV Export**: Interactive budget slider ($K=5..50$) with a one-click browser CSV export button.
- **EDA & Publication Plots Gallery**: Dedicated high-resolution tab showcasing Matplotlib & Seaborn distribution charts and risk curves.
- **Chi-Square Statistical View**: Interactive contingency bar charts and metric cards.
- **Query Audit History Viewer**: Table rendering past logged queries from SQLite DB with live refresh.

---

## 📁 Repository Structure

```
Project-I/
├── dft-road-casualty-statistics-collision-2025.csv       # 101,525 DfT STATS19 records
├── Accident_Severity_Flagger_Notebook.ipynb              # Interactive Jupyter Notebook
├── src/
│   ├── __init__.py
│   ├── decoder.py               # STATS19 Categorical Decoder
│   ├── statistical_analysis.py  # Chi-Square Tests & Cramér's V Engine
│   ├── probabilistic_engine.py  # Bayesian Risk Multipliers & Shortlist Generator
│   ├── baselines.py            # Majority Class & Group-by Road Type Baselines
│   ├── model_trainer.py        # ML Training Engine (LR, DT, Bagging, AdaBoost, NB)
│   ├── metrics_evaluation.py   # Precision@K, Recall@K & Bootstrapped 95% CIs
│   ├── explainability.py       # SHAP Feature Attribution
│   ├── visualization.py       # Matplotlib & Seaborn Data Visualization Engine
│   └── database.py             # SQLAlchemy SQLite Audit Logging
├── backend/
│   ├── app.py                  # Flask REST API Server (Dynamic Model Selection)
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── index.html              # Officer Dashboard HTML
│   ├── css/style.css           # Premium Dark Glassmorphism CSS
│   └── js/app.js               # Frontend Controller, Plotly Visuals & CSV Export
├── tests/
│   ├── test_api.py             # Pytest for Flask REST API endpoints
│   ├── test_database.py        # Pytest for SQLite ORM & Audit Logging
│   ├── test_decoder.py         # Pytest for decoder
│   ├── test_stats.py           # Pytest for statistical tests
│   └── test_models.py          # Pytest for ML models & metrics
├── models_saved/               # Serialized ML Models & Preprocessor (.joblib)
├── reports/
│   ├── chi_square_report.json  # Chi-square statistical report
│   ├── model_benchmark.json    # Precision@K benchmark results
│   ├── council_summary.csv     # Exportable Top-30 Council Shortlist
│   └── visualizations/         # Saved Matplotlib & Seaborn PNG plots
├── run_all.py                  # Master Pipeline Execution Script
└── README.md                   # Complete Academic Documentation
```

---

## ⚙️ How to Run the Project

### 1. Install Dependencies
```bash
python -m pip install -r backend/requirements.txt
```

### 2. Run Master Execution Pipeline
Executes data decoding, chi-square tests, ML model training, evaluation bootstrapping, report exports, pytest tests, and launches the web application server:

```bash
python run_all.py
```

### 3. Open Web Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 4. Run Unit Test Suite Individually
```bash
python -m pytest tests/
```

---

## 🎯 College Presentation Checklist & Highlights
- [x] **Problem Statement Realism**: Solves a real UK local council budget allocation problem.
- [x] **Data Size**: 101,525 full DfT STATS19 collision records.
- [x] **Mathematical Rigor**: Chi-square tests of independence, Cramér's V effect size, Bayesian conditional probabilities, 1,000 bootstrap iterations for 95% CIs.
- [x] **Machine Learning Depth**: 5 ML classifiers compared against 2 non-ML baselines with class imbalance handling.
- [x] **Explainability**: SHAP value attributions explaining risk drivers.
- [x] **Software Engineering Quality**: Flask REST API, SQLite database logging with ORM, 6 passing unit tests.
- [x] **Frontend Polish**: Responsive dark glassmorphism dashboard with Plotly gauge charts, dynamic shortlist slider, and audit log tables.

**Student Name**: Kunche Abhishek  
**Course / Level**: Second Year (Semester 1) — Project-I
