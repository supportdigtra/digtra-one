import customtkinter as ctk
from tkinter import messagebox
import subprocess
import os
import sys
import threading
import psutil
from PIL import Image

# --- Konfigurasi Tema ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
DIGTRA_BLUE = "#005B9F"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DigtraDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Digtra Agent - Control Panel")
        self.geometry("950x720") # Tinggi disesuaikan agar Copyright tidak terpotong
        self.resizable(False, False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1) 

        logo_path = resource_path("digtra-cloud.png")
        if os.path.exists(logo_path):
            try:
                self.logo_image = ctk.CTkImage(Image.open(logo_path), size=(60, 60))
                self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image, text="")
                self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 0))
            except: pass

        ctk.CTkLabel(self.sidebar_frame, text="Digtra Agent", 
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=1, column=0, padx=20, pady=(40, 30))

        self.btn_idm = self.create_sidemenu("Identity Manager (IDM)", self.show_idm_frame, 2)
        self.btn_domain = self.create_sidemenu("Domain Management", self.show_domain_frame, 3)
        self.btn_profile = self.create_sidemenu("Profile Migration", self.show_profile_frame, 4)
        self.btn_performance = self.create_sidemenu("Performance Monitor", self.show_performance_frame, 5)
        self.btn_ntp = self.create_sidemenu("NTP Configuration", self.show_ntp_frame, 6)

        # COPYRIGHT FOOTER - Akan selalu tampil di dasar Sidebar
        ctk.CTkLabel(self.sidebar_frame, text="Copyright @DigtraCloud 2026", 
                     font=ctk.CTkFont(size=11), text_color="gray50").grid(row=8, column=0, padx=20, pady=(0, 20), sticky="s")

        # ==================== FRAMES ====================
        self.idm_frame = self.create_content_frame("Identity Manager", "Informasi Active Directory (SSSD).")
        self.domain_frame = self.create_content_frame("Domain Management", "Koneksi ke Active Directory.")
        self.profile_frame = self.create_content_frame("Profile Migration", "Salin data antar user.")
        self.performance_frame = self.create_content_frame("Performance Monitor", "Status real-time sistem.")
        self.ntp_frame = self.create_content_frame("NTP Configuration", "Sinkronisasi waktu sistem.")

        self.setup_idm_ui()
        self.setup_domain_ui()
        self.setup_profile_ui()
        self.setup_performance_ui()
        self.setup_ntp_ui()

        self.show_idm_frame()
        self.update_stats()

    # --- UI HELPERS ---
    def create_sidemenu(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, fg_color="transparent", anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=10)
        return btn

    def create_content_frame(self, title, subtitle):
        frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=24, weight="bold"), text_color=DIGTRA_BLUE).pack(pady=(30, 5), anchor="w", padx=40)
        ctk.CTkLabel(frame, text=subtitle, text_color="gray").pack(anchor="w", padx=40, pady=(0, 20))
        return frame

    def create_input(self, parent, label, placeholder, show=""):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=20, pady=(5, 0))
        ent = ctk.CTkEntry(parent, placeholder_text=placeholder, width=350, show=show)
        ent.pack(anchor="w", padx=20, pady=5); return ent

    # --- IDM UI (TERINTEGRASI DENGAN SSSD.CONF) ---
    def setup_idm_ui(self):
        self.info_container = ctk.CTkFrame(self.idm_frame)
        self.info_container.pack(fill="x", expand=False, padx=40, pady=10)
        
        self.idm_labels = {}
        # Field berdasarkan isi file sssd.conf
        fields = ["IPA Hostname:", "IPA Domain:", "IPA Server:", "ID Provider:", "Access Provider:", "Status SSSD:"]
        
        for field in fields:
            row = ctk.CTkFrame(self.info_container, fg_color="transparent")
            row.pack(fill="x", pady=8, padx=20)
            ctk.CTkLabel(row, text=field, width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            val_label = ctk.CTkLabel(row, text="Memuat...", text_color="gray")
            val_label.pack(side="left")
            self.idm_labels[field] = val_label

        # Tombol Edit Config SSSD
        btn_f = ctk.CTkFrame(self.idm_frame, fg_color="transparent")
        btn_f.pack(anchor="w", padx=40, pady=20)
        self.btn_edit_sssd = ctk.CTkButton(btn_f, text="✎ Edit SSSD Config", fg_color="#ffc107", hover_color="#e0a800", text_color="black", command=self.open_sssd_editor)
        self.btn_edit_sssd.pack(side="left")

    def refresh_idm(self):
        for field, label in self.idm_labels.items():
            label.configure(text="Memuat...", text_color="gray")
        threading.Thread(target=self.fetch_idm_data, daemon=True).start()

    def fetch_idm_data(self):
        sssd_data = {
            "IPA Hostname:": "Not Configured",
            "IPA Domain:": "Not Configured",
            "IPA Server:": "Not Configured",
            "ID Provider:": "Not Configured",
            "Access Provider:": "Not Configured",
            "Status SSSD:": "Inactive"
        }

        try:
            # Baca file sssd.conf menggunakan pkexec
            content = subprocess.check_output(['pkexec', 'cat', '/etc/sssd/sssd.conf'], text=True)
            for line in content.split('\n'):
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    
                    if key == 'ipa_hostname': sssd_data["IPA Hostname:"] = val
                    elif key == 'ipa_domain': sssd_data["IPA Domain:"] = val
                    elif key == 'ipa_server': sssd_data["IPA Server:"] = val
                    elif key == 'id_provider': sssd_data["ID Provider:"] = val
                    elif key == 'access_provider': sssd_data["Access Provider:"] = val
        except Exception:
            for k in sssd_data.keys():
                if k != "Status SSSD:": sssd_data[k] = "Akses ditolak atau file belum ada"

        try:
            status = subprocess.getoutput('systemctl is-active sssd')
            sssd_data["Status SSSD:"] = "Active (Running)" if status == "active" else "Inactive / Error"
        except: pass

        self.after(0, lambda: self.update_idm_ui(sssd_data))

    def update_idm_ui(self, data):
        color_status = "#28a745" if "Active" in data["Status SSSD:"] else "#dc3545"
        for field, value in data.items():
            color = color_status if field == "Status SSSD:" else "white"
            self.idm_labels[field].configure(text=value, text_color=color)

    # --- SSSD BUILT-IN TEXT EDITOR ---
    def open_sssd_editor(self):
        try:
            content = subprocess.check_output(['pkexec', 'cat', '/etc/sssd/sssd.conf'], text=True)
        except Exception:
            content = "# /etc/sssd/sssd.conf tidak ditemukan atau kosong.\n"

        editor = ctk.CTkToplevel(self)
        editor.title("SSSD Configuration Editor - Digtra Agent")
        editor.geometry("850x600")
        editor.grab_set() # Fokus terpusat ke pop-up ini

        ctk.CTkLabel(editor, text="Edit File: /etc/sssd/sssd.conf", font=ctk.CTkFont(weight="bold", size=18)).pack(pady=(20, 10))

        textbox = ctk.CTkTextbox(editor, width=800, height=450, font=ctk.CTkFont(family="monospace", size=13))
        textbox.pack(pady=10, padx=20)
        textbox.insert("0.0", content)

        def save_config():
            new_content = textbox.get("0.0", "end")
            try:
                # Simpan menggunakan Bash dan pkexec, langsung ganti hak akses dan restart SSSD
                cmd = 'cat > /etc/sssd/sssd.conf && chmod 600 /etc/sssd/sssd.conf && systemctl restart sssd'
                process = subprocess.Popen(['pkexec', 'bash', '-c', cmd], stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                _, err = process.communicate(input=new_content)

                if process.returncode == 0:
                    messagebox.showinfo("Sukses", "Konfigurasi SSSD berhasil disimpan dan layanan SSSD telah di-restart!", parent=editor)
                    editor.destroy()
                    self.refresh_idm() # Refresh layar utama agar data baru terbaca
                else:
                    messagebox.showerror("Gagal", f"Error menyimpan file:\n{err}", parent=editor)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=editor)

        btn_save = ctk.CTkButton(editor, text="Save & Restart SSSD", fg_color="#28a745", hover_color="#218838", height=40, command=save_config)
        btn_save.pack(pady=10)

    # --- DOMAIN UI ---
    def setup_domain_ui(self):
        f = ctk.CTkFrame(self.domain_frame); f.pack(fill="both", expand=True, padx=40, pady=10)
        self.ent_dom = self.create_input(f, "Domain FQDN:", "Masukkan FQDN (ex: corp.digtra.local)")
        self.ent_user_dom = self.create_input(f, "Username Admin AD:", "Masukkan username")
        self.ent_pass_dom = self.create_input(f, "Admin Password:", "****", show="*")
        btn_f = ctk.CTkFrame(f, fg_color="transparent"); btn_f.pack(anchor="w", padx=20, pady=20)
        self.btn_j = ctk.CTkButton(btn_f, text="Join Domain", fg_color="#28a745", command=self.join_domain)
        self.btn_j.pack(side="left", padx=5)

    # --- PROFILE UI ---
    def setup_profile_ui(self):
        f = ctk.CTkFrame(self.profile_frame); f.pack(fill="both", expand=True, padx=40, pady=10)
        ctk.CTkLabel(f, text="Pindahkan data (Desktop, Documents, dll) dari user lama ke user baru.", wraplength=400, justify="left").pack(pady=10, padx=20, anchor="w")
        self.ent_old_user = self.create_input(f, "User Lama (Source):", "Username AD atau Lokal")
        self.ent_new_user = self.create_input(f, "User Baru (Target):", "Username tujuan (ex: digtra-one)")
        self.btn_mig = ctk.CTkButton(f, text="Mulai Migrasi Profil", fg_color=DIGTRA_BLUE, height=45, command=self.start_migration)
        self.btn_mig.pack(pady=30, padx=20)
        self.prog_label = ctk.CTkLabel(f, text="Status: Siap", text_color="gray"); self.prog_label.pack()

    # --- PERFORMANCE UI ---
    def setup_performance_ui(self):
        f = ctk.CTkFrame(self.performance_frame); f.pack(fill="both", expand=True, padx=40, pady=10)
        
        ctk.CTkLabel(f, text="CPU Usage", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=30, pady=(20, 5))
        self.cpu_bar = ctk.CTkProgressBar(f, width=500, height=20)
        self.cpu_bar.pack(anchor="w", padx=30)
        self.cpu_label = ctk.CTkLabel(f, text="0%"); self.cpu_label.pack(anchor="w", padx=30)

        ctk.CTkLabel(f, text="Memory (RAM) Usage", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=30, pady=(20, 5))
        self.ram_bar = ctk.CTkProgressBar(f, width=500, height=20)
        self.ram_bar.pack(anchor="w", padx=30)
        self.ram_label = ctk.CTkLabel(f, text="0 MB / 0 MB"); self.ram_label.pack(anchor="w", padx=30)

    def update_stats(self):
        cpu_p = psutil.cpu_percent()
        self.cpu_bar.set(cpu_p / 100)
        self.cpu_label.configure(text=f"{cpu_p}%")
        
        ram = psutil.virtual_memory()
        self.ram_bar.set(ram.percent / 100)
        self.ram_label.configure(text=f"{ram.used // (1024*1024)} MB / {ram.total // (1024*1024)} MB ({ram.percent}%)")
        self.after(1000, self.update_stats)

    # --- NTP UI ---
    def setup_ntp_ui(self):
        f = ctk.CTkFrame(self.ntp_frame); f.pack(fill="both", expand=True, padx=40, pady=10)
        self.ntp_var = ctk.StringVar(value="id.pool.ntp.org")
        
        ntp_options = [
            ("Indonesia (id.pool.ntp.org)", "id.pool.ntp.org"),
            ("Asia (asia.pool.ntp.org)", "asia.pool.ntp.org"),
            ("Global (pool.ntp.org)", "pool.ntp.org"),
            ("Server AD (Manual)", "manual")
        ]

        for text, value in ntp_options:
            ctk.CTkRadioButton(f, text=text, variable=self.ntp_var, value=value, 
                               command=self.toggle_manual_ntp).pack(anchor="w", padx=25, pady=8)

        self.ent_ntp = ctk.CTkEntry(f, placeholder_text="Masukkan IP Server NTP", state="disabled", width=300)
        self.ent_ntp.pack(anchor="w", padx=55, pady=10)
        
        self.btn_ntp_apply = ctk.CTkButton(self.ntp_frame, text="Sync Waktu Sekarang", command=self.apply_ntp)
        self.btn_ntp_apply.pack(pady=20)

    def toggle_manual_ntp(self):
        self.ent_ntp.configure(state="normal" if self.ntp_var.get() == "manual" else "disabled")

    # --- LOGIKA CORE THREADING ---
    def start_migration(self):
        old_u, new_u = self.ent_old_user.get().strip(), self.ent_new_user.get().strip()
        if not old_u or not new_u: return messagebox.showwarning("Peringatan", "Isi kedua username!")
        
        src = f"/home/{old_u}" if os.path.exists(f"/home/{old_u}") else f"/home/{old_u}@ira.pegadaian.co.id"
        dst = f"/home/{new_u}"
        
        if not os.path.exists(src): return messagebox.showerror("Error", "Folder user lama tidak ditemukan.")
        if not os.path.exists(dst): return messagebox.showerror("Error", "Folder user baru tidak ditemukan. Pastikan sudah pernah login minimal 1x.")
        
        if messagebox.askyesno("Konfirmasi", f"Salin data dari {old_u} ke {new_u}?"):
            self.btn_mig.configure(state="disabled", text="Sedang Menyalin...")
            self.prog_label.configure(text="Status: Proses menyalin...", text_color="orange")
            threading.Thread(target=self.run_mig, args=(src, dst, new_u), daemon=True).start()

    def run_mig(self, s, d, user):
        cmd = f"rsync -av --exclude='.cache' --ignore-errors {s}/ {d}/ && chown -R {user} {d}"
        res = subprocess.run(['pkexec', 'bash', '-c', cmd], capture_output=True, text=True)
        self.after(0, lambda: self.btn_mig.configure(state="normal", text="Mulai Migrasi Profil"))
        if res.returncode == 0:
            self.after(0, lambda: messagebox.showinfo("Sukses", "Migrasi Profil Berhasil!"))
            self.after(0, lambda: self.prog_label.configure(text="Status: Berhasil", text_color="#28a745"))
        else:
            self.after(0, lambda: messagebox.showerror("Gagal", res.stderr))
            self.after(0, lambda: self.prog_label.configure(text="Status: Gagal", text_color="#dc3545"))

    def join_domain(self):
        self.btn_j.configure(state="disabled", text="Connecting...")
        threading.Thread(target=self.run_join, args=(self.ent_dom.get(), self.ent_user_dom.get(), self.ent_pass_dom.get()), daemon=True).start()

    def run_join(self, d, u, p):
        cmd = f"echo '{p}' | realm join -U {u} {d} --verbose"
        res = subprocess.run(['pkexec', 'bash', '-c', cmd], capture_output=True, text=True)
        self.after(0, lambda: self.btn_j.configure(state="normal", text="Join Domain"))
        if res.returncode == 0: messagebox.showinfo("Sukses", "Berhasil!"); self.refresh_idm()
        else: messagebox.showerror("Error", res.stderr)

    def apply_ntp(self):
        self.btn_ntp_apply.configure(state="disabled", text="Menyinkronkan...")
        threading.Thread(target=self.run_ntp, daemon=True).start()

    def run_ntp(self):
        srv = self.ent_ntp.get() if self.ntp_var.get() == "manual" else self.ntp_var.get()
        cmd = f"timedatectl set-ntp false; echo 'NTP={srv}' > /etc/systemd/timesyncd.conf; systemctl restart systemd-timesyncd; timedatectl set-ntp true"
        res = subprocess.run(['pkexec', 'bash', '-c', cmd], capture_output=True, text=True)
        self.after(0, lambda: self.btn_ntp_apply.configure(state="normal", text="Sync Waktu Sekarang"))
        if res.returncode == 0:
            self.after(0, lambda: messagebox.showinfo("Sukses", f"Waktu berhasil disinkronisasi ke {srv}"))
        else:
            self.after(0, lambda: messagebox.showerror("Error", "Gagal menyinkronkan waktu."))

    def hide_all(self):
        for f in [self.idm_frame, self.domain_frame, self.profile_frame, self.performance_frame, self.ntp_frame]: f.grid_forget()
        for b in [self.btn_idm, self.btn_domain, self.btn_profile, self.btn_performance, self.btn_ntp]: b.configure(fg_color="transparent")

    def show_idm_frame(self): self.hide_all(); self.idm_frame.grid(row=0, column=1, sticky="nsew"); self.btn_idm.configure(fg_color=DIGTRA_BLUE); self.refresh_idm()
    def show_domain_frame(self): self.hide_all(); self.domain_frame.grid(row=0, column=1, sticky="nsew"); self.btn_domain.configure(fg_color=DIGTRA_BLUE)
    def show_profile_frame(self): self.hide_all(); self.profile_frame.grid(row=0, column=1, sticky="nsew"); self.btn_profile.configure(fg_color=DIGTRA_BLUE)
    def show_performance_frame(self): self.hide_all(); self.performance_frame.grid(row=0, column=1, sticky="nsew"); self.btn_performance.configure(fg_color=DIGTRA_BLUE)
    def show_ntp_frame(self): self.hide_all(); self.ntp_frame.grid(row=0, column=1, sticky="nsew"); self.btn_ntp.configure(fg_color=DIGTRA_BLUE)

if __name__ == "__main__":
    DigtraDashboard().mainloop()
