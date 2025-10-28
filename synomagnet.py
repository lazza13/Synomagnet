import os, json, requests, sys, tkinter as tk
from tkinter import simpledialog, messagebox

CONFIG_FILE = os.path.expanduser('~/.synomagnet.json')
SID_FILE    = os.path.expanduser('~/.synosid')

ERROR_MAP = {
    400: "File upload failed",
    401: "Maximum number of downloads reached",
    402: "Destination folder denied (insufficient permissions)",
    403: "Destination folder does not exist",
    404: "Invalid task id",
    405: "Invalid task action",
    406: "No default destination set",
    407: "Error setting destination",
    408: "File does not exist"
}

def save_file_secure(filename, data, jdump=False):
    with open(filename, 'w') as f:
        if jdump: json.dump(data, f)
        else:     f.write(data)
    os.chmod(filename, 0o600)

def read_file(filename, is_json=False):
    if not os.path.exists(filename): return None
    with open(filename) as f:
        return json.load(f) if is_json else f.read().strip()

def get_api_endpoints(base_url):
    url = base_url.rstrip('/') + '/webapi/query.cgi'
    params = {
        "api":"SYNO.API.Info",
        "version":"1",
        "method":"query",
        "query":"all"
    }
    try:
        resp = requests.get(url, params=params, verify=False, timeout=5).json()
        return {k:v['path'] for k,v in resp['data'].items()}
    except Exception:
        return None

def login_flow(cfg, api_paths):
    root = tk.Tk(); root.withdraw()
    password = simpledialog.askstring("Password", "Enter your Synology password:", show="*")
    if not password:
        messagebox.showerror("Login error", "Password is required.")
        return None
    otp = simpledialog.askstring("OTP", "Please enter your 2FA OTP:")
    if not otp:
        messagebox.showerror("Login error", "OTP is required.")
        return None
    payload = {
        "api": "SYNO.API.Auth",
        "version": "3",
        "method": "login",
        "account": cfg['user'],
        "passwd": password,
        "otp_code": otp,
        "session": "DownloadStation",
        "format": "sid"
    }
    url = cfg['server'].rstrip('/') + '/webapi/' + api_paths['SYNO.API.Auth']
    resp = requests.get(url, params=payload, verify=False).json()
    if resp.get('success'):
        sid = resp['data']['sid']
        save_file_secure(SID_FILE, sid)
        messagebox.showinfo("Login", "SID obtained and saved ✅")
        return sid
    else:
        messagebox.showerror("Login error", json.dumps(resp))
        return None

def load_config():
    c = read_file(CONFIG_FILE, is_json=True)
    return c if c else {}

def save_config(cfg):
    save_file_secure(CONFIG_FILE, cfg, jdump=True)

def check_sid(cfg, sid, api_paths):
    url = cfg['server'].rstrip('/') + '/webapi/' + api_paths['SYNO.DownloadStation.Task']
    params = {
        "api": "SYNO.DownloadStation.Task",
        "version": "1",
        "method": "list",
        "_sid": sid,
        "limit": 1
    }
    try:
        resp = requests.get(url, params=params, verify=False, timeout=5).json()
        return resp.get('success', False)
    except Exception:
        return False

def ensure_sid(cfg, api_paths):
    sid = read_file(SID_FILE)
    if sid and check_sid(cfg, sid, api_paths):
        return sid
    else:
        return login_flow(cfg, api_paths)

def send_magnet(cfg, magnet, sid, api_paths, dest):
    url = cfg['server'].rstrip('/') + '/webapi/' + api_paths['SYNO.DownloadStation.Task']
    payload = {
        "api": "SYNO.DownloadStation.Task",
        "version": "1",
        "method": "create",
        "uri": magnet,
        "destination": dest,
        "_sid": sid
    }
    r = requests.get(url, params=payload, verify=False).json()
    if r.get('success'):
        return True, None
    else:
        code = r.get('error', {}).get('code', 0)
        error_str = ERROR_MAP.get(code, f"Unknown error (code {code})")
        return False, error_str

