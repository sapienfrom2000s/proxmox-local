from locust import HttpUser, task, between
import random


class TodoUser(HttpUser):
    wait_time = between(0.2, 1.5)

    def on_start(self):
        resp = self.client.post("/todos", json={"title": "locust seed"})
        if resp.status_code == 201:
            self.todo_id = resp.json()["id"]

    @task(5)
    def list_todos(self):
        self.client.get("/todos")

    @task(4)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def get_todo(self):
        if hasattr(self, "todo_id"):
            self.client.get(f"/todos/{self.todo_id}")

    @task(2)
    def create_todo(self):
        self.client.post("/todos", json={"title": f"todo {random.randint(1, 10000)}"})

    @task(1)
    def update_todo(self):
        if hasattr(self, "todo_id"):
            self.client.put(
                f"/todos/{self.todo_id}",
                json={
                    "title": f"updated {random.randint(1, 10000)}",
                    "done": random.choice([True, False]),
                },
            )
