from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
NON_SHIFT_VALUES = {"OFF", "SET", "REQ", "NONE", ""}


def newest_csv(data_dir: Path) -> Path:
    csvs = list(data_dir.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")
    csvs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return csvs[0]


def normalize_cell(val) -> str:
    s = "" if val is None else str(val).strip()
    if s.lower() == "nan" or s == "":
        return "OFF"
    return s


def clean_df_from_eataly_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Drop the rows you were dropping in your notebook
    # If your new CSV format changes later, adjust these indices.
    df = df.drop([0, 2, 3, 4], errors="ignore").reset_index(drop=True)

    # Rename the first column to Name if it is an unnamed column
    if "Unnamed: 0" in df.columns:
        df = df.rename(columns={"Unnamed: 0": "Name"})

    # Rename paired AM/PM columns
    rename_map = {
        "Monday": "Monday_AM",
        "Unnamed: 2": "Monday_PM",
        "Tuesday": "Tuesday_AM",
        "Unnamed: 4": "Tuesday_PM",
        "Wednesday": "Wednesday_AM",
        "Unnamed: 6": "Wednesday_PM",
        "Thursday": "Thursday_AM",
        "Unnamed: 8": "Thursday_PM",
        "Friday": "Friday_AM",
        "Unnamed: 10": "Friday_PM",
        "Saturday": "Saturday_AM",
        "Unnamed: 12": "Saturday_PM",
        "Sunday": "Sunday_AM",
        "Unnamed: 14": "Sunday_PM",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Fill empty cells as OFF
    df = df.fillna("OFF")

    # If the first row is an events row, your old notebook removed it.
    # This tries to detect it: if Name cell looks like "Events" or is blank, drop it.
    if len(df) > 0:
        first_name = normalize_cell(df.iloc[0].get("Name", ""))
        if first_name.upper() in {"EVENTS", "EVENT", "NONE", "OFF"} or first_name.strip() == "":
            df = df.drop(df.index[0]).reset_index(drop=True)

    return df


def df_to_schedule_data(df: pd.DataFrame) -> list[dict]:
    out: list[dict] = []

    for _, row in df.iterrows():
        name = normalize_cell(row.get("Name", "")).strip()
        if not name or name.upper() in NON_SHIFT_VALUES:
            continue

        person = {"name": name}

        for day, key in zip(DAYS, DAY_KEYS):
            am = normalize_cell(row.get(f"{day}_AM", "OFF"))
            pm = normalize_cell(row.get(f"{day}_PM", "OFF"))

            shifts = []
            if am.upper() not in NON_SHIFT_VALUES:
                shifts.append(am)
            if pm.upper() not in NON_SHIFT_VALUES:
                shifts.append(pm)

            if len(shifts) == 0:
                # Preserve SET if both are SET, otherwise OFF
                person[key] = "SET" if am.upper() == "SET" and pm.upper() == "SET" else "OFF"
            elif len(shifts) == 1:
                person[key] = shifts[0]
            else:
                person[key] = shifts

        out.append(person)

    return out


def write_schedule_js(out_path: Path, schedule_data: list[dict]) -> None:
    js = (
        "// AUTO GENERATED FILE. DO NOT EDIT.\n"
        "export const scheduleData = "
        + json.dumps(schedule_data, ensure_ascii=False, indent=2)
        + ";\n"
    )
    out_path.write_text(js, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_path = Path(args.out)

    latest_csv = newest_csv(data_dir)
    df = clean_df_from_eataly_csv(latest_csv)
    schedule_data = df_to_schedule_data(df)
    write_schedule_js(out_path, schedule_data)

    print(f"Used latest CSV: {latest_csv}")
    print(f"Wrote JS to: {out_path}")
    print(f"Rows exported: {len(schedule_data)}")


if __name__ == "__main__":
    main()
