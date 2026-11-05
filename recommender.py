import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class DecisionEngine:
    def __init__(self, db_path="database.sqlite"):
        self.db_path = db_path
        self.features = [
            "placement_score", "higher_study_score", "gov_exam_score", 
            "coding_env_score", "faculty_score", "college_life_score", "sports_score"
        ]
        self.feature_names = [
            "placement opportunities", "higher studies support", "government exam preparation", 
            "coding environment", "faculty quality", "campus life", "sports facilities"
        ]

    def _get_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM colleges", conn)
        conn.close()
        return df.fillna(0)

    # --- Fetch exact data for the Chatbot ---
    def get_college_details(self, college_name):
        df = self._get_data()
        college_data = df[df['college_name'] == college_name]
        if college_data.empty:
            return None
        return college_data.iloc[0].to_dict()

    def generate_explanation(self, college_name, user_vector, college_vector):
        diffs = np.abs(np.array(user_vector) - np.array(college_vector))
        best_match_indices = diffs.argsort()[:2] 
        reason_1 = self.feature_names[best_match_indices[0]]
        reason_2 = self.feature_names[best_match_indices[1]]
        return f"{college_name} is highly recommended because its {reason_1} and {reason_2} closely align with your specific priorities."

    def calculate_admission_chance(self, user_rank, min_rank, max_rank):
        # Prevent division by zero if data is missing
        if max_rank <= 0: 
            return {"label": "Data Unavailable", "level": "reach", "value": 10}
            
        if user_rank <= min_rank:
            return {"label": "Safe (High Probability)", "level": "safe", "value": 92}
        elif user_rank <= (min_rank + max_rank) / 2:
            return {"label": "Good Chance", "level": "good", "value": 75}
        elif user_rank <= max_rank:
            return {"label": "Borderline Match", "level": "borderline", "value": 45}
        else:
            return {"label": "Tough Reach", "level": "reach", "value": 15}

    # --- FEASIBILITY-AWARE ML RECOMMENDATION ---
    def get_recommendations(self, user_rank, user_preferences, target_branch="cs", top_n=50):
        df = self._get_data()
        
        # 1. Identify the correct cutoff columns for the selected branch
        min_col = f"{target_branch}_min_rank"
        max_col = f"{target_branch}_max_rank"

        # 2. Create a weighting function to penalize impossible colleges
        def get_rank_weight(row):
            b_min = row.get(min_col, row.get('min_rank', 0))
            b_max = row.get(max_col, row.get('max_rank', 0))
            
            # If the user's rank is completely out of bounds (more than 1.5x the max cutoff),
            # we slash their ML Match Score in half so it drops down the list.
            if b_max > 0 and user_rank > (b_max * 1.5):
                return 0.5 
            return 1.0

        # 3. Calculate ML Vector Similarity 
        user_vector = [user_preferences[feat] for feat in self.features]
        college_vectors = df[self.features].values
        similarities = cosine_similarity([user_vector], college_vectors)[0]
        
        # 4. Apply the rank weight BEFORE sorting!
        df['rank_weight'] = df.apply(get_rank_weight, axis=1)
        df['match_score'] = np.round((similarities * 100) * df['rank_weight'], 1)
        
        # 5. Sort by the new weighted score so branch feasibility actually changes the order
        top_colleges = df.sort_values(by='match_score', ascending=False).head(top_n)
        
        results = []
        for _, row in top_colleges.iterrows():
            coll_vec = [row[feat] for feat in self.features]
            
            # Get specific branch bounds
            b_min = row.get(min_col, row.get('min_rank', 0))
            b_max = row.get(max_col, row.get('max_rank', 0))
            
            chances = self.calculate_admission_chance(user_rank, b_min, b_max)
            
            # Dynamic explanation mentioning the branch
            explanation = f"Based on your {target_branch.upper()} goal and rank of {user_rank}, {row['college_name']} offers the best data alignment."
            
            results.append({
                "college_name": str(row['college_name']),
                "match_score": float(row['match_score']),
                "response_count": int(row['response_count']),
                "avg_confidence": float(np.round(row.get('avg_confidence', 0), 1)),
                "explanation": str(explanation),
                "admission_chance": chances,
                "metrics": {feat: float(np.round(row[feat], 1)) for feat in self.features},
                "extra_data": {
                    "Target Branch": target_branch.upper(), 
                    "Historical Min Rank": int(b_min),
                    "Historical Max Rank": int(b_max),
                    "Overall Satisfaction": float(np.round(row.get('overall_satisfaction', 0), 1)),
                    "Hostel Facilities Rating": float(np.round(row.get('hostel_rating', 0), 1))
                }
            })
            
        return results

    def get_admin_dashboard_data(self):
        df = self._get_data()
        global_avg = df[self.features].mean().to_dict()
        colleges = df[['college_name', 'response_count'] + self.features].to_dict('records')
        
        return {
            "global_average": {k: float(np.round(v, 1)) for k, v in global_avg.items()},
            "colleges": [
                {k: (int(v) if k == 'response_count' else (str(v) if k == 'college_name' else float(v))) for k, v in c.items()} 
                for c in colleges
            ]
        }   