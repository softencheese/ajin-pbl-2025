import socketio

from app.core.logging import get_logger

logger = get_logger(__name__)

# 비동기 Socket.IO 서버 생성
# cors_allowed_origins='*'는 개발용입니다. 프로덕션에서는 구체적인 도메인을 지정하세요.
sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# ASGI 앱 생성 (FastAPI에 마운트할 객체)
sio_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path=''
)

@sio_server.event
async def connect(sid, environ, auth):
    logger.info(f"Client connected: {sid}")
    await sio_server.emit('message', {'data': 'Connected'}, room=sid)

@sio_server.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
