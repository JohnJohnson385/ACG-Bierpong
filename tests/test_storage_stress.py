"""Offline storage stress simulation: 15 long games, no Firestore access."""
import ast
import copy
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / "logik_spiel.py").read_text(encoding="utf-8"))
nodes = [n for n in tree.body if (
    isinstance(n, ast.FunctionDef) and n.name == "save_step"
    or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MAX_UNDO_STEPS" for t in n.targets)
)]
ns = {"copy": copy}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), "logik_spiel.py", "exec"), ns)


class State(dict):
    def __getattr__(self, name):
        return self[name]


class StreamlitStub:
    session_state = State()


ns["st"] = StreamlitStub()


class StorageStressTests(unittest.TestCase):
    def test_15_long_games_fit_in_firestore_document(self):
        # Representative storage-shape simulation, not an end-to-end UI test.
        matches = []
        for game in range(15):
            live = {
                "match_id": game, "t1_cups": 10, "t2_cups": 10,
                "game_state": "playing", "history": [], "action_log": [],
                "stats": {"turns_t1": 0, "turns_t2": 0},
                "bombs_events": [], "clutch_nachwurf_events": []
            }
            StreamlitStub.session_state.live = live
            for turn in range(250):
                ns["save_step"]()
                live["stats"]["turns_t1"] += 1
                live["action_log"].append(f"Game {game + 1}, turn {turn + 1}: a missed throw and possession change")
            self.assertLessEqual(len(live["history"]), 30)
            match = {
                "id": game, "t1_score": 0, "t2_score": 1,
                "winner_team": 2, "stats": copy.deepcopy(live["stats"]),
                "action_log": copy.deepcopy(live["action_log"]),
                "live_backup": copy.deepcopy({k: v for k, v in live.items() if k != "history"})
            }
            self.assertNotIn("history", match["live_backup"])
            matches.append(match)

        document = {"t_name": "Test", "t_date": "2026-11-13", "players": list("ABCDE"), "matches": matches, "live": None}
        payload_size = len(json.dumps(document, ensure_ascii=False).encode("utf-8"))
        self.assertLess(payload_size, 1_048_576, f"Representative 15-game payload: {payload_size} bytes")


if __name__ == "__main__":
    unittest.main()
