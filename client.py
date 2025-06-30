import sys
import socket
import os
import logging

SERVER_HOST = '172.16.16.101'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def send_request(request_str, port, body_bytes=b""):
    server_address = (SERVER_HOST, port)
    
    try:
        with socket.create_connection(server_address, timeout=10) as sock:
            logging.info(f"Connecting to {SERVER_HOST}:{port}...")
            
            sock.sendall(request_str.encode('utf-8'))
            if body_bytes:
                sock.sendall(body_bytes)

            fp = sock.makefile('rb')
            status_line = fp.readline().decode('utf-8').strip()
            logging.info(f"Server status: {status_line}")
            
            headers = {}
            while True:
                line = fp.readline().decode('utf-8').strip()
                if not line:
                    break
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

            content_length = int(headers.get('content-length', 0))

            body = b''
            if content_length > 0:
                body = fp.read(content_length)
            
            fp.close()

            print("\n--- Jawaban Server ---")
            print(f"Status: {status_line}")
            print("Isi Pesan:")
            print(body.decode('utf-8', 'ignore'))
            print("---------------------\n")

    except ConnectionRefusedError:
        logging.error(f"Koneksi ke {SERVER_HOST}:{port} ditolak. Pastikan server berjalan.")
    except socket.timeout:
        logging.error(f"Koneksi ke {SERVER_HOST}:{port} timeout. Cek firewall atau masalah jaringan.")
    except Exception as e:
        logging.error(f"Terjadi error: {e}")

def list_files_on_server(port):
    print(f"\n--- Mengambil daftar file dari server ---")
    request = f"GET /list HTTP/1.1\r\nHost: {SERVER_HOST}\r\n\r\n"
    send_request(request, port)

def upload_file_to_server(port):
    local_filepath = input("Masukkan path lengkap file yang akan diunggah: ")
    if not os.path.exists(local_filepath) or not os.path.isfile(local_filepath):
        print(f"Error: File '{local_filepath}' tidak ditemukan atau bukan file valid.")
        return

    print(f"\n--- Mengunggah {local_filepath} ke server ---")
    try:
        with open(local_filepath, 'rb') as f:
            file_content = f.read()
        
        filename = os.path.basename(local_filepath)
        request_line = f"POST /upload/{filename} HTTP/1.1\r\n"
        headers = f"Host: {SERVER_HOST}\r\nContent-Length: {len(file_content)}\r\n\r\n"
        request = request_line + headers
        
        send_request(request, port, file_content)

    except Exception as e:
        logging.error(f"Gagal membaca file untuk diunggah: {e}")

def delete_file_on_server(port):
    filename = input("Masukkan nama file di server yang akan dihapus: ")
    if not filename:
        print("Nama file tidak boleh kosong.")
        return

    print(f"\n--- Menghapus {filename} dari server ---")
    request = f"DELETE /delete/{filename} HTTP/1.1\r\nHost: {SERVER_HOST}\r\n\r\n"
    send_request(request, port)

def main():
    TARGET_PORT = 8885
    
    while True:
        print("\n===== Menu Klien HTTP =====")
        print(f"Terhubung ke Server: {SERVER_HOST}:{TARGET_PORT}")
        print("1. Lihat daftar file di server")
        print("2. Unggah (upload) file ke server")
        print("3. Hapus file di server")
        print("4. Keluar")
        
        choice = input("Masukkan pilihan Anda (1-4): ")
        
        if choice == '1':
            list_files_on_server(TARGET_PORT)
        elif choice == '2':
            upload_file_to_server(TARGET_PORT)
        elif choice == '3':
            delete_file_on_server(TARGET_PORT)
        elif choice == '4':
            print("Terima kasih telah menggunakan program ini. Keluar...")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")

if __name__ == '__main__':
    main()
