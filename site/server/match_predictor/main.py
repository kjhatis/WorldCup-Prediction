import os
import pickle
from pprint import pprint

import numpy as np
import pandas as pd

from .mean_stats import get_average_goals
from .player_stats import find_player_stats

__all__ = [
    "get_nbest_scores",
    "predict_proba",
    "xgb_model",
    "stage_encoder",
    "team_name_encoder",
]

# # # SET CURRENT FILE DIR # # #
DIR = os.path.abspath(os.path.dirname(__file__))

# # # LOAD ML Utils # # #
with open(os.path.join(DIR, "./ml_data/xgb_model.b"), "rb") as f:
    xgb_model = pickle.load(f)

with open(os.path.join(DIR, "./ml_data/stage_encoder.b"), "rb") as f:
    stage_encoder = pickle.load(f)

with open(os.path.join(DIR, "./ml_data/team_name_encoder.b"), "rb") as f:
    team_name_encoder = pickle.load(f)
# # # # # # # # # # # # #

def get_nbest_scores(team_name, n=11):
    with open(os.path.join(DIR, "./ml_data/team_players.b"), "rb") as f:
        team_players = pickle.load(f)

    players = team_players[team_name]
    scores = []

    # pprint(players)
    for i in range(len(players)):
        try:
            scores.append(int(players[i][1]))
            continue

        except:
            player_score = int(find_player_stats(players[i])["Overall"])
            scores.append(player_score)
            team_players[team_name][i] = [players[i], player_score]

    # pprint(team_players)
    with open(os.path.join(DIR, "./ml_data/team_players.b"), "wb") as f:
        pickle.dump(team_players, f)

    scores.sort()
    return scores[:n]

def predict_proba(stage, attendance, home_team_name, away_team_name):
    feature_names = [
        "Stage", "Home Team Name", "Away Team Name",
        "Attendance",
        "Player 1 Overall Diff",
        "Player 2 Overall Diff",
        "Player 3 Overall Diff",
        "Player 4 Overall Diff",
        "Player 5 Overall Diff",
        "Player 6 Overall Diff",
        "Player 7 Overall Diff",
        "Player 8 Overall Diff",
        "Player 9 Overall Diff",
        "Player 10 Overall Diff",
        "Player 11 Overall Diff",
        "Mean Home Team Goals", "Mean Away Team Goals"
    ]

    data = []

    # Stage
    data.append(stage_encoder.transform([stage])[0])
    # Home Team Name
    data.append(team_name_encoder.transform([home_team_name])[0])
    # Away Team Name
    data.append(team_name_encoder.transform([away_team_name])[0])
    # Attendance
    data.append(attendance)

    # Overall
    home_players_scores = get_nbest_scores(home_team_name)
    away_players_scores = get_nbest_scores(away_team_name)
    for i in range(11):
        data.append(home_players_scores[i] - away_players_scores[i])

    avg_goals = get_average_goals(home_team_name, away_team_name)
    if avg_goals != 0:
        # Mean Home Team Goals
        data.append(avg_goals[0])
        # Mean Away Team Goals
        data.append(avg_goals[1])
    else:
        data.append(0.0)
        data.append(0.0)

    df = pd.DataFrame(columns=feature_names)
    data = pd.Series(data, index=feature_names)
    df = df.append(data, ignore_index=True)
    df = df.append(data, ignore_index=True)

    # 0 -> Draw
    # 1 -> Home
    # 2 -> Away
    return xgb_model.predict_proba(df)[0]