def ask_destination(cfg):
    root = tk.Tk(); root.withdraw()
    answer = messagebox.askquestion(
        "Download Destination",
        "Do you want to use the conversion folder?"
    )
    return cfg.get("conversion_dir") if answer == "yes" else cfg.get("download_dir")

def gui_settings():
    root = tk.Tk()
    root.title("Synology Magnet Settings")
    root.geometry("480x210")
    root.minsize(380, 160)

    frm = tk.Frame(root, padx=16, pady=8)
    frm.pack(fill="both", expand=True)

    cfg = load_config()
    api_base = cfg.get("server", "")
    api_paths = get_api_endpoints(api_base) if api_base else {}

    labels = [
        "NAS URL:", "User:",
        "Default folder:", "Conversion folder:"
    ]
    vars_ = [tk.StringVar() for _ in range(4)]
    if cfg:
        fields = [cfg.get("server",""), cfg.get("user",""), cfg.get("download_dir",""), cfg.get("conversion_dir","")]
        for var, val in zip(vars_, fields): var.set(val)

    for i, (lbl, var) in enumerate(zip(labels, vars_)):
        tk.Label(frm, text=lbl, anchor="e").grid(row=i, column=0, sticky="e", padx=(0, 8), pady=4)
        ent = tk.Entry(frm, textvariable=var)
        ent.grid(row=i, column=1, sticky="ew", padx=(0, 8), pady=4)

    # Responsive columns
    frm.grid_columnconfigure(0, minsize=120, weight=0)
    frm.grid_columnconfigure(1, weight=1)

    def discover_paths():
        server_v = vars_[0].get()
        paths = get_api_endpoints(server_v)
        if paths:
            messagebox.showinfo("API", "API endpoints successfully discovered!")
        else:
            messagebox.showerror("Error", "Unable to get endpoints, check your NAS URL and its status.")

    def save_all():
        c = {
            "server": vars_[0].get(),
            "user": vars_[1].get(),
            "download_dir": vars_[2].get(),
            "conversion_dir": vars_[3].get()
        }
        paths = get_api_endpoints(c['server'])
        if not paths or "SYNO.API.Auth" not in paths or "SYNO.DownloadStation.Task" not in paths:
            messagebox.showerror("API", "DownloadStation and/or Auth endpoints not found! Check your NAS URL and Download Station status.")
            return
        c["api_paths"] = paths
        save_config(c)
        messagebox.showinfo("Saved", "Configuration and endpoint mapping saved ✅")
        root.quit()

    btn_frm = tk.Frame(frm)
    btn_frm.grid(row=5, columnspan=2, pady=(16,0), sticky="ew")
    btn_frm.grid_columnconfigure(0, weight=1)
    btn_frm.grid_columnconfigure(1, weight=1)

    discover_btn = tk.Button(btn_frm, text="Check Endpoints", command=discover_paths, width=18)
    discover_btn.grid(row=0, column=0, padx=12, sticky="ew")
    save_btn = tk.Button(btn_frm, text="Save", command=save_all, width=15)
    save_btn.grid(row=0, column=1, padx=12, sticky="ew")

    root.mainloop()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store_true")
    parser.add_argument("magnet", nargs='?', help="Magnet link")
    args = parser.parse_args()

    if args.settings:
        gui_settings()
        return

    if args.magnet and args.magnet.startswith("magnet"):
        cfg = load_config()
        if not cfg or 'api_paths' not in cfg:
            print("No config found! Run 'synomagnet --settings' and let the app discover the API.")
            return
        api_paths = cfg['api_paths']
        sid = ensure_sid(cfg, api_paths)
        dest = ask_destination(cfg)
        ok, error_str = send_magnet(cfg, args.magnet, sid, api_paths, dest)
        root = tk.Tk(); root.withdraw()
        if ok:
            messagebox.showinfo("OK", f"Magnet sent to Download Station!\nFolder: {dest}")
        else:
            messagebox.showerror("Error", error_str)
        return

    print("Usage:\n  synomagnet --settings   (configure)\n  synomagnet magnet:?xt=...  (start download)")

if __name__ == "__main__":
    main()