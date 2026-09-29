from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        print("--- Create a New Officer/Admin ---")
        username = input("Enter new username: ")
        password = input("Enter new password: ")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"Error: User '{username}' already exists!")
            return
            
        # Hash the password for security
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Add to database
        new_admin = User(username=username, password=hashed_password, role='officer')
        db.session.add(new_admin)
        db.session.commit()
        
        print(f"Success! Officer '{username}' has been added to the database.")

if __name__ == '__main__':
    create_admin()
