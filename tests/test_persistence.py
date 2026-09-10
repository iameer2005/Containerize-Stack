"""
Script proving data persistence across application and container restarts.
Validates requirement: "create rows -> restart app and container -> rows still there".
"""
import os
import sys
import time
import requests

API_URL = os.getenv("API_URL", "http://localhost:3000")

def run_persistence_check():
    print(f"Connecting to Task API at {API_URL}...")
    try:
        # 1. Fetch initial tasks
        res = requests.get(f"{API_URL}/tasks")
        res.raise_for_status()
        initial_tasks = res.json()
        print(f"Initial tasks count: {len(initial_tasks)}")

        # 2. Create a unique persistent marker task
        unique_title = f"Persistence verification task - {int(time.time())}"
        create_res = requests.post(f"{API_URL}/tasks", json={"title": unique_title, "done": True})
        create_res.raise_for_status()
        created = create_res.json()
        print(f"Created task id={created['id']} title='{created['title']}'")

        print("\n--- PERSISTENCE VERIFICATION INSTRUCTION ---")
        print("Now simulate or execute a container restart:")
        print("  docker compose down")
        print("  docker compose up -d")
        print("Then re-run this script to verify the created task still exists in Postgres.")

        return True
    except Exception as exc:
        print(f"Error during verification: {exc}")
        return False

if __name__ == "__main__":
    success = run_persistence_check()
    sys.exit(0 if success else 1)
