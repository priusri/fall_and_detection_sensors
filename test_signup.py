from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    print("Checking database connection...")
    try:
        db.create_all() # Ensure tables exist
        print("Tables checked/created.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        exit(1)

    print("Attempting to create user 'test_user'...")
    existing = User.query.filter_by(username='test_user').first()
    if existing:
        print("User 'test_user' already exists. Deleting...")
        db.session.delete(existing)
        db.session.commit()
    
    try:
        user = User(username='test_user', password_hash='hashed_secret')
        db.session.add(user)
        db.session.commit()
        print("SUCCESS: User 'test_user' created successfully.")
    except Exception as e:
        print(f"FAILURE: Could not create user. Error: {e}")
