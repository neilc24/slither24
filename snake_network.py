"""
snake_network.py

Github: https://github.com/neilc24/slither24
Author: Neil (GitHub: neilc24)
"""

import socket
import pickle
import struct
import sys
import os

from config import *

class SnakeNetwork():
    def send_msg(self, conn, raw_data, msg_type, *, lock_print):
        """ Send a message and handle exceptions """
        # Header + data
        msg_to_send = struct.pack('!II', msg_type, len(raw_data)) + raw_data
        try:
            conn.sendall(msg_to_send)
        except Exception as e:
            with lock_print:
                print(f"Unable to send message. Reason: {e}")
            return False
        return True

    def recv_msg(self, conn, *, timeout=RECV_TIMEOUT, lock_print):
        """ Receive message (including header and data of certain length) """
        try:
            conn.settimeout(timeout)
            raw_header = conn.recv(8) # Receive header first
        except socket.timeout:
            with lock_print:
                print(f"Timeout while waiting for header.")
            return None
        except socket.error as e:
            with lock_print:
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
                with lock_print:
                    print(f"Timeout while waiting for data.")
                return None
            except socket.error as e:
                with lock_print:
                    print(f"Error occured while receiving data. Reason:{e}")
                return None
            if not packet:
                with lock_print:
                    print(f"Error occured while receiving data.")
                return None
            raw_data += packet
        return raw_data, msg_type

    def send_game_snapshot(self, conn, game_snapshot, *, lock_print):
        """ Send game state to a single player"""
        raw_data = pickle.dumps(game_snapshot)
        if not self.send_msg(conn, raw_data, MSG_TYPE_SNAKEGAME, lock_print=lock_print):
            with lock_print:
                print(f"Connection interrupted while sending game snapshot.")
            return False
        return True

    def send_id(self, conn, snake_id, *, lock_print):
        """ Send player their ID """
        raw_data = snake_id.encode()
        if not self.send_msg(conn, raw_data, MSG_TYPE_SNAKEID, lock_print=lock_print):
            with lock_print:
                print(f"Connection interrupted while sending id.")
            return False
        return True

    def send_death_notice(self, conn, *, lock_print):
        """ Send a message to notice player that they died """
        if not self.send_msg(conn, b"", MSG_TYPE_NOTICE, lock_print=lock_print):
            with lock_print:
                print(f"Connection interrupted while sending id.")
            return False
        return True
    
    def send_passkey(self, conn, *, lock_print):
        """ Send input message """
        raw_data = PASSKEY.encode('utf-8')
        if not self.send_msg(conn, raw_data, MSG_TYPE_PASSKEY, lock_print=lock_print):
            with lock_print:
                print(f"Connection interrupted while sending passkey.")
            return False
        return True
    
    def send_input(self, conn, direction, speed, *, lock_print):
        """ Send input message """
        raw_data = struct.pack("ff", direction, speed)
        if not self.send_msg(conn, raw_data, MSG_TYPE_INPUT, lock_print=lock_print):
            with lock_print:
                print(f"Connection interrupted while sending input data.")
            return False
        return True
    
    def get_abs_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)