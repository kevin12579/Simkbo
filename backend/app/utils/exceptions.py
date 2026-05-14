from fastapi import HTTPException


class GameNotFoundException(HTTPException):
    def __init__(self, game_id: int):
        super().__init__(
            status_code=404,
            detail={"code": "GAME_NOT_FOUND", "message": f"경기(id={game_id})를 찾을 수 없습니다.", "status": 404},
        )


class TeamNotFoundException(HTTPException):
    def __init__(self, team_id: int):
        super().__init__(
            status_code=404,
            detail={"code": "TEAM_NOT_FOUND", "message": f"팀(id={team_id})을 찾을 수 없습니다.", "status": 404},
        )


class PlayerNotFoundException(HTTPException):
    def __init__(self, player_id: int):
        super().__init__(
            status_code=404,
            detail={"code": "PLAYER_NOT_FOUND", "message": f"선수(id={player_id})를 찾을 수 없습니다.", "status": 404},
        )
