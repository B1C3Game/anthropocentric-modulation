"""
B1C3 Clock — REST API (Flask)

Endpoints:
  GET /api/clock?timestamp=<ISO8601>&fermentation_start=<YYYY-MM-DD>

Both params are optional:
  - timestamp defaults to UTC now
  - fermentation_start defaults to today (Sealed / day 0)
"""

from datetime import datetime, date, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

from b1c3_clock_engine import get_clock_state

app = Flask(__name__)
CORS(app)  # allow the standalone visual_preview.html (local file) to call this


@app.get("/api/clock")
def clock():
    # --- timestamp ---
    ts_param = request.args.get("timestamp")
    if ts_param:
        try:
            ts = datetime.fromisoformat(ts_param.rstrip("Z")).replace(tzinfo=timezone.utc)
        except ValueError:
            return jsonify({"error": f"Invalid timestamp: '{ts_param}'. Use ISO 8601."}), 400
    else:
        ts = datetime.now(tz=timezone.utc)

    # --- fermentation_start ---
    ferm_param = request.args.get("fermentation_start")
    if ferm_param:
        try:
            ferm_start = date.fromisoformat(ferm_param)
        except ValueError:
            return jsonify({"error": f"Invalid fermentation_start: '{ferm_param}'. Use YYYY-MM-DD."}), 400
    else:
        ferm_start = ts.date()

    state = get_clock_state(ts, ferm_start)
    return jsonify(state)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
