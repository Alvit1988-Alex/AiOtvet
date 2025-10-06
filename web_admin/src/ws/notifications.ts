import { io, Socket } from 'socket.io-client';

export function createSocket(token: string | null): Socket {
  const socket = io('/ws/notifications', {
    auth: { token },
  });
  return socket;
}
