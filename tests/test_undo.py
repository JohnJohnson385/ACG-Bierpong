"""Regression tests for bounded undo history (no Firebase required)."""
import ast
import copy
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "logik_spiel.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Assign)) and (
    isinstance(n, ast.FunctionDef) and n.name in {"save_step", "restore_step"} or
    isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MAX_UNDO_STEPS" for t in n.targets)
)]
module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
namespace = {"copy": copy}
exec(compile(module, str(SOURCE), "exec"), namespace)


class Session(dict):
    def __getattr__(self, name):
        return self[name]


class FakeStreamlit:
    session_state = Session()


namespace["st"] = FakeStreamlit()


class UndoTests(unittest.TestCase):
    def setUp(self):
        self.live = {"t1_cups": 10, "action_log": [], "history": [], "stats": {"hits": 0}}
        FakeStreamlit.session_state.live = self.live

    def test_undo_restores_state_and_log(self):
        namespace["save_step"]()
        self.live["t1_cups"] = 9
        self.live["stats"]["hits"] = 1
        self.live["action_log"].append("Hit")
        self.assertTrue(namespace["restore_step"](self.live))
        self.assertEqual(self.live["t1_cups"], 10)
        self.assertEqual(self.live["stats"]["hits"], 0)
        self.assertEqual(self.live["action_log"], [])

    def test_history_is_bounded(self):
        for i in range(250):
            namespace["save_step"]()
            self.live["t1_cups"] = i
            self.live["action_log"].append(str(i))
        self.assertEqual(len(self.live["history"]), namespace["MAX_UNDO_STEPS"])
        self.assertTrue(all("action_log" not in item for item in self.live["history"]))

    def test_old_snapshot_is_supported(self):
        self.live["history"].append({"t1_cups": 8, "action_log": ["old"]})
        self.assertTrue(namespace["restore_step"](self.live))
        self.assertEqual(self.live["t1_cups"], 8)
        self.assertEqual(self.live["action_log"], ["old"])

    def test_no_history(self):
        self.assertFalse(namespace["restore_step"](self.live))


if __name__ == "__main__":
    unittest.main()
