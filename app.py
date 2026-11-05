from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import DecisionEngine
import time
import numpy as np
import sqlite3
import datetime
import pandas as pd

print("1. Imports successful...")
from recommender import DecisionEngine
print("2. Recommender imported...")
app = Flask(__name__)

CORS(app)
print("3. Initializing Decision Engine...")
engine = DecisionEngine(db_path="database.sqlite")
print("4. Engine Initialized!")
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "message": "Decision Engine Operational"})

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        user_rank = data.get('rank', 0)
        user_preferences = data.get('preferences', {})
        target_branch = data.get('branch', 'cs')
        recommendations = engine.get_recommendations(user_rank, user_preferences, target_branch, top_n=50)
        return jsonify({"status": "success", "data": recommendations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    try:
        data = engine.get_admin_dashboard_data()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def student_chat():
    data = request.json
    college_name = data.get('college_name', '')
    message = data.get('message', '').lower()
    
    college_data = engine.get_college_details(college_name)
    if not college_data:
        return jsonify({"status": "error", "reply": "I couldn't find database records for this college."})

    placement = float(np.round(college_data.get('placement_score', 0), 1))
    coding = float(np.round(college_data.get('coding_env_score', 0), 1))
    hostel = float(np.round(college_data.get('12- Rate Hostel', 0), 1))
    faculty = float(np.round(college_data.get('faculty_score', 0), 1))
    satisfaction = float(np.round(college_data.get('overall_satisfaction', 0), 1))
    responses = int(college_data.get('response_count', 0))

    if 'placement' in message or 'package' in message or 'job' in message or 'salary' in message:
        if placement >= 4.0: response = f"Based on {responses} student reviews, {college_name} has exceptional placements with a score of {placement}/5! Top recruiters actively hire from here."
        elif placement >= 3.0: response = f"Placements at {college_name} are decent, rated at {placement}/5 by current students."
        else: response = f"Students rate the placement opportunities at {college_name} at {placement}/5. You might need to rely heavily on off-campus drives here."
    elif 'hostel' in message or 'food' in message or 'stay' in message:
        if hostel >= 4.0: response = f"The hostel and mess facilities are highly rated at {hostel}/5!"
        elif hostel >= 2.5: response = f"The hostel facilities score {hostel}/5. Manageable, but PGs are also popular."
        else: response = f"Hostel facilities are rated quite low at {hostel}/5."
    elif 'coding' in message or 'hackathon' in message or 'tech' in message:
        if coding >= 4.0: response = f"The coding environment at {college_name} is outstanding ({coding}/5)."
        else: response = f"The coding culture is rated {coding}/5."
    elif 'faculty' in message or 'teacher' in message or 'academic' in message:
        if faculty >= 3.5: response = f"Students give the faculty a solid score of {faculty}/5."
        else: response = f"The teaching quality is rated at {faculty}/5."
    else:
        response = f"Overall, {college_name} has a student satisfaction score of {satisfaction}/5 based on {responses} verified reviews."
        
    time.sleep(1.2)
    return jsonify({"status": "success", "reply": response})

# --- NEW: Fetch list of unique colleges for dropdown ---
@app.route('/api/colleges', methods=['GET'])
def get_colleges():
    try:
        conn = sqlite3.connect('database.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT college_name FROM colleges ORDER BY college_name")
        colleges = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"status": "success", "data": colleges}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- UPDATED: Crowdsourced Data Pipeline ---
# --- PERFECTLY MAPPED CROWDSOURCED DATA PIPELINE ---
@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    try:
        import pandas as pd
        data = request.json
        conn = sqlite3.connect('database.sqlite')
        
        # 1. Fetch existing rank data to protect cutoffs
        df_existing = pd.read_sql(
            "SELECT min_rank, max_rank FROM colleges WHERE college_name=?", 
            conn, 
            params=(data.get('college_name'),)
        )
        
        # Safely calculate the mean cutoffs for this college
        df_existing['min_rank'] = pd.to_numeric(df_existing['min_rank'], errors='coerce')
        df_existing['max_rank'] = pd.to_numeric(df_existing['max_rank'], errors='coerce')
        
        safe_min = df_existing['min_rank'].mean() if not df_existing.empty else 0
        safe_max = df_existing['max_rank'].mean() if not df_existing.empty else 0
            
        # 2. Build the new row matching YOUR EXACT 15 COLUMNS
        new_row = {
            'college_name': data.get('college_name'),
            'response_count': 1, # Adds 1 new response
            'placement_score': float(data.get('placement_score', 3)),
            'higher_study_score': float(data.get('higher_study_score', 3)),
            'gov_exam_score': float(data.get('gov_exam_score', 3)),
            'coding_env_score': float(data.get('coding_env_score', 3)),
            'faculty_score': float(data.get('faculty_score', 3)),
            'college_life_score': float(data.get('college_life_score', 3)),
            'sports_score': float(data.get('sports_score', 3)),
            'avg_confidence': 5.0, # Default
            'min_rank': safe_min,
            'max_rank': safe_max,
            'overall_satisfaction': float(data.get('overall_satisfaction', 3)),
            'gym_rating': 3.0, # Default since it's not in the form
            'hostel_rating': float(data.get('hostel_rating', 3))
        }
        
        # 3. Append to database
        new_df = pd.DataFrame([new_row])
        new_df.to_sql('colleges', conn, if_exists='append', index=False)
        
        conn.close()
        return jsonify({"status": "success", "message": "Review added to dataset!"}), 200
        
    except Exception as e:
        print(f"\n--- CRITICAL DATABASE INSERT ERROR ---")
        print(str(e))
        print("--------------------------------------\n")
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == '__main__':
    print("Starting AI Backend on http://localhost:5000")
    app.run(debug=True, port=5000)