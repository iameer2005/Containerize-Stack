"""
Stretch Goal: Demonstrate EXPLAIN ANALYZE before and after adding an index on a seeded table.
Shows query planner optimization: Sequential Scan vs Bitmap Index Scan.
"""
import os
import time
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dev@localhost:5432/tasks"
)

def benchmark_indexing():
    print(f"Connecting to PostgreSQL at {DATABASE_URL}...")
    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 1. Ensure table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    );
                """)

                # 2. Check row count and seed up to 10,000 rows if needed
                cur.execute("SELECT COUNT(*) AS total FROM tasks;")
                count = cur.fetchone()["total"]
                if count < 10000:
                    needed = 10000 - count
                    print(f"Seeding {needed} dummy tasks for measurable EXPLAIN ANALYZE benchmark...")
                    batch = [
                        (f"Seeded benchmark task #{i}", (i % 2 == 0))
                        for i in range(needed)
                    ]
                    cur.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s);", batch)
                    print(f"Table seeded. Total rows: 10,000.")

                # 3. Drop index if exists to test unindexed query plan
                cur.execute("DROP INDEX IF EXISTS idx_tasks_done;")
                print("\n=======================================================")
                print("1. QUERY PLAN BEFORE INDEX (Sequential Scan)")
                print("=======================================================")
                cur.execute("EXPLAIN ANALYZE SELECT * FROM tasks WHERE done = true;")
                before_plan = cur.fetchall()
                for line in before_plan:
                    print(list(line.values())[0])

                # 4. Create Index on 'done' column
                print("\nCreating index: CREATE INDEX idx_tasks_done ON tasks(done);")
                cur.execute("CREATE INDEX idx_tasks_done ON tasks(done);")

                # 5. Run EXPLAIN ANALYZE with index
                print("\n=======================================================")
                print("2. QUERY PLAN AFTER INDEX (Bitmap / Index Scan)")
                print("=======================================================")
                cur.execute("EXPLAIN ANALYZE SELECT * FROM tasks WHERE done = true;")
                after_plan = cur.fetchall()
                for line in after_plan:
                    print(list(line.values())[0])

                print("\nBenchmark completed successfully.")
    except Exception as exc:
        print(f"Could not connect to live PostgreSQL: {exc}")
        print("Note: Run this script while PostgreSQL container is running: python scripts/explain_analyze.py")

if __name__ == "__main__":
    benchmark_indexing()
