# TARDIS — Predicting SNCF Train Delays

A data-science project that explores French railway (SNCF) data, trains a model
to **predict the average arrival delay** of a train journey, and serves the
results through an interactive **Streamlit** dashboard.

## Highlights

- **Exploratory data analysis** of SNCF delays (`tardis_eda.ipynb`)
- **Model training** pipeline with preprocessing + estimator (`tardis_model.ipynb`),
  exported as `model.joblib`
- **Interactive dashboard** (`tardis_dashboard.py`) with three tabs:
  - **Overview** — headline KPIs (average delay, punctuality, cancellation rate),
    a year × month delay heatmap, and delay distribution / cumulative curves
  - **Exploration** — filterable rankings of the most-delayed stations and routes
  - **Prediction** — enter a journey and get the model's predicted delay,
    compared against the route's history, plus the model's feature importances

## Tech Stack

Python • pandas • NumPy • scikit-learn • joblib • Streamlit • Matplotlib •
Seaborn • Jupyter

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the dashboard

```bash
streamlit run tardis_dashboard.py
```

The dashboard loads `cleaned_dataset.csv` and the trained `model.joblib`.

### Reproduce the analysis & model

Open the notebooks in Jupyter:

```bash
jupyter notebook tardis_eda.ipynb     # exploratory data analysis
jupyter notebook tardis_model.ipynb   # feature engineering + model training
```

## Project Layout

```
tardis_eda.ipynb       exploratory data analysis
tardis_model.ipynb     feature engineering & model training
tardis_dashboard.py    Streamlit dashboard (overview / exploration / prediction)
cleaned_dataset.csv    cleaned dataset used by the dashboard
model.joblib           trained scikit-learn pipeline (prep + model)
requirements.txt       pinned Python dependencies
```

## Model

The model is a scikit-learn `Pipeline` (`prep` → `model`) predicting the
*average delay of all trains at arrival* from journey features: service type,
departure/arrival stations, route, month, year, journey time, traffic pressure,
cancellation severity, fault breakdown and delay probability. A train is
considered *on time* under a 5-minute arrival delay.
