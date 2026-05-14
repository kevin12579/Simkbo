from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.db.game import Game
from app.models.db.team import Team


def get_all_teams(db: Session) -> list[dict]:
    teams = db.query(Team).filter(Team.is_active if hasattr(Team, "is_active") else True).all()
    return [
        {
            "id": t.id,
            "name": t.full_name,
            "short_name": t.short_name,
            "stadium": t.stadium,
            "logo_url": None,
        }
        for t in teams
    ]


def get_team_stats(team_id: int, db: Session, n_games: int = 10) -> dict | None:
    team = db.query(Team).get(team_id)
    if not team:
        return None

    cutoff = date.today() - timedelta(days=120)

    recent_games = (
        db.query(Game)
        .filter(
            Game.status == "COMPLETED",
            Game.scheduled_at >= cutoff,
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id),
        )
        .order_by(Game.scheduled_at.desc())
        .limit(n_games)
        .all()
    )

    wins = losses = home_wins = home_losses = away_wins = away_losses = 0
    total_runs = 0
    streak_type = ""
    streak_count = 0

    for game in recent_games:
        is_home = game.home_team_id == team_id
        team_score = game.home_score if is_home else game.away_score
        opp_score = game.away_score if is_home else game.home_score

        if team_score is None or opp_score is None:
            continue

        won = team_score > opp_score
        total_runs += team_score

        if won:
            wins += 1
            if is_home:
                home_wins += 1
            else:
                away_wins += 1
        else:
            losses += 1
            if is_home:
                home_losses += 1
            else:
                away_losses += 1

    played = wins + losses
    win_rate = round(wins / played, 3) if played > 0 else 0.0
    avg_runs = round(total_runs / played, 2) if played > 0 else 0.0

    # 연승/연패 계산 (최근 게임 기준)
    for game in recent_games:
        is_home = game.home_team_id == team_id
        team_score = game.home_score if is_home else game.away_score
        opp_score = game.away_score if is_home else game.home_score
        if team_score is None or opp_score is None:
            break
        won = team_score > opp_score
        if streak_count == 0:
            streak_type = "W" if won else "L"
            streak_count = 1
        elif (streak_type == "W" and won) or (streak_type == "L" and not won):
            streak_count += 1
        else:
            break

    streak = f"{streak_type}{streak_count}" if streak_count else "-"

    return {
        "team": {
            "id": team.id,
            "name": team.full_name,
            "short_name": team.short_name,
            "stadium": team.stadium,
            "logo_url": None,
        },
        "recent_stats": {
            "last_n_games": played,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_runs_scored": avg_runs,
            "home_record": {"wins": home_wins, "losses": home_losses},
            "away_record": {"wins": away_wins, "losses": away_losses},
            "streak": streak,
        },
        "updated_at": date.today().isoformat(),
    }
