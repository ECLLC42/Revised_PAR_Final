import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Successfully connected to Redis")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")