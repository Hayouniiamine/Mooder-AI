from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'  # ✅ Explicitly set table name (PostgreSQL is case-sensitive)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)  # ✅ Increased size for usernames
    email = db.Column(db.String(255), unique=True, nullable=False)  # ✅ Increased size for email
    password = db.Column(db.String(255), nullable=False)  # ✅ Ensure password hashes fit

    def __repr__(self):
        return f"<User {self.username}>"
