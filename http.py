import sys
import os
import os.path
import uuid
import logging
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        script_path = os.path.abspath(__file__)
        self.base_dir = os.path.dirname(script_path)

        os.makedirs(self.base_dir, exist_ok=True)
        logging.info(f"File operations will be based in: {self.base_dir}")
        
        self.sessions={}
        self.types={}
        self.types['.pdf']='application/pdf'
        self.types['.jpg']='image/jpeg'
        self.types['.txt']='text/plain'
        self.types['.html']='text/html'

    def _get_safe_path(self, client_path):
        safe_filename = os.path.basename(client_path)
        return os.path.join(self.base_dir, safe_filename)

    def http_get(self, object_address, headers):
        if object_address == '/list':
            try:
                files = os.listdir(self.base_dir)
                file_list_str = "\n".join(files)
                return self.response(200, 'OK', file_list_str.encode(), {'Content-Type': 'text/plain'})
            except Exception as e:
                return self.response(500, "Internal Server Error", str(e).encode())

        if object_address == '/':
            return self.response(200, 'OK', b'Ini Adalah web Server percobaan')

        safe_path = self._get_safe_path(object_address.lstrip('/'))
        
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            try:
                with open(safe_path, 'rb') as fp:
                    isi = fp.read()
                fext = os.path.splitext(safe_path)[1]
                content_type = self.types.get(fext, 'application/octet-stream')
                return self.response(200, 'OK', isi, {'Content-Type': content_type})
            except Exception as e:
                return self.response(500, "Internal Server Error", str(e).encode())
        else:
            logging.warning(f"File not found at safe path: {safe_path}")
            return self.response(404, 'Not Found', b'File not found')

    def http_post(self, object_address, headers, body):
        if object_address.startswith('/upload/'):
            filename = object_address[len('/upload/'):]
            safe_path = self._get_safe_path(filename)
            
            if not os.path.basename(filename):
                return self.response(400, 'Bad Request', b'Filename not specified.')
            
            try:
                with open(safe_path, 'wb') as f:
                    f.write(body)
                logging.info(f"File uploaded to {safe_path}")
                return self.response(200, 'OK', f'File {os.path.basename(safe_path)} uploaded successfully.'.encode())
            except Exception as e:
                return self.response(500, 'Internal Server Error', f'Error uploading file: {e}'.encode())
        
        return self.response(400, 'Bad Request', b'Invalid POST request.')

    def http_delete(self, object_address, headers):
        if object_address.startswith('/delete/'):
            filename = object_address[len('/delete/'):]
            safe_path = self._get_safe_path(filename)
            
            if not os.path.basename(filename):
                return self.response(400, 'Bad Request', b'Filename not specified.')
            
            if os.path.exists(safe_path) and os.path.isfile(safe_path):
                try:
                    os.remove(safe_path)
                    logging.info(f"File deleted from {safe_path}")
                    return self.response(200, 'OK', f'File {os.path.basename(safe_path)} deleted.'.encode())
                except Exception as e:
                    return self.response(500, 'Internal Server Error', f'Error deleting file: {e}'.encode())
            else:
                logging.warning(f"Attempt to delete non-existent file at safe path: {safe_path}")
                return self.response(404, 'Not Found', f'File {os.path.basename(safe_path)} not found.'.encode())
        
        return self.response(400, 'Bad Request', b'Invalid DELETE request.')

    def response(self, kode=404, message='Not Found', messagebody=b'', headers={}):
        logging.info(f"Sending response: {kode} {message}")
        tanggal = datetime.now().strftime('%c')
        resp = [
            f"HTTP/1.0 {kode} {message}\r\n",
            f"Date: {tanggal}\r\n", "Connection: close\r\n", "Server: myserver/1.0\r\n",
            f"Content-Length: {len(messagebody)}\r\n"
        ]
        for kk, vv in headers.items():
            resp.append(f"{kk}:{vv}\r\n")
        resp.append("\r\n")
        response_headers = "".join(resp)
        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode('utf-8')
        return response_headers.encode('utf-8') + messagebody

    def proses(self, data):
        try:
            header_end_index = data.find(b"\r\n\r\n")
            if header_end_index == -1: return self.response(400, 'Bad Request', b'Invalid HTTP Request format')
            headers_part_bytes = data[:header_end_index]
            body_part = data[header_end_index + 4:]
            headers_part_str = headers_part_bytes.decode('utf-8')
            baris = headers_part_str.split("\r\n")[0]
            method, object_address, _ = baris.split(" ", 2)
            method = method.upper().strip()
            object_address = object_address.strip()
            logging.info(f"Processing request: {method} {object_address}")
            if method == 'GET':
                return self.http_get(object_address, {})
            elif method == 'POST':
                return self.http_post(object_address, {}, body_part)
            elif method == 'DELETE':
                return self.http_delete(object_address, {})
            else:
                return self.response(501, 'Not Implemented', b'Unsupported method')
        except Exception as e:
            logging.error(f"Error parsing request: {e}, Data: {data[:1024]}")
            return self.response(400, 'Bad Request', b'Malformed request line')
