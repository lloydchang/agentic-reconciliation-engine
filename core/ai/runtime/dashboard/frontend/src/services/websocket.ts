import { io, Socket } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:8081';

class WebSocketService {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Function[]> = new Map();

  connect() {
    this.socket = io(WS_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.emit('connect');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.emit('disconnect');
    });

    this.socket.on('agent_status', (data: any) => {
      this.emit('agent_status', data);
    });

    this.socket.on('activity', (data: any) => {
      this.emit('activity', data);
    });

    this.socket.on('metrics', (data: any) => {
      this.emit('metrics', data);
    });

    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, handler: Function) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: Function) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  send(event: string, data: any) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export { WebSocketService };
