from app import create_app
from app.redis import init_redis

app = create_app()
init_redis(app)

if __name__ == "__main__":
    app.run(debug=True)
