import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from personal_finance.api.main import create_app


class FrontendServingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dist = Path(self._tmp.name) / "browser"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<app-root>index</app-root>")
        (self.dist / "main.js").write_text("console.log('main')")
        (Path(self._tmp.name) / "secret.txt").write_text("outside")
        self.client = TestClient(create_app(frontend_dir=self.dist))

    def tearDown(self):
        self._tmp.cleanup()

    def test_index(self):
        self.assertIn("index", self.client.get("/").text)

    def test_static_file(self):
        self.assertIn("main", self.client.get("/main.js").text)

    def test_deep_link_falls_back_to_index(self):
        response = self.client.get("/accounts")
        self.assertEqual(response.status_code, 200)
        self.assertIn("index", response.text)

    def test_unknown_api_path_is_not_swallowed(self):
        self.assertEqual(self.client.get("/api/nope").status_code, 404)

    def test_path_traversal_serves_index(self):
        response = self.client.get("/..%2Fsecret.txt")
        self.assertNotIn("outside", response.text)

    def test_missing_build_shows_instructions(self):
        client = TestClient(create_app(frontend_dir=Path(self._tmp.name) / "missing"))
        self.assertIn("npm run build", client.get("/").text)


if __name__ == "__main__":
    unittest.main()
