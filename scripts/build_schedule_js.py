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

import re

TIME_24H_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")
TIME_12H_RE = re.compile(r"^\s*(\d{1,2})(?::?(\d{2}))?\s*([AaPp][Mm])\s*$")

def format_shift_time(val: str) -> str:
    """
    Convert times into your simple format:
    14:00 -> 2PM
    11:00 -> 11AM
    10:15 -> 1015AM
    16:15 -> 415PM
    Also keeps existing 2PM, 11AM, 415PM formats as is.
    """
    s = normalize_cell(val)

    up = s.upper().strip()
    if up in NON_SHIFT_VALUES:
        return up if up else "OFF"

    # Already in AM PM format like 2PM, 11AM, 4:15PM, 415PM
    m12 = TIME_12H_RE.match(s)
    if m12:
        hour = int(m12.group(1))
        mins = m12.group(2) or "00"
        ampm = m12.group(3).upper()

        if mins == "00":
            return f"{hour}{ampm}"
        return f"{hour}{mins}{ampm}"

    # 24 hour format like 14:00 or 14:00:00
    m24 = TIME_24H_RE.match(s)
    if m24:
        hour24 = int(m24.group(1))
        mins = m24.group(2)

        ampm = "AM" if hour24 < 12 else "PM"
        hour12 = hour24 % 12
        if hour12 == 0:
            hour12 = 12

        if mins == "00":
            return f"{hour12}{ampm}"
        return f"{hour12}{mins}{ampm}"

    # Anything else, leave untouched (covers notes, weird tokens, etc)
    return s.strip()



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
            am = format_shift_time(row.get(f"{day}_AM", "OFF"))
            pm = format_shift_time(row.get(f"{day}_PM", "OFF"))


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
