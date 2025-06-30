from socket import *
import socket
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


httpserver = HttpServer()

def ProcessTheClient(connection, address):
    try:
        headers_data = b""
        while b"\r\n\r\n" not in headers_data:
            chunk = connection.recv(1024)
            if not chunk: break
            headers_data += chunk
        
        header_end_pos = headers_data.find(b"\r\n\r\n")
        if header_end_pos == -1: return

        body_chunk = headers_data[header_end_pos + 4:]
        headers_data = headers_data[:header_end_pos + 4]
        
        content_length = 0
        headers_str = headers_data.decode('utf-8', 'ignore')
        for line in headers_str.split('\r\n'):
            if line.lower().startswith('content-length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                except (ValueError, IndexError):
                    content_length = 0
                break
        
        body_data = body_chunk
        while len(body_data) < content_length:
            chunk = connection.recv(1024)
            if not chunk: break
            body_data += chunk
        
        full_request = headers_data + body_data
        hasil = httpserver.proses(full_request)
        connection.sendall(hasil)

    except Exception as e:
        logging.error(f"Error processing client {address}: {e}")
    finally:
        connection.close()
        logging.info(f"Connection from {address} closed.")
    return

def Server():
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = 8885
    
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        my_socket.bind((SERVER_HOST, SERVER_PORT))
        my_socket.listen(1)
        logging.info(f"Thread Pool Server running on http://{SERVER_HOST}:{SERVER_PORT}...")
    except OSError as e:
        logging.error(f"Failed to bind to {SERVER_HOST}:{SERVER_PORT}. Error: {e}")
        sys.exit(1)

    with ThreadPoolExecutor(20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                logging.info(f"Connection received from {client_address}")
                executor.submit(ProcessTheClient, connection, client_address)
            except KeyboardInterrupt:
                logging.info("Server shutting down by user request (Ctrl+C).")
                break
            except Exception as e:
                logging.error(f"An error occurred in the main server loop: {e}")

if __name__ == "__main__":
    Server()
