from app import app
from socketio_instance import socketio

if __name__ == "__main__":
    socketio.run(app)