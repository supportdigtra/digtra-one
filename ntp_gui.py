import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys
from PIL import Image

ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def apply_ntp():
    choice = radio_var.get()
    
    if choice == "manual":
        server = entry_manual.get().strip()
        if not server:
            messagebox.showwarning("Peringatan", "Harap masukkan alamat server NTP manual.")
            return
    else:
        server = choice
        
    try:
        bash_cmd = f"""
        mkdir -p /etc/systemd
        touch /etc/systemd/timesyncd.conf
        sed -i '/^NTP=/d; /^#NTP=/d' /etc/systemd/timesyncd.conf
        echo 'NTP={server}' >> /etc/systemd/timesyncd.conf
        systemctl unmask systemd-timesyncd.service
        systemctl enable systemd-timesyncd.service
        systemctl restart systemd-timesyncd
        timedatectl set-ntp true
        """
        
        result = subprocess.run(['pkexec', 'bash', '-c', bash_cmd], capture_output=True, text=True)
        
        if result.returncode == 0:
            messagebox.showinfo("Sukses", f"Berhasil sinkronisasi waktu!\nServer Digtra Cloud: {server}")
        else:
            if "dismissed" in result.stderr or "Error executing" in result.stderr:
                 pass 
            else:
                 messagebox.showerror("Gagal", f"Terjadi kesalahan sistem:\n{result.stderr}")
                 
    except Exception as e:
        messagebox.showerror("Error", f"Aplikasi gagal dieksekusi:\n{e}")

def toggle_manual():
    if radio_var.get() == "manual":
        entry_manual.configure(state="normal")
        entry_manual.focus()
    else:
        entry_manual.configure(state="disabled")

app = ctk.CTk()
app.title("Digtra Agent - NTP Sync")
app.geometry("480x500") 
app.resizable(False, False)

# --- Mengatur Logo (Bersih dari error ImageTk) ---
logo_filename = "digtra-cloud.png"
logo_path = resource_path(logo_filename)

if os.path.exists(logo_path):
    try:
        logo_image = ctk.CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(80, 80) 
        )
        logo_label = ctk.CTkLabel(app, image=logo_image, text="")
        logo_label.pack(pady=(20, 0))
    except Exception as e:
        print(f"Gambar rusak: {e}")
        ctk.CTkLabel(app, text="").pack(pady=(20, 0))
else:
    ctk.CTkLabel(app, text="").pack(pady=(20, 0))

# --- UI Elements ---
title_label = ctk.CTkLabel(app, text="Digtra Cloud NTP", font=ctk.CTkFont(size=22, weight="bold"), text_color="#005B9F")
title_label.pack(pady=(10, 5))

subtitle_label = ctk.CTkLabel(app, text="Pilih regional server pool atau masukkan manual.", font=ctk.CTkFont(size=12), text_color="gray")
subtitle_label.pack(pady=(0, 15))

frame = ctk.CTkFrame(app)
frame.pack(pady=10, padx=30, fill="both", expand=True)

radio_var = ctk.StringVar(value="id.pool.ntp.org")
options = [
    ("Indonesia (id.pool.ntp.org)", "id.pool.ntp.org"),
    ("Asia (asia.pool.ntp.org)", "asia.pool.ntp.org"),
    ("Global (pool.ntp.org)", "pool.ntp.org"),
    ("Input Manual", "manual")
]

for text, value in options:
    radio = ctk.CTkRadioButton(frame, text=text, variable=radio_var, value=value, command=toggle_manual, font=ctk.CTkFont(size=13))
    radio.pack(anchor="w", pady=10, padx=25)

entry_manual = ctk.CTkEntry(frame, placeholder_text="contoh: time.cloudflare.com", state="disabled", width=260)
entry_manual.pack(anchor="w", padx=55, pady=(0, 15))

btn_apply = ctk.CTkButton(
    app, text="Terapkan & Sinkronisasi", command=apply_ntp, 
    fg_color="#005B9F", hover_color="#003F6F", 
    font=ctk.CTkFont(size=14, weight="bold"), height=40
)
btn_apply.pack(pady=20)

app.mainloop()
