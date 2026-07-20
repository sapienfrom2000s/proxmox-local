from dataclasses import asdict
from flask import Blueprint, request, jsonify, abort
from app.redis import get_redis
from app.todo import Todo

api = Blueprint("api", __name__)


@api.route("/health")
def health():
    return {"status": "ok"}


@api.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json()
    if not data or "title" not in data:
        abort(400, description="title is required")
    todo = Todo(title=data["title"])
    get_redis().set(todo.redis_key, todo.to_json())
    return jsonify(asdict(todo)), 201


@api.route("/todos", methods=["GET"])
def list_todos():
    redis = get_redis()
    keys = redis.keys("todo:*")
    todos = [Todo.from_json(redis.get(k)) for k in keys]
    return jsonify([asdict(t) for t in todos])


@api.route("/todos/<id>", methods=["GET"])
def get_todo(id):
    data = get_redis().get(f"todo:{id}")
    if not data:
        abort(404)
    return jsonify(asdict(Todo.from_json(data)))


@api.route("/todos/<id>", methods=["PUT"])
def update_todo(id):
    redis = get_redis()
    key = f"todo:{id}"
    if not redis.get(key):
        abort(404)
    data = request.get_json()
    if not data or "title" not in data:
        abort(400, description="title is required")
    todo = Todo(id=id, title=data["title"], done=data.get("done", False))
    redis.set(key, todo.to_json())
    return jsonify(asdict(todo))


@api.route("/todos/<id>", methods=["DELETE"])
def delete_todo(id):
    redis = get_redis()
    key = f"todo:{id}"
    if not redis.delete(key):
        abort(404)
    return "", 204
