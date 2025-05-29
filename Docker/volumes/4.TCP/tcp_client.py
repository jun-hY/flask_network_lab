import socket

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.connect(('10.9.0.6', 9090))

tcp.sendall(b"hello Server!\n")
tcp.sendall(b"Hello Again!\n")

tcp.close
