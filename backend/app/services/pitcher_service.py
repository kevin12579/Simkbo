from sqlalchemy.orm import Session

from app.models.db.pitcher_game_stats import PitcherGameStats
from app.models.db.player import Player


def get_pitcher_stats(player_id: int, db: Session, n_games: int = 5) -> dict | None:
    player = db.query(Player).get(player_id)
    if not player:
        return None

    stats = (
        db.query(PitcherGameStats)
        .filter(PitcherGameStats.player_id == player_id, PitcherGameStats.is_starter == True)
        .order_by(PitcherGameStats.game_id.desc())
        .limit(n_games)
        .all()
    )

    records = [
        {
            "game_id": s.game_id,
            "innings_pitched": float(s.innings_pitched) if s.innings_pitched else None,
            "earned_runs": s.earned_runs,
            "strikeouts": s.strikeouts,
            "walks": s.walks,
            "hits_allowed": s.hits_allowed,
            "era": float(s.era) if s.era else None,
            "whip": float(s.whip) if s.whip else None,
        }
        for s in stats
    ]

    return {
        "player_id": player.id,
        "name": player.name,
        "team_name": player.team.full_name if player.team else "",
        "recent_games": records,
    }
