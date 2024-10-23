"""
snake_network.py
Github: https://github.com/neilc24/slither24
"""

import socket
import pickle
import struct

from config import *

class SnakeNetwork():
    def send_msg(self, conn, raw_data, msg_type):
        """ Send a message and handle exceptions """
        # Header + data
        msg_to_send = struct.pack('!II', msg_type, len(raw_data)) + raw_data
        try:
            conn.sendall(msg_to_send)
        except Exception as e:
            with self.lock_print:
                print(f"Unable to send message. Reason: {e}")
            return False
        return True

    def recv_msg(self, conn, timeout=RECV_TIMEOUT):
        """ Receive message (including header and data of certain length) """
        conn.settimeout(timeout)
        try:
            raw_header = conn.recv(8) # Receive header first
        except socket.timeout:
            with self.lock_print:
                print(f"Socket timed out waiting for header.")
            return None
        except socket.error as e:
            with self.lock_print:
                print(f"Error occured while receiving header. Reason:{e}")
            return None
        if not raw_header:
            return None
        msg_type, msg_len = struct.unpack('!II', raw_header)
        raw_data = b''
        while len(raw_data) < msg_len:
            try:
                packet = conn.recv(msg_len - len(raw_data))
            except socket.timeout:
                with self.lock_print:
                    print(f"Socket timed out waiting for data.")
                return None
            except socket.error as e:
                with self.lock_print:
                    print(f"Error occured while receiving data. Reason:{e}")
                return None
            if not packet:
                with self.lock_print:
                    print(f"Error occured while receiving data.")
                return None
            raw_data += packet
        return raw_data, msg_type

    def send_game_snapshot(self, conn, mygame):
        """ Send game state to a single player"""
        raw_data = pickle.dumps(mygame)
        if not self.send_msg(conn, raw_data, MSG_TYPE_SNAKEGAME):
            with self.lock_print:
                print(f"Connection interrupted while sending game snapshot.")
            return False
        return True

    def send_id(self, conn, snake_id):
        """ Send player their ID """
        raw_data = snake_id.encode()
        if not self.send_msg(conn, raw_data, MSG_TYPE_SNAKEID):
            with self.lock_print:
                print(f"Connection interrupted while sending id.")
            return False
        return True

    def send_death_notice(self, conn):
        """ Send a message to notice player that they died """
        if not self.send_msg(conn, b"", MSG_TYPE_NOTICE):
            with self.lock_print:
                print(f"Connection interrupted while sending id.")
            return False
        return True
    
    def send_input(self, conn, direction, speed):
        """ Send input message """
        raw_data = struct.pack("ff", direction, speed)
        if not self.send_msg(conn, raw_data, MSG_TYPE_INPUT):
            with self.lock_print:
                print(f"Connection interrupted while sending input data.")
            return False
        return True