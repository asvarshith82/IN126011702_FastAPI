from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ------------------ MODELS ------------------

class NewRoom(BaseModel):
    type: str
    price_per_night: int = Field(..., gt=0)
    available: bool = True

class BookingRequest(BaseModel):
    user_name: str = Field(..., min_length=2)
    room_id: int
    nights: int = Field(..., gt=0)

# ------------------ DATA ------------------

rooms = [
    {"id": 1, "type": "Single", "price_per_night": 1500, "available": True},
    {"id": 2, "type": "Double", "price_per_night": 2500, "available": True},
    {"id": 3, "type": "Deluxe", "price_per_night": 4000, "available": True},
    {"id": 4, "type": "Suite", "price_per_night": 6000, "available": True},
    {"id": 5, "type": "Single", "price_per_night": 1600, "available": True},
    {"id": 6, "type": "Double", "price_per_night": 2700, "available": True},
    {"id": 7, "type": "Deluxe", "price_per_night": 4200, "available": True},
    {"id": 8, "type": "Suite", "price_per_night": 6500, "available": True},
]

bookings = []
booking_counter = 1

# ------------------ HELPERS ------------------

def find_room(room_id):
    return next((r for r in rooms if r["id"] == room_id), None)

def calculate_total(price, nights):
    return price * nights

# ------------------ HOME ------------------

@app.get("/")
def home():
    return {"message": "Hotel Booking API"}

# ------------------ ROOMS ------------------

@app.get("/rooms")
def get_rooms():
    return {"rooms": rooms, "total": len(rooms)}

@app.post("/rooms")
def add_room(data: NewRoom, response: Response):
    new_id = max(r["id"] for r in rooms) + 1
    room = {"id": new_id, **data.dict()}
    rooms.append(room)
    response.status_code = status.HTTP_201_CREATED
    return {"message": "Room added", "room": room}

# ------------------ SEARCH / SORT / PAGINATION ------------------

@app.get("/rooms/search")
def search_rooms(keyword: str):
    result = [r for r in rooms if keyword.lower() in r["type"].lower()]
    if not result:
        return {"message": "No rooms found"}
    return {"results": result}

@app.get("/rooms/sort")
def sort_rooms(order: str = "asc"):
    result = sorted(rooms, key=lambda x: x["price_per_night"], reverse=(order == "desc"))
    return {"rooms": result}

@app.get("/rooms/page")
def paginate_rooms(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    return {
        "page": page,
        "total_pages": -(-len(rooms) // limit),
        "rooms": rooms[start:start + limit]
    }

@app.get("/rooms/browse")
def browse_rooms(
    keyword: str = Query(None),
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    result = rooms

    if keyword:
        result = [r for r in result if keyword.lower() in r["type"].lower()]

    result = sorted(result, key=lambda x: x["price_per_night"], reverse=(order == "desc"))

    total = len(result)
    start = (page - 1) * limit

    return {
        "total": total,
        "page": page,
        "rooms": result[start:start + limit]
    }

# ------------------ BOOKING WORKFLOW ------------------

@app.post("/book")
def book_room(data: BookingRequest):
    global booking_counter

    room = find_room(data.room_id)

    if not room:
        return {"error": "Room not found"}

    if not room["available"]:
        return {"error": "Room not available"}

    total = calculate_total(room["price_per_night"], data.nights)

    room["available"] = False

    booking = {
        "booking_id": booking_counter,
        "user_name": data.user_name,
        "room_type": room["type"],
        "nights": data.nights,
        "total_price": total
    }

    bookings.append(booking)
    booking_counter += 1

    return {"message": "Room booked successfully", "booking": booking}

@app.get("/bookings")
def get_bookings():
    return {"bookings": bookings, "total": len(bookings)}

@app.post("/checkout/{room_id}")
def checkout(room_id: int):
    room = find_room(room_id)

    if not room:
        return {"error": "Room not found"}

    room["available"] = True

    return {"message": "Room checkout successful"}

# ------------------ ANALYTICS ------------------

@app.get("/analytics")
def analytics():
    total_bookings = len(bookings)
    total_revenue = sum(b["total_price"] for b in bookings)

    return {
        "total_bookings": total_bookings,
        "total_revenue": total_revenue
    }

# ------------------ SINGLE ROOM (KEEP LAST) ------------------

@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    room = find_room(room_id)
    if not room:
        return {"error": "Room not found"}
    return room