import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
import joblib


## - Initialisation

# File paths for the dataset and the trained model
DATASET_PATH = "cleaned_dataset.csv"
MODEL_PATH = "model.joblib"

# Set up the Streamlit page
st.set_page_config(
    page_title="TARDIS - Retards SNCF",
    page_icon=":train:",
    layout="wide",
)


# Load the dataset and add a proper date column
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH)
    return df


# Load the trained model
@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


# A train is considered on time if its delay is under 5 minutes
PUNCTUALITY_THRESHOLD_MIN = 5.0
DELAY_COL = "Average delay of all trains at arrival"


## - Overview


# Show the 4 metrics at the top of the overview tab
def render_kpis(df: pd.DataFrame):
    # Compute the four headline numbers
    avg_delay = df[DELAY_COL].mean()
    total_trips = int(df["real_nb_train"].sum())
    punctuality = (df[DELAY_COL] <= PUNCTUALITY_THRESHOLD_MIN).mean() * 100
    cancel_rate = df["Cancellation_Severity"].mean() * 100

    # Display them as four side-by-side metric cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Retard moyen à l'arrivée", f"{avg_delay:.2f} min")
    col2.metric("Trajets totaux", f"{total_trips:,}".replace(",", " "))
    col3.metric(
        f"Ponctualité (≤ {PUNCTUALITY_THRESHOLD_MIN:.0f} min)",
        f"{punctuality:.1f} %",
    )
    col4.metric("Taux d'annulation", f"{cancel_rate:.2f} %")


# Short month labels used on the heatmap
MONTH_LABELS = {
    1: "JAN",
    2: "FEV",
    3: "MARS",
    4: "AVR",
    5: "MAI",
    6: "JUIN",
    7: "JUIL",
    8: "AOUT",
    9: "SEPT",
    10: "OCT",
    11: "NOV",
    12: "DEC",
}


# Show a heatmap of average delays per month, for the last 3 years
def render_delay_heatmap(df: pd.DataFrame):
    # Keep only the 3 most recent years
    last_three_years = sorted(df["Year"].unique())[-3:]
    recent_df = df[df["Year"].isin(last_three_years)]

    # Build the year x month table of average delays
    delay_by_year_month = recent_df.pivot_table(
        index="Year", columns="Month", values=DELAY_COL, aggfunc="mean"
    )
    delay_by_year_month = delay_by_year_month.rename(columns=MONTH_LABELS)

    # Draw the heatmap
    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(delay_by_year_month, annot=True, fmt=".1f", cmap="RdYlGn_r", ax=ax)
    ax.set_title(
        "Retard moyen à l'arrivée par année x mois (minutes) - 3 dernières années"
    )
    ax.set_xlabel("Mois")
    ax.set_ylabel("Année")
    st.pyplot(fig)


# Common figure size for the two side-by-side graphs
SIDE_BY_SIDE_FIGSIZE = (8, 5)


# Show how delays are distributed across all observations
def render_delay_distribution(df: pd.DataFrame):
    # Count how often each rounded delay value appears
    delay_counts = df[DELAY_COL].round().value_counts()

    fig, ax = plt.subplots(figsize=SIDE_BY_SIDE_FIGSIZE)
    sns.lineplot(x=delay_counts.index, y=delay_counts.values, ax=ax)
    ax.set_xlim(0, 30)
    ax.set_ylim(0)
    ax.set_title("Distribution des retards à l'arrivée")
    ax.set_xlabel("Retard (minutes, arrondi)")
    ax.set_ylabel("Nombre d'observations route-mois")
    fig.tight_layout()
    st.pyplot(fig, width='stretch')


