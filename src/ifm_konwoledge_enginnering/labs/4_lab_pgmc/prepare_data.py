"""Przygotowanie danych do laboratorium PyMC (nadmiarowe zgony).

Pliki w katalogu data/ są dostarczane razem z instrukcją (przygotowane tym skryptem
13.11.2026), więc uruchamianie go NIE jest potrzebne do wykonania instrukcji ani zadań.
Skrypt dokumentuje sposób przygotowania danych i pozwala je zaktualizować; jego
uruchomienie NADPISUJE dostarczone pliki, a ponieważ źródła są aktualizowane
(lub mogą przestać być dostępne), wyniki mogą się wtedy różnić od podanych w instrukcji.

Skrypt pobiera:
  * World Mortality Dataset (Karlinsky, Kobak 2021) -> data/world_mortality.csv
  * dane COVID-19 z Our World in Data (archiwum repozytorium owid/covid-19-data)
    i zapisuje z nich jedynie zmienne opisujące kraje -> data/country_covariates.csv
  * dobowe temperatury w 10 dużych miastach Polski z archiwum Open-Meteo
    (https://open-meteo.com, licencja CC BY 4.0) i zapisuje ich miesięczne
    podsumowanie -> data/poland_temperature.csv (używane w rozwiązaniach zadań)

Plik OWID ma ok. 100 MB, dlatego jest pobierany do katalogu tymczasowego
i nie jest przechowywany. Uruchomienie: python prepare_data.py
"""

import json
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
WMD_URL = "https://raw.githubusercontent.com/akarlinsky/world_mortality/main/world_mortality.csv"
OWID_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

CITIES = {  # (szerokość, długość geograficzna)
    "Warszawa": (52.23, 21.01),
    "Kraków": (50.06, 19.94),
    "Łódź": (51.76, 19.46),
    "Wrocław": (51.11, 17.03),
    "Poznań": (52.41, 16.93),
    "Gdańsk": (54.35, 18.65),
    "Szczecin": (53.43, 14.55),
    "Lublin": (51.25, 22.57),
    "Białystok": (53.13, 23.16),
    "Katowice": (50.26, 19.02),
}


def poland_temperature(start="2015-01-01", end="2024-12-31", hot_threshold=30.0):
    """Miesięczna średnia temperatura i średnia liczba dni upalnych (Tmax >= próg) w 10 miastach."""
    query = urllib.parse.urlencode({
        "latitude": ",".join(str(lat) for lat, _ in CITIES.values()),
        "longitude": ",".join(str(lon) for _, lon in CITIES.values()),
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_mean,temperature_2m_max",
        "timezone": "Europe/Warsaw",
    })
    with urllib.request.urlopen(f"{METEO_URL}?{query}", timeout=300) as response:
        locations = json.load(response)
    daily = pd.concat(
        pd.DataFrame({
            "city": city,
            "date": pd.to_datetime(loc["daily"]["time"]),
            "tmean": loc["daily"]["temperature_2m_mean"],
            "tmax": loc["daily"]["temperature_2m_max"],
        })
        for city, loc in zip(CITIES, locations)
    )
    daily["hot"] = daily["tmax"] >= hot_threshold
    daily["month"] = daily["date"].dt.to_period("M").dt.to_timestamp()
    per_city = daily.groupby(["city", "month"]).agg(temp=("tmean", "mean"), hot_days=("hot", "sum"))
    out = per_city.groupby("month").mean()
    out.index.name = "date"
    return out.round(3).reset_index()

STATIC_COLUMNS = [
    "population",
    "population_density",
    "median_age",
    "aged_65_older",
    "aged_70_older",
    "gdp_per_capita",
    "cardiovasc_death_rate",
    "diabetes_prevalence",
    "hospital_beds_per_thousand",
    "life_expectancy",
    "human_development_index",
]


def last_value_before(df, column, date):
    """Ostatnia niepusta wartość kolumny z datą nie późniejszą niż `date` (dla każdego kraju)."""
    sub = df.loc[(df["date"] <= date) & df[column].notna(), ["iso_code", "date", column]]
    return sub.sort_values("date").groupby("iso_code")[column].last()


def country_covariates(owid):
    owid = owid[~owid["iso_code"].str.startswith("OWID_") | (owid["iso_code"] == "OWID_KOS")].copy()
    owid["iso_code"] = owid["iso_code"].replace({"OWID_KOS": "KOS"})
    owid["date"] = pd.to_datetime(owid["date"])

    static = owid.groupby("iso_code").agg(
        location=("location", "first"),
        continent=("continent", "first"),
        **{c: (c, "last") for c in STATIC_COLUMNS},
    )
    dynamic = pd.DataFrame(
        {
            # odsetek zaszczepionych co najmniej jedną dawką (gdy brak: w pełni zaszczepionych)
            "vaccinated_2021": last_value_before(owid, "people_vaccinated_per_hundred", "2021-12-31").combine_first(
                last_value_before(owid, "people_fully_vaccinated_per_hundred", "2021-12-31")
            ),
            "booster_2022": last_value_before(owid, "total_boosters_per_hundred", "2022-06-30"),
            "covid_deaths_pm_2020": last_value_before(owid, "total_deaths_per_million", "2020-12-31"),
            "covid_deaths_pm_2021": last_value_before(owid, "total_deaths_per_million", "2021-12-31"),
            "covid_deaths_pm_2022": last_value_before(owid, "total_deaths_per_million", "2022-12-31"),
            "owid_excess_pscore_2022": last_value_before(owid, "excess_mortality_cumulative", "2022-12-31"),
        }
    )
    in_period = owid[(owid["date"] >= "2020-03-01") & (owid["date"] <= "2021-12-31")]
    dynamic["stringency_2020_2021"] = in_period.groupby("iso_code")["stringency_index"].mean()

    out = static.join(dynamic)
    out.index.name = "iso3c"
    return out.reset_index()


def main():
    DATA.mkdir(exist_ok=True)
    print("Pobieranie World Mortality Dataset...")
    urllib.request.urlretrieve(WMD_URL, DATA / "world_mortality.csv")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "owid-covid-data.csv"
        print("Pobieranie danych OWID (ok. 100 MB)...")
        urllib.request.urlretrieve(OWID_URL, path)
        owid = pd.read_csv(path, low_memory=False)

    cov = country_covariates(owid)
    cov.to_csv(DATA / "country_covariates.csv", index=False, float_format="%.6g")
    print(f"Zapisano {len(cov)} krajów do {DATA / 'country_covariates.csv'}")

    print("Pobieranie temperatur z Open-Meteo...")
    temp = poland_temperature()
    temp.to_csv(DATA / "poland_temperature.csv", index=False)
    print(f"Zapisano {len(temp)} miesięcy do {DATA / 'poland_temperature.csv'}")


if __name__ == "__main__":
    main()
