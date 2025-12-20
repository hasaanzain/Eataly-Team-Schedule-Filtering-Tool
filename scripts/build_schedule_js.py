from pathlib import Path
import subprocess
data_dir = Path("data")   # change if your CSVs are elsewhere
csv_files = list(data_dir.glob("*.csv"))
latest_csv = None
latest_time = -1
for csv in csv_files:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", str(csv)],
        capture_output=True,
        text=True
    )
    commit_time = result.stdout.strip()
    if not commit_time:
        continue
    commit_time = int(commit_time)
    if commit_time > latest_time:
        latest_time = commit_time
        latest_csv = csv


#Import Pandas
import pandas as pd

#load in from CSV
df = pd.read_csv(latest_csv)


#drop all irrelevant rows at the top
df = df.drop([0,2,3,4])

#reset indexes
df = df.reset_index(drop=True)


#rename the column names:
df = df.rename(columns={df.columns[0]: "Name"})
df = df.rename(columns={df.columns[1]: "Monday_AM"})
df = df.rename(columns={df.columns[2]: "Monday_PM"})
df = df.rename(columns={df.columns[3]: "Tuesday_AM"})
df = df.rename(columns={df.columns[4]: "Tuesday_PM"})
df = df.rename(columns={df.columns[5]: "Wednesday_AM"})
df = df.rename(columns={df.columns[6]: "Wednesday_PM"})
df = df.rename(columns={df.columns[7]: "Thursday_AM"})
df = df.rename(columns={df.columns[8]: "Thursday_PM"})
df = df.rename(columns={df.columns[9]: "Friday_AM"})
df = df.rename(columns={df.columns[10]: "Friday_PM"})
df = df.rename(columns={df.columns[11]: "Saturday_AM"})
df = df.rename(columns={df.columns[12]: "Saturday_PM"})
df = df.rename(columns={df.columns[13]: "Sunday_AM"})
df = df.rename(columns={df.columns[14]: "Sunday_PM"})


#Clean up events row by replacing empty cells with 'none'
df.iloc[0] = df.iloc[0].fillna("None")

#extract events as a list
first_row_list = df.iloc[0].tolist()

# df = df.drop(df.columns[15:], axis=1)
# #remove events row
df = df.drop(0)

#reset indexes
df = df.reset_index(drop=True)

#replace all empty cells with 'OFF'
df = df.fillna('OFF')



days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

pairs_per_row = []   # this will hold one list per row

for row_index in range(len(df)):
    row = df.iloc[row_index]

    day_pairs = []

    # go through the 14 shift columns two at a time
    for col_index in range(1, 15, 2):
        first_shift = row[col_index]
        second_shift = row[col_index + 1]

        day_pairs.append([first_shift, second_shift])

    pairs_per_row.append(day_pairs)

# optional: attach it back to the dataframe
df["pairs"] = pairs_per_row



#now that we have a new column that is a list of lists for each person, we can combine the pairs of days 
#we iterate over each person

def combine_pair(x,y):
    x = str(x)
    y = str(y)
    
    if x == y:
        return x
        
    elif x == 'OFF' and y=='SET':
        return 'OFF'
    elif y == 'OFF' and y=='SET':
        return 'OFF'
        
    elif x!=y and y in ['OFF', 'SET']:
        return x
    elif x!=y and x in ['OFF', 'SET']:
        return y
        
    else:
        return [x,y]

combined_rows = []

for row_pairs in pairs_per_row:   # one employee at a time
    combined_days = []

    for pair in row_pairs:        # one day at a time
        x = pair[0]
        y = pair[1]

        combined_value = combine_pair(x, y)
        combined_days.append(combined_value)

    combined_rows.append(combined_days)


days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

scheduleData = []

for i in range(len(combined_rows)):
    # name from the first column of df, same row index i
    name = df.iloc[i, 0]

    # the 7 values for that person (Mon..Sun)
    week = combined_rows[i]

    person_dict = {"name": name}

    # assign each day
    for d in range(7):
        person_dict[days[d]] = week[d]

    scheduleData.append(person_dict)



import json

output_path = "scheduleData.js"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("export const scheduleData = ")
    json.dump(scheduleData, f, indent=2)
    f.write(";\n")
