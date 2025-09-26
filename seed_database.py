
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

import database

def seed():
    print("Seeding database...")
    # Make sure the database is initialized
    database.initialize_database()

    # Create a default admin user
    username = "admin"
    password = "password"
    
    # Check if admin already exists to avoid duplicates
    if not database.get_admin(username):
        database.create_admin(username, password)
        print(f"Admin user '{username}' created with password '{password}'.")
    else:
        print(f"Admin user '{username}' already exists.")

if __name__ == "__main__":
    seed()