# Show the cumulative distribution of delays, with the median highlighted
def render_delay_cdf(df: pd.DataFrame):
    # Sort delays and compute the percentage
    sorted_delays = df[DELAY_COL].sort_values().reset_index(drop=True)
    cumulative_percentage = (sorted_delays.index + 1) / len(sorted_delays) * 100

    fig, ax = plt.subplots(figsize=SIDE_BY_SIDE_FIGSIZE)
    ax.plot(sorted_delays, cumulative_percentage, color="steelblue")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 100)

    # Add reference lines for the median
    median_delay = df[DELAY_COL].quantile(0.5)
    ax.axhline(
        50, color="gray", linestyle=":", label=f"Médiane (P50 = {median_delay:.1f} min)"
    )
    ax.axvline(median_delay, color="gray", linestyle=":")

    ax.set_title("Distribution cumulative des retards")
    ax.set_xlabel("Retard (minutes)")
    ax.set_ylabel("% d'observations ≤ X")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig, width='stretch')


# Render the full overview tab
def render_overview(df: pd.DataFrame):
    st.header("Vue d'ensemble")
    render_kpis(df)
    render_delay_heatmap(df)
    # Place the two distribution graphs side by side
    col_dist, col_cdf = st.columns(2)
    with col_dist:
        render_delay_distribution(df)
    with col_cdf:
        render_delay_cdf(df)


## - Exploration


# Show the filter controls and return the filtered dataset
def apply_exploration_filters(df: pd.DataFrame) -> pd.DataFrame:
    # Collect the user's filter choices
    with st.expander("Filtres", expanded=True):
        service_col, departure_col, arrival_col = st.columns(3)
        selected_services = service_col.multiselect(
            "Service", sorted(df["Service"].unique())
        )
        selected_departures = departure_col.multiselect(
            "Gare de départ", sorted(df["Departure station"].unique())
        )
        selected_arrivals = arrival_col.multiselect(
            "Gare d'arrivée", sorted(df["Arrival station"].unique())
        )
        year_col, month_col = st.columns(2)
        min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
        selected_years = year_col.slider(
            "Plage d'années", min_year, max_year, (min_year, max_year)
        )
        selected_months = month_col.slider("Plage de mois", 1, 12, (1, 12))

    # Keep only the rows that match every active filter
    row_mask = pd.Series(True, index=df.index)
    if selected_services:
        row_mask &= df["Service"].isin(selected_services)
    if selected_departures:
        row_mask &= df["Departure station"].isin(selected_departures)
    if selected_arrivals:
        row_mask &= df["Arrival station"].isin(selected_arrivals)
    row_mask &= df["Year"].between(selected_years[0], selected_years[1])
    row_mask &= df["Month"].between(selected_months[0], selected_months[1])
    return df[row_mask]


# Show the top 10 most delayed departure and arrival stations
def render_top_stations(df: pd.DataFrame):
    # Average delay per station, then keep the worst 10
    top_departure_stations = (
        df.groupby("Departure station")[DELAY_COL].mean().nlargest(10).reset_index()
    )
    top_arrival_stations = (
        df.groupby("Arrival station")[DELAY_COL].mean().nlargest(10).reset_index()
    )

    # Display both graphs side by side
    departure_col, arrival_col = st.columns(2)
    with departure_col:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(
            data=top_departure_stations,
            x=DELAY_COL,
            y="Departure station",
            hue="Departure station",
            palette="Reds_r",
            legend=False,
            ax=ax,
        )
        ax.set_title("Top 10 gares de départ les plus en retard")
        ax.set_xlabel("Retard moyen (minutes)")
        ax.set_ylabel("")
        fig.tight_layout()
        st.pyplot(fig, width='stretch')
    with arrival_col:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(
            data=top_arrival_stations,
            x=DELAY_COL,
            y="Arrival station",
            hue="Arrival station",
            palette="Reds_r",
            legend=False,
            ax=ax,
        )
        ax.set_title("Top 10 gares d'arrivée les plus en retard")
        ax.set_xlabel("Retard moyen (minutes)")
        ax.set_ylabel("")
        fig.tight_layout()
        st.pyplot(fig, width='stretch')


# Show the top 10 most delayed routes
def render_top_routes(df: pd.DataFrame):
    # Average delay per route, then keep the worst 10
    top_routes = df.groupby("Route")[DELAY_COL].mean().nlargest(10).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=top_routes,
        x=DELAY_COL,
        y="Route",
        hue="Route",
        palette="Reds_r",
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 10 routes les plus en retard")
    ax.set_xlabel("Retard moyen (minutes)")
    ax.set_ylabel("")
    fig.tight_layout()
    st.pyplot(fig, width='stretch')


