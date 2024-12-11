import sqlite3
import random
import time

# Path to the SQLite database
db_path = "roads.db"

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the car table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    road_id INTEGER,
    target_intersection_id INTEGER,
    x REAL,
    y REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS update_cars_timestamp
AFTER UPDATE ON cars
FOR EACH ROW
BEGIN
    UPDATE cars SET timestamp = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
""")
conn.commit()

# Add one car to the database
def add_car(road_id, target_intersection_id, x, y):
    cursor.execute("INSERT INTO cars (road_id, target_intersection_id, x, y) VALUES (?, ?, ?, ?)",
                   (road_id, target_intersection_id, x, y))
    conn.commit()
    return cursor.lastrowid

def get_random_road_coordinates_and_target():
    # Fetch a random road
    cursor.execute("SELECT id, intersection_id1, intersection_id2 FROM roads")
    roads = cursor.fetchall()
    if not roads:
        return None, None, None, None  # No roads available in the database
    
    # Pick a random road
    road = random.choice(roads)
    road_id, intersection_id1, intersection_id2 = road
    
    # Randomly select one intersection as the source
    source_intersection = intersection_id1 if random.choice([True, False]) else intersection_id2
    target_intersection = intersection_id2 if source_intersection == intersection_id1 else intersection_id1
    
    # Get coordinates of the source intersection
    cursor.execute("SELECT x, y FROM intersections WHERE id = ?", (source_intersection,))
    coordinates = cursor.fetchone()
    
    if coordinates:
        x, y = coordinates
        return road_id,x, y, target_intersection
    else:
        return None,None, None, None

# Get coordinates of an intersection
def get_intersection_coordinates(intersection_id):
    cursor.execute("SELECT x, y FROM intersections WHERE id = ?", (intersection_id,))
    return cursor.fetchone()
def load_roads_to_dict():
    # Execute the query to fetch road data
    cursor.execute("SELECT id, intersection_id1, intersection_id2 FROM roads")
    roads = cursor.fetchall()

    # Store roads in a dictionary by road_id
    roads_dict = {
        road_id: {
            "intersection_id1": intersection_id1,
            "intersection_id2": intersection_id2
        }
        for road_id, intersection_id1, intersection_id2 in roads
    }

    return roads_dict
roadsd=load_roads_to_dict()

# Select a new road and target intersection
def get_new_road_and_target_intersection(current_intersection_id):
    cursor.execute("SELECT id, intersection_id1, intersection_id2 FROM roads WHERE intersection_id1 = ? OR intersection_id2 = ?",
                   (current_intersection_id, current_intersection_id))
    possible_roads = cursor.fetchall()
    if not possible_roads:
        return None, None
    selected_road = random.choice(possible_roads)
    new_target = selected_road[1] if selected_road[2] == current_intersection_id else selected_road[2]
    return selected_road[0], new_target

import requests

def update_car_position(car_id, speed, dt):
    # Fetch recently updated cars from the HTTP endpoint
    response = requests.get("http://127.0.0.1:9999/cars/updated_recently")
    if response.status_code != 200:
        print("Failed to fetch recently updated cars.")
        return

    # Parse the JSON response
    recently_updated_cars = response.json()

    # Find the car's data in the fetched list
    car = next((c for c in recently_updated_cars if c["id"] == car_id), None)
    if not car:
        print(f"Car {car_id} not eligible for update.")
        return

    road_id, target_intersection_id, x, y = (
        car["road_id"],
        car["target_intersection_id"],
        car["x"],
        car["y"],
    )
    target_coords = get_intersection_coordinates(target_intersection_id)
    if not target_coords:
        print(f"Target coordinates for intersection {target_intersection_id} not found.")
        return

    target_x, target_y = target_coords
    dx, dy = target_x - x, target_y - y
    distance_to_target = (dx ** 2 + dy ** 2) ** 0.5
    step_distance = speed * dt

    # Check if another car is too close
    # ~ for other_car in recently_updated_cars:
        # ~ if other_car["id"] == car_id:
            # ~ continue
        # ~ other_x, other_y = other_car["x"], other_car["y"]
        # ~ if ((x + dx / distance_to_target * step_distance - other_x) ** 2 +
            # ~ (y + dy / distance_to_target * step_distance - other_y) ** 2) ** 0.5 < 6:
            # ~ for intid in roadsd[target_intersection_id]:
                # ~ if intid!=target_intersection_id:
                    # ~ target_intersection_id=intid
                    # ~ break
            # ~ x-=dx / distance_to_target * step_distance
            # ~ y-=dy / distance_to_target * step_distance
            # ~ print(f"Car {car_id} is too close to another car; not moving.")
            # ~ # Always update the database with the current position
            # ~ cursor.execute("""
                # ~ UPDATE cars 
                # ~ SET road_id = ?, target_intersection_id = ?, x = ?, y = ? 
                # ~ WHERE id = ?
            # ~ """, (road_id, target_intersection_id, x, y, car_id))
            # ~ conn.commit()
            # ~ return

    # Check if another car is on the same road with the same target intersection
    

    if step_distance >= distance_to_target:
        # Reached the intersection
        x, y = target_x, target_y
        rid, tid = get_new_road_and_target_intersection(target_intersection_id)
        good=True
        for car in recently_updated_cars:
            if rid==car["road_id"] and car["target_intersection_id"]==target_intersection_id:
                good=False
                break
            
        if not good:
            print(f"Car {car_id} has no available roads to continue.")
            return
        road_id, target_intersection_id = rid,tid
    else:
        # Move towards the target
        x += dx / distance_to_target * step_distance
        y += dy / distance_to_target * step_distance

    # Always update the database with the current position
    cursor.execute("""
        UPDATE cars 
        SET road_id = ?, target_intersection_id = ?, x = ?, y = ? 
        WHERE id = ?
    """, (road_id, target_intersection_id, x, y, car_id))
    conn.commit()
    print(f"Car {car_id} updated to position ({x}, {y}), targeting intersection {target_intersection_id}.")

# Initialize one car and run the update loop
try:

    road_id,initial_x,initial_y,target_intersection_id = get_random_road_coordinates_and_target()


    if initial_x is None or initial_y is None:
        raise ValueError("Intersection 0 does not exist in the database.")

    car_id = add_car(road_id, target_intersection_id, initial_x, initial_y)

    speed = 50  # units per second
    dt = 1/6# 1/30 second updates

    print("Starting simulation for car with ID:", car_id)
    while True:
        update_car_position(car_id, speed, dt)
        time.sleep(dt)

except KeyboardInterrupt:
    print("Simulation stopped.")
finally:
    conn.close()
    print("Database connection closed.")
