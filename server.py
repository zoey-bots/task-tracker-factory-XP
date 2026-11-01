import sys
import json
import sqlite3
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        cl = self.headers.get("Content-Length")
        if cl is None:
            return None
        try:
            length = int(cl)
        except ValueError:
            return None
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    content = f.read().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_response(500)
                self.end_headers()
            return

        if self.path == "/api/tasks":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id, title, done FROM tasks ORDER BY id ASC").fetchall()
            conn.close()
            tasks = []
            for row in rows:
                tasks.append({
                    "id": int(row["id"]),
                    "title": str(row["title"]),
                    "done": bool(row["done"])
                })
            self.send_json(tasks, 200)
            return

        self.send_json({"error":"not found"}, 404)

    def do_POST(self):
        if self.path != "/api/tasks":
            self.send_json({"error":"not found"}, 404)
            return

        data = self.read_json()
        if not isinstance(data, dict):
            self.send_json({"error":"invalid body"}, 422)
            return
        if "title" not in data:
            self.send_json({"error":"missing title"}, 422)
            return
        title = data["title"]
        if type(title) is not str:
            self.send_json({"error":"invalid title type"}, 422)
            return
        title = title.strip()
        if len(title) < 1 or len(title) > 200:
            self.send_json({"error":"title length invalid"}, 422)
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0))
        conn.commit()
        task_id = cur.lastrowid
        conn.close()
        self.send_json({"id": int(task_id), "title": title, "done": False}, 201)

    def do_PATCH(self):
        if not self.path.startswith("/api/tasks/"):
            self.send_json({"error":"not found"}, 404)
            return
        rest = self.path[len("/api/tasks/"):]
        try:
            task_id = int(rest)
        except ValueError:
            self.send_json({"error":"not found"}, 404)
            return

        data = self.read_json()
        if not isinstance(data, dict):
            self.send_json({"error":"invalid body"}, 422)
            return
        if "done" not in data:
            self.send_json({"error":"missing done"}, 422)
            return
        done_val = data["done"]
        if type(done_val) is not bool:
            self.send_json({"error":"invalid done type"}, 422)
            return

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            conn.close()
            self.send_json({"error":"not found"}, 404)
            return

        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (1 if done_val else 0, task_id))
        conn.commit()
        updated = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        self.send_json({
            "id": int(updated["id"]),
            "title": str(updated["title"]),
            "done": bool(updated["done"])
        }, 200)


def main():
    global DB_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    DB_PATH = args.db

    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
    conn.commit()
    conn.close()

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    actual_port = server.server_address[1]
    sys.stdout.write(json.dumps({"host":"127.0.0.1","port":actual_port}) + "\n")
    sys.stdout.flush()

    server.serve_forever()


if __name__ == "__main__":
    main()
