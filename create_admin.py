
import argparse
import getpass
import database
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Create a new admin user.")
    parser.add_argument("username", help="The username for the new admin.")
    args = parser.parse_args()

    password = getpass.getpass(f"Enter password for {args.username}: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Passwords do not match.")
        return

    # The new database.py handles password hashing
    admin = database.create_admin(args.username, password)

    if admin:
        print(f"Admin user '{args.username}' created successfully.")
    else:
        print(f"Admin user '{args.username}' already exists.")

if __name__ == "__main__":
    # Ensure the database is initialized
    # The load_dotenv() call above ensures credentials are set
    database.initialize_database()
    main()
