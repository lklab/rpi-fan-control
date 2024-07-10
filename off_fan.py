import sys
import socket
import json

command = {}
command['cmd'] = 'control'
command['val'] = '0'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 10105))

sock.send(json.dumps(command).encode())
sock.close()