# Render the full exploration tab
def render_exploration(df: pd.DataFrame):
    st.header("Exploration")

    # Apply the user filters first
    filtered_df = apply_exploration_filters(df)
    if filtered_df.empty:
        st.warning("Aucune donnée ne correspond à ces filtres.")
        return

    # Show the row count, then draw the graphs
    st.caption(
        f"Sélection courante : **{len(filtered_df):,}** observations".replace(",", " ")
    )
    render_top_stations(filtered_df)
    render_top_routes(filtered_df)


## - Prediction

# Model features in order
MODEL_FEATURES = [
    "Service",
    "Departure station",
    "Arrival station",
    "Route",
    "Average journey time",
    "Month",
    "Year",
    "Traffic_Pressure",
    "Cancellation_Severity",
    "Hight_Delay_Impact",
    "Medium_Delay_Impact",
    "Light_Delay_Impact",
    "Internal_Fault_pct",
    "External_Fault_pct",
    "Delay_Probability",
]

# Model features filled by history
ADVANCED_FEATURES = [
    "Average journey time",
    "Traffic_Pressure",
    "Cancellation_Severity",
    "Hight_Delay_Impact",
    "Medium_Delay_Impact",
    "Light_Delay_Impact",
    "Internal_Fault_pct",
    "External_Fault_pct",
    "Delay_Probability",
]


# Show the prediction controls and return the filtered dataset
def render_prediction_form(df: pd.DataFrame):
    with st.form("prediction_form"):
        st.markdown("**Paramètres du trajet**")

        # Trip identity: service and stations
        service_col, departure_col, arrival_col = st.columns(3)
        selected_service = service_col.selectbox(
            "Service", sorted(df["Service"].unique())
        )
        selected_departure = departure_col.selectbox(
            "Gare de départ", sorted(df["Departure station"].unique())
        )
        selected_arrival = arrival_col.selectbox(
            "Gare d'arrivée", sorted(df["Arrival station"].unique())
        )

        # When the trip happens
        month_col, year_col = st.columns(2)
        selected_month = month_col.slider("Mois", 1, 12, 6)
        min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
        selected_year = year_col.slider("Année", min_year, max_year, max_year)

        # Build the route label and look up its history
        selected_route = f"{selected_departure}-{selected_arrival}"
        route_history = df[df["Route"] == selected_route]

        # Pre-fill advanced features with the route's averages, or the global ones if unknown
        default_values = (
            route_history[ADVANCED_FEATURES].mean()
            if not route_history.empty
            else df[ADVANCED_FEATURES].mean()
        )
        advanced_values = {col: float(default_values[col]) for col in ADVANCED_FEATURES}

        submitted = st.form_submit_button("Prédire le retard")

    # Nothing to return until the user submits the form
    if not submitted:
        return None
    return {
        "Service": selected_service,
        "Departure station": selected_departure,
        "Arrival station": selected_arrival,
        "Route": selected_route,
        "Month": selected_month,
        "Year": selected_year,
        **advanced_values,
    }


# Run the model on the user's choices and show the result next to the history
def render_prediction_result(df: pd.DataFrame, model, user_inputs: dict):
    # Predict the delay for the selected trip
    input_row = pd.DataFrame([user_inputs])[MODEL_FEATURES]
    predicted_delay = float(model.predict(input_row)[0])

    # Compare with the average delay on the same route, or globally if unknown
    selected_route = user_inputs["Route"]
    route_history = df[df["Route"] == selected_route]
    if route_history.empty:
        historical_mean = df[DELAY_COL].mean()
        mean_label = "Moyenne historique globale"
    else:
        historical_mean = route_history[DELAY_COL].mean()
        mean_label = "Moyenne historique de la route"

    # Show both numbers side by side
    prediction_col, history_col = st.columns(2)
    prediction_col.metric(
        "Retard prédit",
        f"{predicted_delay:.2f} min",
        delta=f"{predicted_delay - historical_mean:+.2f} min vs historique",
        delta_color="inverse",
    )
    history_col.metric(mean_label, f"{historical_mean:.2f} min")


