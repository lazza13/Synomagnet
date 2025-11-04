# Synomagnet

**Easily send magnet links to your Synology Download Station with OTP support**

This project was born out of my need to be able to send downloads 
directly to my Synology NAS from Firefox by clicking on the magnet link.
 Since I couldn’t find any extension that worked with 2FA, I created 
this small tool to make my life easier. There are two folders where 
downloads are saved: one default folder, and another for videos that 
need to be converted.



## Features

- **Add torrents remotely**: Single-click, direct sending of magnet links to Synology Download Station.
- **2FA (OTP) support**: Handles Synology accounts with two-factor authentication.
- **User-friendly GUI**: Configure your Synology settings and folders in a clear and responsive interface.
- **Choose destination on download**: Decide at each magnet whether to use your default or a "conversion" folder.
- **Standalone executable**: Can be built to a single binary for easy use and distribution (no need for Python installed).



## How it Works

- On first run, configure your NAS address, username, and default/conversion download folders (password is *never* saved).
- The app dynamically discovers the correct Synology API endpoints for your server.
- When you add a magnet link:
  - It uses your SID if valid, or prompts for password and OTP if the session expired.
  - Lets you choose (via popup) whether to send the torrent to the default or the conversion folder (I did this because sometimes I need to convert files with automatic scripts in a particular folder) .
  - Gives you instant, clear feedback on success or any error.



## Requirements

- Python 3.8+ (if running from source)
- [requests](https://pypi.org/project/requests/)
- (Optional for standalone): [PyInstaller](https://www.pyinstaller.org/)
- Tkinter (apt-get install python3-tk)

## Installation

### Recommended: Build Standalone Executable

Install PyInstaller:

```bash
pip install pyinstaller
```

Build your standalone app:

```bash
pyinstaller --onefile --windowed synomagnet.py
```

You’ll find the compiled binary in the `dist/` folder.

### Or: Run from Source

```bash
pip install requests
python3 synomagnet.py --settings
```

## Usage

### Configuration

Start the settings GUI:

```bash
synomagnet --settings
```

- Fill out your NAS URL (e.g., `https://yournas:5001`), Synology username, default folder, and conversion folder.
- No password is ever saved; you will be prompted only when a session expires.

### Send a Magnet Link

```bash
synomagnet "magnet:?xt=..."
```

- On each use (if there’s no valid SID), you’ll be prompted for your Synology password and OTP.
- Choose your download folder via popup.

## Create Desktop Entry

To get this bin in the app view and launch gui with settings you can use .desktop file like this:

```
[Desktop Entry]
Name=Synomagnet
Comment=Send magnet links to Download Station
Exec=PATH_TO_SYNOMAGNET --settings
Terminal=false
Type=Application
MimeType=x-scheme-handler/magnet;
Categories=Network;

```

## Development

Feel free to fork, modify, and submit pull requests!

## License

MIT

## Note

- This project is **not affiliated, associated, authorized, endorsed by, or in any way officially connected with Synology Inc.**
- The software is provided “as is”, without warranty of any kind. Use at your own risk.
- This README was written with the help of AI, because the author didn’t feel like writing it all manually.
