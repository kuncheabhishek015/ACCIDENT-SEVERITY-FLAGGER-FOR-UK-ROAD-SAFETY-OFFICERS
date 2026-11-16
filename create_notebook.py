import json

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Accident Severity Flagger for UK Road Safety Officers\n",
                "**Academic Project Notebook — Project-I (Semester 1)**  \n",
                "**Student Name**: Kunche Abhishek  \n",
                "\n",
                "---\n",
                "## 📌 Overview\n",
                "This interactive Jupyter Notebook contains the complete end-to-end data science pipeline:\n",
                "1. **STATS19 Data Loading & Categorical Decoding** (101,525 DfT collision records).\n",
                "2. **Exploratory Data Analysis (EDA) & Visualizations** (Matplotlib & Seaborn).\n",
                "3. **Mathematics of Probability & Statistical Independence** ($\\chi^2$ test, Cramér's V, Bayesian conditional risk).\n",
                "4. **Machine Learning Classifiers & Baselines** (Logistic Regression, Decision Tree, Bagging, AdaBoost, Naive Bayes).\n",
                "5. **Budget-Constrained Evaluation** ($\\text{Precision@K}$, $\\text{Recall@K}$, 1,000 Bootstrapped 95% CIs).\n",
                "6. **SHAP Feature Explainability** & **Council Prioritized Shortlist**."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### ⚙️ Step 0: Import Libraries & Environment Setup"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "import os\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "from scipy import stats\n",
                "\n",
                "# Set plot style\n",
                "sns.set_theme(style=\"darkgrid\")\n",
                "plt.rcParams[\"figure.figsize\"] = (10, 5)\n",
                "print(\"✓ Environment Initialized Successfully.\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                "## 1️⃣ STATS19 Categorical Decoding & Data Loading"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.decoder import Stats19Decoder\n",
                "\n",
                "data_path = \"dft-road-casualty-statistics-collision-2025.csv\"\n",
                "decoder = Stats19Decoder(data_path)\n",
                "decoded_df = decoder.decode()\n",
                "clean_df = decoder.get_clean_features_df()\n",
                "\n",
                "print(f\"Total Collision Records: {len(decoded_df):,}\")\n",
                "print(f\"Severe Collision Proportion: {clean_df['is_severe'].mean() * 100:.2f}%\")\n",
                "clean_df.head()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                "## 2️⃣ Exploratory Data Analysis (EDA) & Data Visualizations"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.visualization import DataVisualizationEngine\n",
                "\n",
                "viz = DataVisualizationEngine(decoded_df)\n",
                "# 1. Plot Severity Target Distribution\n",
                "viz.plot_severity_distribution()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 2. Weather vs. Light Severe Risk Heatmap\n",
                "viz.plot_weather_light_risk_heatmap()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 3. Speed Limit Collision & Severe Risk Rate Distribution\n",
                "viz.plot_speed_limit_risk_distribution()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                "## 3️⃣ Mathematics of Probability & Statistical Independence ($\\chi^2$ & Cramér's V)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.statistical_analysis import run_full_statistical_analysis\n",
                "\n",
                "stats_report = run_full_statistical_analysis(clean_df)\n",
                "w_test = stats_report[\"tests\"][\"weather_conditions\"]\n",
                "l_test = stats_report[\"tests\"][\"light_conditions\"]\n",
                "\n",
                "print(f\"Weather vs Severity: Chi2 = {w_test['chi2_statistic']}, p = {w_test['p_value_formatted']}, df = {w_test['degrees_of_freedom']}, Cramér V = {w_test['cramers_v']}\")\n",
                "print(f\"Light vs Severity:   Chi2 = {l_test['chi2_statistic']}, p = {l_test['p_value_formatted']}, df = {l_test['degrees_of_freedom']}, Cramér V = {l_test['cramers_v']}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                "## 4️⃣ Machine Learning Models & Bootstrapped Precision@K Evaluation"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.model_trainer import AccidentSeverityModelTrainer\n",
                "\n",
                "trainer = AccidentSeverityModelTrainer(data_path)\n",
                "results = trainer.train_and_evaluate_all()\n",
                "trainer.save_artifacts(\"models_saved\")\n",
                "\n",
                "# Build Summary DataFrame\n",
                "summary_rows = []\n",
                "for model_name, res in results.items():\n",
                "    p25 = res[\"metrics_at_k\"][\"K_25\"]\n",
                "    summary_rows.append({\n",
                "        \"Model Name\": model_name,\n",
                "        \"ROC-AUC\": res[\"roc_auc\"],\n",
                "        \"Precision@25 (%)\": p25[\"precision_at_k_percent\"],\n",
                "        \"Precision@25 95% CI\": f\"[{p25['precision_at_k_ci95'][0]}, {p25['precision_at_k_ci95'][1]}]\",\n",
                "        \"Recall@25 (%)\": p25[\"recall_at_k_percent\"],\n",
                "        \"Accuracy (%)\": round(res[\"accuracy\"] * 100, 2)\n",
                "    })\n",
                "\n",
                "df_summary = pd.DataFrame(summary_rows)\n",
                "df_summary"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n",
                "## 5️⃣ Council Top-K Prioritized Interventions Shortlist"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.probabilistic_engine import ProbabilisticRiskEngine\n",
                "\n",
                "engine = ProbabilisticRiskEngine(decoded_df)\n",
                "shortlist = engine.generate_prioritized_shortlist(top_k=15)\n",
                "df_shortlist = pd.DataFrame(shortlist)\n",
                "df_shortlist"
            ]
        }
    ],
    "metadata": {
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open("Accident_Severity_Flagger_Notebook.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print("Created Jupyter Notebook: Accident_Severity_Flagger_Notebook.ipynb")
