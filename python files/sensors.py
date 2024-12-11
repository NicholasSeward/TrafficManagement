from flask import Flask, jsonify
import sqlite3
from datetime import datetime, timedelta,timezone

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('roads.db')  # Replace with your actual database name
    conn.row_factory = sqlite3.Row  # Enables accessing columns by name
    return conn

@app.route('/cars/updated_recently', methods=['GET'])
def get_recently_updated_cars():
    try:
        # Calculate the time one second ago
        one_second_ago = datetime.now(timezone.utc) - timedelta(seconds=1)

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Execute the query to fetch cars updated within the last second
        query = """
        SELECT * FROM cars WHERE timestamp >= ?
        """
        cur.execute(query, (one_second_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        rows = cur.fetchall()
        conn.close()

        # Convert rows to a list of dictionaries
        cars = [dict(row) for row in rows]

        return jsonify(cars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=9999)
