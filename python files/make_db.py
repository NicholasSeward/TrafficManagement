import sqlite3
from itertools import combinations
import math

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay

# Function to generate points with a minimum distance constraint
def generate_points_with_min_distance(size, num_points, min_distance):
    points = []
    while len(points) < num_points:
        candidate = np.random.uniform(-size, size, 2)
        if all(np.linalg.norm(candidate - np.array(p)) >= min_distance for p in points):
            points.append(candidate)
    return np.array(points)

# Parameters
size = 100
num_points = 40
min_distance = 5  # Minimum distance between points

# Generate points
points = generate_points_with_min_distance(size, num_points, min_distance)

# Perform triangulation
tri = Delaunay(points)

# Remove long edges on the outer boundary by filtering based on edge length
threshold = size * 0.75  # Adjust threshold to limit long edges
edges = set()
for simplex in tri.simplices:
    for i in range(3):
        op1 = points[simplex[i]]
        op2 = points[simplex[(i + 1) % 3]]
        p1=tuple(op1)
        p2=tuple(op2)
        if p2<p1:
            p1,p2=p2,p1
        if np.linalg.norm(op1 - op2) < threshold:
            edges.add((p1, p2))

# Create SQLite database
db_path = "roads.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables with auto-incrementing IDs
cursor.execute("""
CREATE TABLE IF NOT EXISTS intersections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    x REAL,
    y REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS roads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intersection_id1 INTEGER,
    intersection_id2 INTEGER,
    FOREIGN KEY (intersection_id1) REFERENCES intersections (id),
    FOREIGN KEY (intersection_id2) REFERENCES intersections (id)
)
""")

# Insert intersections into the database
for x, y in points:
    cursor.execute("INSERT INTO intersections (x, y) VALUES (?, ?)", (x, y))

# Retrieve intersections with their IDs
intersections = cursor.execute("SELECT id, x, y FROM intersections").fetchall()

# Map points to intersection IDs
point_to_id = {tuple(inter[1:]): inter[0] for inter in intersections}
print(point_to_id)
# Insert roads into the database based on edges
for p1, p2 in edges:
    id1 = point_to_id[tuple(p1)]
    id2 = point_to_id[tuple(p2)]
    cursor.execute("INSERT INTO roads (intersection_id1, intersection_id2) VALUES (?, ?)", (id1, id2))

# Commit changes and close connection
conn.commit()
conn.close()
