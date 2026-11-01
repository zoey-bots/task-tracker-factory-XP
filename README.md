# Task Tracker

Loopback SQLite-backed task tracker using Python stdlib and vanilla browser JavaScript.

## Start

python server.py --port 0 --db tasks.db

The server binds to 127.0.0.1, prints a JSON line with host and port, and serves the UI at `/`.

## Usage

- Open `http://127.0.0.1:<port>/` in a browser.
- Add tasks with the textbox labeled exactly "Task title", the button "Add task", and mark complete with checkbox labeled exactly "Complete <exact task title>".
- Data persists in SQLite across reload and restart.
- API endpoints: `GET /api/tasks`, `POST /api/tasks`, `PATCH /api/tasks/<id>`. All responses are valid JSON, including 404 and 422 errors.
