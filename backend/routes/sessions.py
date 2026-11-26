import hashlib
import secrets
import string
from flask import Blueprint, jsonify, request

from database.db import get_conn

sessions_pb = Blueprint("sessions", __name__)

SESSION_CODE_LEN = 8
SESSION_CODE_CHARS = string.ascii_uppercase + string.digits


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    return "".join(secrets.choice(SESSION_CODE_CHARS) for _ in range(SESSION_CODE_LEN))


def _unique_code(conn) -> str:
    for _ in range(10):
        code = _generate_code()
        existing = conn.execute("SELECT id FROM sessions WHERE code = ?", (code,)).fetchone()
        if not existing:
            return code
    raise RuntimeError("No se pudo generar un código de sesión único")


@sessions_pb.post("")
def create_session():
    """Crear una sesión.
    Body JSON opcional: { host: bool, name: str, code: str }
    Sin host: registra al jugador creador y devuelve su player_token.
    Con host: devuelve el host_token.
    """
    data = request.get_json(silent=True) or {}
    with_host = bool(data.get("host", False))
    session_name = data.get("name")
    code = data.get("code") or _unique_code(get_conn())

    conn = get_conn()
    try:
        if code != _unique_code(conn):
            # Si se pidió código explícito, verificar que no exista
            existing = conn.execute("SELECT id FROM sessions WHERE code = ?", (code,)).fetchone()
            if existing:
                return jsonify({"error": "El código de sesión ya existe"}), 409

        host_token_raw = None
        host_token_hash = None
        if with_host:
            host_token_raw = secrets.token_urlsafe(32)
            host_token_hash = _hash_token(host_token_raw)

        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO sessions (code, host_token, status) VALUES (?, ?, 'open')",
            (code, host_token_hash),
        )
        session_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        player_token_raw = None
        if not with_host:
            creator_name = session_name or "Creador"
            player_token_raw = secrets.token_urlsafe(32)
            player_token_hash = _hash_token(player_token_raw)
            conn.execute(
                "INSERT INTO players (session_id, name, player_token, is_creator) VALUES (?, ?, ?, 1)",
                (session_id, creator_name, player_token_hash),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    response = {"session_code": code, "status": "open"}
    if with_host:
        response["host_token"] = host_token_raw
    else:
        response["player_token"] = player_token_raw
        response["player_name"] = creator_name
    return jsonify(response), 201


@sessions_pb.post("/<code>/join")
def join_session(code):
    """Unirse a una sesión en estado open. Registra al jugador y devuelve su player_token."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "Se requiere el nombre del jugador"}), 400

    conn = get_conn()
    try:
        session = conn.execute("SELECT id, status FROM sessions WHERE code = ?", (code,)).fetchone()
        if not session:
            return jsonify({"error": "Sesión no encontrada"}), 404
        if session["status"] != "open":
            return jsonify({"error": "La sesión no admite jugadores nuevos"}), 409

        existing = conn.execute(
            "SELECT id FROM players WHERE session_id = ? AND name = ?", (session["id"], name)
        ).fetchone()
        if existing:
            return jsonify({"error": "El nombre ya está en uso en esta sesión"}), 409

        player_token_raw = secrets.token_urlsafe(32)
        player_token_hash = _hash_token(player_token_raw)

        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO players (session_id, name, player_token, is_creator) VALUES (?, ?, ?, 0)",
            (session["id"], name, player_token_hash),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({"session_code": code, "player_name": name, "player_token": player_token_raw}), 201


@sessions_pb.get("/<code>/players")
def list_players(code):
    """Listar los jugadores de una sesión."""
    conn = get_conn()
    try:
        session = conn.execute("SELECT id, status FROM sessions WHERE code = ?", (code,)).fetchone()
        if not session:
            return jsonify({"error": "Sesión no encontrada"}), 404

        players = conn.execute(
            "SELECT name, is_creator, created_at FROM players WHERE session_id = ? ORDER BY is_creator DESC, created_at ASC",
            (session["id"],),
        ).fetchall()

        return jsonify({
            "session_code": code,
            "players": [
                {
                    "name": p["name"],
                    "is_creator": bool(p["is_creator"]),
                    "joined_at": p["created_at"],
                }
                for p in players
            ],
        })
    finally:
        conn.close()


@sessions_pb.post("/<code>/start")
def start_session(code):
    """Pasar sesión de open a active. Autorización del host o del creador (si no hay host)."""
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "Se requiere token"}), 401

    conn = get_conn()
    try:
        session = conn.execute("SELECT id, host_token, status FROM sessions WHERE code = ?", (code,)).fetchone()
        if not session:
            return jsonify({"error": "Sesión no encontrada"}), 404
        if session["status"] != "open":
            return jsonify({"error": "La sesión no está en estado open"}), 409

        host_token_hash = session["host_token"]
        authorized = False
        if host_token_hash and _hash_token(token) == host_token_hash:
            authorized = True
        elif not host_token_hash:
            creator = conn.execute(
                "SELECT player_token FROM players WHERE session_id = ? AND is_creator = 1",
                (session["id"],),
            ).fetchone()
            if creator and _hash_token(token) == creator["player_token"]:
                authorized = True

        if not authorized:
            return jsonify({"error": "No autorizado para iniciar la sesión"}), 403

        conn.execute("BEGIN")
        conn.execute("UPDATE sessions SET status = 'active' WHERE id = ?", (session["id"],))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({"session_code": code, "status": "active"})


@sessions_pb.post("/reconnect")
def reconnect():
    """Reconectar validando player_token o host_token."""
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "Se requiere token"}), 401

    token_hash = _hash_token(token)
    conn = get_conn()
    try:
        player = conn.execute(
            """
            SELECT p.id, p.name, p.is_creator, s.code, s.status
            FROM players p
            JOIN sessions s ON s.id = p.session_id
            WHERE p.player_token = ?
            """,
            (token_hash,),
        ).fetchone()

        if player:
            if player["status"] == "closed":
                return jsonify({"error": "La sesión está cerrada"}), 409
            return jsonify({
                "type": "player",
                "session_code": player["code"],
                "player_name": player["name"],
                "is_creator": bool(player["is_creator"]),
                "status": player["status"],
            })

        session = conn.execute(
            "SELECT code, status FROM sessions WHERE host_token = ?",
            (token_hash,),
        ).fetchone()
        if session:
            if session["status"] == "closed":
                return jsonify({"error": "La sesión está cerrada"}), 409
            return jsonify({
                "type": "host",
                "session_code": session["code"],
                "status": session["status"],
            })

        return jsonify({"error": "Token no válido"}), 401
    finally:
        conn.close()


@sessions_pb.get("")
def list_sessions():
    """Consultar sesiones disponibles (open) o activas."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT code, status, created_at FROM sessions WHERE status IN ('open', 'active') ORDER BY created_at DESC"
        ).fetchall()
        return jsonify([{"session_code": r["code"], "status": r["status"], "created_at": r["created_at"]} for r in rows])
    finally:
        conn.close()


