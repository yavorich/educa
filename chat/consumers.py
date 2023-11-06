import json
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # принять соединение
        self.accept()
    
    def disconnect(self, close_code):
        pass
    
    # получить сообщение от WebSocket
    def receive(self, text_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # отправить сообщение в WebSocket
        self.send(text_data=json.dumps({'message': message}))
