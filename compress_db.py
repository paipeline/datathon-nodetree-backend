import sqlite3

# Path to your Chroma database
db_path = "chroma/chroma.sqlite3"  # Update if your path is different

# Connect to the SQLite database
conn = sqlite3.connect(db_path)

# Run the VACUUM command to compress the database
conn.execute("VACUUM;")

# Close the connection
conn.close()

print(f"Compressed {db_path} successfully!")