# Model feature readable names
FEATURE_LABELS = {
    "Service": "Type de train (National / International)",
    "Departure station": "Gare de départ",
    "Arrival station": "Gare d'arrivée",
    "Route": "Liaison (départ → arrivée)",
    "Average journey time": "Durée moyenne du trajet (min)",
    "Month": "Mois de circulation",
    "Year": "Année de circulation",
    "Traffic_Pressure": "Pression du trafic (trains réalisés / prévus)",
    "Cancellation_Severity": "Taux d'annulation des trains",
    "Heavy_Delay_Impact": "Poids des retards supérieurs à 15 min",
    "Internal_Fault_pct": "Part des retards dus à la SNCF",
    "External_Fault_pct": "Part des retards d'origine externe",
    "Delay_Probability": "Probabilité d'un retard supérieur à 15 min",
}

# Categorical features (one-hot encoded by the model)
CATEGORICAL_FEATURES = {"Service", "Departure station", "Arrival station", "Route"}


# Turn a raw feature name from the model into a clean French label
def convert_feature_name(raw_feature_name: str) -> str:
    # Drop the encoder prefix
    cleaned_name = (
        raw_feature_name.split("__", 1)[1]
        if "__" in raw_feature_name
        else raw_feature_name
    )

    # Only keep the base name
    for categorical in CATEGORICAL_FEATURES:
        if cleaned_name.startswith(f"{categorical}_") or cleaned_name == categorical:
            return FEATURE_LABELS[categorical]
    return FEATURE_LABELS.get(cleaned_name, cleaned_name)


# Show the 10 features that influence the model the most
def render_feature_importances(model):
    # Get the model and the preprocessor
    estimator = model.named_steps.get("model")
    preprocessor = model.named_steps.get("prep")

    # Pair each feature with its importance score
    feature_names = preprocessor.get_feature_names_out()
    feature_importances = pd.Series(estimator.feature_importances_, index=feature_names)

    # Keep the top 10 and rename them for display
    top_features = (
        feature_importances.sort_values(ascending=False).head(10).reset_index()
    )
    top_features.columns = ["Caractéristique", "Importance"]
    top_features["Caractéristique"] = top_features["Caractéristique"].map(
        convert_feature_name
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=top_features,
        x="Importance",
        y="Caractéristique",
        hue="Caractéristique",
        palette="Reds_r",
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 10 caractéristiques les plus influentes du modèle")
    ax.set_xlabel("Importance")
    ax.set_ylabel("")
    fig.tight_layout()
    st.pyplot(fig, width='stretch')


# Render the full prediction tab
def render_prediction(df: pd.DataFrame, model):
    st.header("Prédiction")
    st.caption(
        "Saisis les paramètres d'un trajet, le modèle estime le retard moyen attendu "
        "à l'arrivée (en minutes)."
    )

    # Show the form first, then the result once the user submits
    user_inputs = render_prediction_form(df)
    if user_inputs is not None:
        render_prediction_result(df, model, user_inputs)

    # Bottom of the tab: explain how the model makes its decision
    st.divider()
    st.subheader("Comment le modèle prend ses décisions:")
    render_feature_importances(model)


## - Dashboard


# Main function
def main():
    st.title(":train: TARDIS - Prédire l'imprévisible")  # Set Dashboard title

    df = load_data()  # load dataframe
    model = load_model()  # load model

    overview, exploration, prediction = st.tabs(  # Set Dashboard differents tabs
        ["Vue d'ensemble", "Exploration", "Prédiction"]
    )
    with overview:
        render_overview(df)  # Load Overview tab with render_overview function
    with exploration:
        render_exploration(df)  # Load Exploration tab with render_exploration function
    with prediction:
        render_prediction(
            df, model
        )  # Load Prediction tab with render_prediction function


main()
