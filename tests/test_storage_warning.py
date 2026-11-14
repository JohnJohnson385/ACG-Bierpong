"""Regression tests for Firestore document-size warnings."""
import ast
import pathlib
import unittest


SOURCE = pathlib.Path(__file__).resolve().parents[1] / "datenbank.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
selected = [node for node in tree.body if (
    isinstance(node, ast.FunctionDef) and node.name in {
        "_string_size", "_value_size", "estimate_firestore_document_size", "get_storage_level"
    }
    or isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id in {
            "FIRESTORE_DOCUMENT_LIMIT_BYTES", "STORAGE_WARNING_RATIO", "STORAGE_CRITICAL_RATIO"
        }
        for target in node.targets
    )
)]
namespace = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), str(SOURCE), "exec"), namespace)


class StorageWarningTests(unittest.TestCase):
    def test_small_document_is_normal(self):
        size = namespace["estimate_firestore_document_size"]({"name": "Turnier", "matches": []})
        self.assertEqual(namespace["get_storage_level"](size), "normal")

    def test_warning_starts_at_60_percent(self):
        limit = namespace["FIRESTORE_DOCUMENT_LIMIT_BYTES"]
        self.assertEqual(namespace["get_storage_level"](int(limit * 0.60)), "warning")

    def test_critical_starts_at_85_percent(self):
        limit = namespace["FIRESTORE_DOCUMENT_LIMIT_BYTES"]
        self.assertEqual(namespace["get_storage_level"](int(limit * 0.85)), "critical")

    def test_long_logs_trigger_warning(self):
        data = {"matches": [{"action_log": ["x" * 1000] * 700}]}
        size = namespace["estimate_firestore_document_size"](data)
        self.assertEqual(namespace["get_storage_level"](size), "warning")


if __name__ == "__main__":
    unittest.main()
