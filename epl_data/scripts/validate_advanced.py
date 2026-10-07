"""Independent provider and aggregation consistency checks for acquired data."""
from __future__ import annotations

import json

import pandas as pd

from common import ROOT, current_teams, now_utc


def main():
    whitelist = set(current_teams().team)
    folder = ROOT / "data" / "processed"
    understat = pd.read_csv(folder / "understat" / "matches.csv")
    espn = pd.read_csv(folder / "espn" / "match_info.csv")
    completed = understat[understat.isResult.eq(True)].copy()
    completed["date"] = pd.to_datetime(completed.datetime).dt.strftime("%Y-%m-%d")
    espn["date"] = pd.to_datetime(espn.match_datetime_utc).dt.strftime("%Y-%m-%d")
    merged = espn.merge(completed, on=["home_team", "away_team", "date"], suffixes=("_espn", "_understat"))
    mismatches = merged[(merged.home_goals != merged.goals__h) | (merged.away_goals != merged.goals__a)]
    profiles = pd.read_csv(folder / "espn" / "player_profiles.csv")
    metrics = pd.read_csv(folder / "understat" / "team_match_metrics.csv")
    findings = {
        "checked_at_utc": now_utc(),
        "independent_provider_scores": {"espn_completed_matches": len(espn), "matched_to_understat": len(merged),
                                        "unmatched_espn": len(espn[~espn.espn_match_id.isin(merged.espn_match_id)]),
                                        "score_mismatches": len(mismatches)},
        "current_player_profile_coverage": {"espn_clubs": profiles.team.nunique(), "espn_players": len(profiles),
                                            "focal_clubs_outside_whitelist": sorted(set(profiles.team) - whitelist)},
        "understat_team_history": {"completed_matches_with_focal_club": len(completed),
                                    "expected_focal_team_match_rows": int(completed.home_team.notna().sum()+completed.away_team.notna().sum()),
                                    "observed_focal_team_match_rows": len(metrics),
                                    "duplicate_team_match_keys": int(metrics.duplicated(["match_id", "team"]).sum()),
                                    "focal_clubs_outside_whitelist": sorted(set(metrics.team) - whitelist)},
        "observed_current_season_actual_match_coverage": {
            "understat_latest_source_datetime": completed[completed.season.eq("2026-27")].datetime.max(),
            "espn_latest_source_datetime": espn[espn.requested_source_season.eq(2026)].match_datetime_utc.max(),
            "current_completed_matches_understat": int(completed.season.eq("2026-27").sum())},
    }
    shots_path = folder / "understat" / "shots.csv"
    roster_path = folder / "understat" / "player_match_metrics.csv"
    if shots_path.exists() and roster_path.exists():
        shots = pd.read_csv(shots_path)
        rosters = pd.read_csv(roster_path)
        shot_xg = shots.groupby(["match_id", "team"])["xG"].sum().rename("shot_sum_xG").reset_index()
        roster_xg = rosters.groupby(["match_id", "team"])["xG"].sum().rename("roster_sum_xG").reset_index()
        comparison = metrics.merge(shot_xg, on=["match_id", "team"], how="left").merge(roster_xg, on=["match_id", "team"], how="left")
        # No-shot sides have true xG zero and no shot rows. Missing nonzero sides indicate gaps.
        comparison.loc[comparison.xG.eq(0), "shot_sum_xG"] = comparison.loc[comparison.xG.eq(0), "shot_sum_xG"].fillna(0)
        comparison["shot_minus_displayed_xG"] = comparison.shot_sum_xG - comparison.xG
        comparison["roster_minus_displayed_xG"] = comparison.roster_sum_xG - comparison.xG
        comparison["shot_roster_xg_error"] = (comparison.shot_sum_xG-comparison.roster_sum_xG).abs()
        findings["understat_match_detail_consistency"] = {
            "shots": len(shots), "player_match_rows": len(rosters),
            "expected_focal_team_match_rows": len(metrics),
            "nonzero_xg_team_sides_missing_shots": int(comparison.shot_sum_xG.isna().sum()),
            "team_sides_missing_rosters": int(comparison.roster_sum_xG.isna().sum()),
            "max_additive_shot_vs_player_xg_error": float(comparison.shot_roster_xg_error.max()),
            "additive_shot_vs_player_xg_errors_over_0_0001": int(comparison.shot_roster_xg_error.gt(0.0001).sum()),
            "duplicate_shot_ids": int(shots.duplicated("id").sum()),
            "duplicate_player_match_keys": int(rosters.duplicated(["match_id", "team", "understat_player_id"]).sum()),
            "shot_coordinates_outside_unit_square": int((~shots.X.between(0,1)|~shots.Y.between(0,1)).sum()),
            "shot_xg_outside_unit_interval": int((~shots.xG.between(0,1)).sum()),
            "focal_clubs_outside_whitelist": sorted((set(shots.team)|set(rosters.team))-whitelist),
        }
        findings["understat_distinct_xg_bases"] = {
            "max_additive_shot_minus_displayed_team_xG": float(comparison.shot_minus_displayed_xG.max()),
            "max_additive_player_minus_displayed_team_xG": float(comparison.roster_minus_displayed_xG.max()),
            "team_sides_differing_from_additive_shots_over_0_0001": int(comparison.shot_minus_displayed_xG.abs().gt(0.0001).sum()),
            "team_sides_differing_from_additive_players_over_0_0001": int(comparison.roster_minus_displayed_xG.abs().gt(0.0001).sum()),
            "additive_shot_below_displayed_team_xG_by_over_0_0001": int(comparison.shot_minus_displayed_xG.lt(-0.0001).sum()),
            "interpretation": "Possession/rebound adjustment is inferred from exact primary-source arithmetic for the largest-gap sample. Without official full methodology/possession IDs, all other gaps remain explicit differences between provider outputs. Never force raw shot sums to equal displayed team xG.",
        }
        example_shots = shots[(shots.match_id.eq(28828)) & shots.team.eq("Manchester United") & shots.minute.eq(25)]
        probabilities = example_shots.xG.tolist()
        complement = 1.0
        for probability in probabilities:
            complement *= 1-probability
        raw_sum = sum(probabilities)
        possession_probability = 1-complement
        gap = comparison[(comparison.match_id.eq(28828)) & comparison.team.eq("Manchester United")].iloc[0]
        findings["understat_largest_gap_raw_example"] = {
            "source_match_url": "https://understat.com/match/28828",
            "source_match_json": "https://understat.com/getMatchData/28828",
            "fixture": "Brentford vs Manchester United", "date": "2025-09-27", "player": "Benjamin Sesko",
            "minute": 25, "shot_probabilities": probabilities,
            "shot_probability_sum": raw_sum,
            "probability_of_at_least_one_goal_if_sequence_attempt_probabilities_combined": possession_probability,
            "inferred_rebound_correction": raw_sum-possession_probability,
            "observed_additive_minus_displayed_team_xG": float(gap.shot_minus_displayed_xG),
            "correction_matches_observed_gap_within_source_rounding": bool(abs((raw_sum-possession_probability)-gap.shot_minus_displayed_xG) <0.00001),
            "scope_of_inference": "One exact arithmetic example only; not a claim all2701differences were individually reconciled or an official provider methodology statement.",
        }
    context_path = folder / "understat_context" / "team_context_metrics.csv"
    if context_path.exists():
        contexts = pd.read_csv(context_path)
        findings["understat_context_coverage"] = {
            "rows": len(contexts),
            "club_season_pairs": int(contexts[["team", "season"]].drop_duplicates().shape[0]),
            "current_season_clubs": int(contexts[contexts.season.eq("2026-27")].team.nunique()),
            "categories": sorted(contexts.category.unique().tolist()),
            "duplicate_context_keys": int(contexts.duplicated(["team", "season", "category", "category_value"]).sum()),
            "focal_clubs_outside_whitelist": sorted(set(contexts.team)-whitelist),
            "availability_caution": "Historical final-season aggregates require lagging and are not contemporaneous pre-match features.",
        }
    path = ROOT / "metadata" / "advanced_validation.json"
    path.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