@sessions_pb.post("/<code>/close")
def close_session(code):
    """Cerrar sesión active, guardar resultados en session_records y marcar closed."""
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "Se requiere token"}), 401

    conn = get_conn()
    try:
        session = conn.execute("SELECT id, host_token, status FROM sessions WHERE code = ?", (code,)).fetchone()
        if not session:
            return jsonify({"error": "Sesión no encontrada"}), 404
        if session["status"] != "active":
            return jsonify({"error": "La sesión no está activa"}), 409

        host_token_hash = session["host_token"]
        authorized = False
        if host_token_hash and _hash_token(token) == host_token_hash:
            authorized = True
        elif not host_token_hash:
            creator = conn.execute(
                "SELECT player_token FROM players WHERE session_id = ? AND is_creator = 1",
                (session["id"],),
            ).fetchone()
            if creator and _hash_token(token) == creator["player_token"]:
                authorized = True

        if not authorized:
            return jsonify({"error": "No autorizado para cerrar la sesión"}), 403

        players = conn.execute(
            "SELECT name FROM players WHERE session_id = ? ORDER BY name",
            (session["id"],),
        ).fetchall()

        conn.execute("BEGIN")
        conn.execute("UPDATE sessions SET status = 'closed', closed_at = datetime('now') WHERE id = ?", (session["id"],))
        for rank, p in enumerate(players, start=1):
            conn.execute(
                "INSERT INTO session_records (session_code, player_name, final_cash, rank) VALUES (?, ?, 0, ?)",
                (code, p["name"], rank),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify({"session_code": code, "status": "closed", "records": [p["name"] for p in players]})
