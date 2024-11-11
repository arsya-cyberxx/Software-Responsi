import asyncio
import websockets
import pandas as pd
import json
from datetime import datetime

# Baca data pengguna dari CSV
data = pd.read_csv('DataUser.csv')
login_attempts = {}         # Melacak percobaan login untuk setiap user ID
password_reset_stage = {}    # Menyimpan status reset password untuk setiap user ID

print("Server is starting...")

# Fungsi untuk menyimpan data kembali ke CSV setelah perubahan
def save_data():
    data.to_csv('DataUser.csv', index=False)
    print("Data saved to CSV.")

# Fungsi untuk menangani setiap koneksi WebSocket
async def handle_connection(websocket, path):
    print("New connection established.")
    user_id_valid = False  # Flag untuk status validasi ID
    user_ID = None         # Menyimpan ID pengguna yang valid

    try:
        async for message in websocket:
            print(f"Received message: {message}")
            content = json.loads(message)

            # Jika pesan berisi user_IDinput (validasi ID)
            if "user_IDinput" in content:
                user_ID = content["user_IDinput"].strip()

                # Periksa apakah ID ada di data
                if user_ID in data['ID'].astype(str).str.strip().values:
                    user_id_valid = True
                    response = {"login_status": "id_valid"}
                    print("ID is valid. Waiting for password.")
                else:
                    response = {"login_status": "failed", "message": "ID not found"}
                    print("ID not found.")
                
                await websocket.send(json.dumps(response))

            # Jika ID valid dan pesan berisi password
            elif user_id_valid and "user_password" in content:
                user_password = content["user_password"].strip()
                correct_password = data[data['ID'].astype(str).str.strip() == user_ID]['Password'].values[0].strip()

                # Inisialisasi percobaan login dan status reset password jika belum ada
                if user_ID not in login_attempts:
                    login_attempts[user_ID] = 0
                if user_ID not in password_reset_stage:
                    password_reset_stage[user_ID] = False

                # Cek apakah user dalam tahap reset password
                if password_reset_stage[user_ID]:
                    # Perbarui password dan simpan
                    data.loc[data['ID'].astype(str).str.strip() == user_ID, 'Password'] = user_password
                    data.loc[data['ID'].astype(str).str.strip() == user_ID, 'lastLogin'] = datetime.now().isoformat()
                    save_data()
                    response = {"login_status": "success", "message": "Password updated successfully"}
                    await websocket.send(json.dumps(response))
                    print(f"Password for user {user_ID} updated successfully.")
                    
                    # Reset status setelah perubahan password
                    password_reset_stage[user_ID] = False
                    login_attempts[user_ID] = 0
                    continue

                # Verifikasi password
                if user_password == correct_password:
                    # Login berhasil
                    data.loc[data['ID'].astype(str).str.strip() == user_ID, 'lastLogin'] = datetime.now().isoformat()
                    save_data()
                    response = {"login_status": "success", "message": "Login successful"}
                    await websocket.send(json.dumps(response))
                    print(f"User {user_ID} logged in successfully.")
                    login_attempts[user_ID] = 0  # Reset percobaan jika login berhasil
                else:
                    # Login gagal
                    login_attempts[user_ID] += 1
                    if login_attempts[user_ID] < 3:
                        response = {"login_status": "failed", "message": f"Password incorrect. Attempt {login_attempts[user_ID]} of 3"}
                        print(f"Incorrect password for user {user_ID}. Attempt {login_attempts[user_ID]} of 3.")
                    else:
                        # Maksimal percobaan tercapai, memulai proses reset password
                        response = {"login_status": "failed", "message": "Maximum attempts reached. Please reset your password."}
                        password_reset_stage[user_ID] = True  # Aktifkan tahap reset password
                        login_attempts[user_ID] = 0  # Reset counter setelah 3 kali percobaan
                        print(f"User {user_ID} has reached maximum login attempts. Password reset required.")
                
                await websocket.send(json.dumps(response))

    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Fungsi utama untuk menjalankan server
async def main():
    print("Setting up server...")
    async with websockets.serve(handle_connection, "0.0.0.0", 5000):
        print("Server WebSocket berjalan di 0.0.0.0:5000")
        await asyncio.Future()  # Menjaga server tetap berjalan

if __name__ == "__main__":
    print("Running the server...")
    asyncio.run(main())
