import sqlite3
import pandas as pd

print("Loading data...")
df = pd.read_csv('Final-Database.csv.xls')

# Convert these to numeric just in case there are blank text spaces in your CSV
for col in ['overall_satisfaction', '11- Rate GYM ', '12- Rate Hostel']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

print("Calculating averages for all columns...")
aggregated_data = df.groupby('college_name').agg(
    response_count=('college_name', 'count'),
    placement_score=('placement_score', 'mean'),
    higher_study_score=('higher_study_score', 'mean'),
    gov_exam_score=('gov_exam_score', 'mean'),
    coding_env_score=('coding_env_score', 'mean'),
    faculty_score=('faculty_score', 'mean'),
    college_life_score=('college_life_score', 'mean'),
    sports_score=('sports_score', 'mean'),
    avg_confidence=('confidence_score', 'mean'),
    min_rank=('min_mhtcet_rank', 'min'),
    max_rank=('max_mhtcet_rank', 'max'),
    # --- NEW EXTRA COLUMNS ---
    overall_satisfaction=('overall_satisfaction', 'mean'),
    gym_rating=('11- Rate GYM ', 'mean'),
    hostel_rating=('12- Rate Hostel', 'mean')
).reset_index()

print("Saving to SQLite database...")
conn = sqlite3.connect('database.sqlite')
aggregated_data.to_sql('colleges', conn, if_exists='replace', index=False)
conn.close()

print("Success! Database updated with extra columns.")