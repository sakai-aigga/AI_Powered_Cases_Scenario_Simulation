import sys
from app import create_app
from app.models import db, User

app = create_app()


@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        print("PostgreSQL tables created successfully.")


if __name__ == "__main__":
    if "--init-db" in sys.argv:
        with app.app_context():
            db.create_all()
            print("PostgreSQL tables created successfully.")
    else:
        app.run(debug=True, port=5000)
