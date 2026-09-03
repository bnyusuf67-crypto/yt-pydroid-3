import urllib.request
import re
import os
import time
import subprocess
import json
import shutil
from datetime import datetime

# ==================== YAPILANDIRMA ====================
PLAYLIST_FILE = "playlist.m3u"
STREAMS_DIR = "streams"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FETCH_TIMEOUT = 12

# Git Repository Ayarları (Kendi Bilgilerinizle Değiştirin, Pydroid Terminalinde)
GITHUB_USER = "KULLANICI_ADINIZ"
GITHUB_REPO = "youtube-iptv"
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" # Personal Access Token (github.com/settings/tokens üzerinden alınan token)

# KANAL LİSTESİ
CHANNELS = [
    {"name": "TRT Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/2/29/TRT_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@trthaber/live"},
    {"name": "CNN Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b2/CNN_Turk_logo.png", "group": "Haber", "url": "https://www.youtube.com/@cnnturk/live"},
    {"name": "NTV", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d7/NTV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@NTV/live"},
    {"name": "A Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/8/87/A_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@ahaber/live"},
    {"name": "Haber Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/07/Haberturk_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@HaberturkTV/live"},
    {"name": "Halk TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/dc/Halk_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@Halktvkanali/live"},
    {"name": "Sozcu TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Sozcu_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@SZCTVKanali/live"},
    {"name": "TGRT Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/TGRT_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tgrthabertv/live"},
    {"name": "Flash Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/08/Flash_Haber_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@FlashHaberTV/live"},
    {"name": "Haber Global", "logo": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Haber_Global_logo.png", "group": "Haber", "url": "https://www.youtube.com/@haberglobal/live"},
    {"name": "TV 100", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/7b/TV100_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tv100/live"},
    {"name": "Bloomberg HT", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Bloomberg_HT_logo.png", "group": "Ekonomi", "url": "https://www.youtube.com/@BloombergHT/live"},
    {"name": "Bengu Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Bengu_Turk_logo.png", "group": "Haber", "url": "https://www.youtube.com/@benguturktv/live"},
    {"name": "KRT TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/KRT_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@krttv/live"},
    {"name": "Ulusal Kanal", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a8/Ulusal_Kanal_logo.png", "group": "Haber", "url": "https://www.youtube.com/@UlusalKanalTV/live"},
    {"name": "Ulke TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Ulke_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@ulketv/live"},
    {"name": "Eko Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/52/Ekoturk_logo.png", "group": "Ekonomi", "url": "https://www.youtube.com/@Ekoturktv/live"},
    {"name": "24 TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/1/14/24_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@24tv/live"},
    {"name": "A Spor", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b9/A_Spor_logo.png", "group": "Spor", "url": "https://www.youtube.com/@aspor/live"},
    {"name": "HT Spor", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/5f/HT_Spor_logo.png", "group": "Spor", "url": "https://www.youtube.com/@HTSpor/live"},
    {"name": "TV Net", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/75/TVNET_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tvnet/live"},
    {"name": "Bein Spor Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/37/BeIN_Sports_Haber_logo.png", "group": "Spor", "url": "https://www.youtube.com/@beINSPORTSTurkiye/live"},
    {"name": "CNBC-e", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/30/CNBC-e_2024_logo.png", "group": "Genel", "url": "https://www.youtube.com/@CNBCeTurkiye/live"}
]

# ==================== BİNARY YÖNETİCİLERİ ====================

def ensure_ytdlp():
    """yt-dlp binary dosyasını indirir ve güncel tutar."""
    ytdlp_bin = shutil.which("yt-dlp")
    if ytdlp_bin:
        return ytdlp_bin

    local_ytdlp = os.path.join(os.getcwd(), "yt-dlp")
    if os.path.exists(local_ytdlp):
        return local_ytdlp

    print("⏬ 'yt-dlp' binary bulunamadı, web üzerinden indiriliyor...")
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response, open(local_ytdlp, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(local_ytdlp, 0o755)
        print("✅ 'yt-dlp' başarıyla indirildi.")
        return local_ytdlp
    except Exception as e:
        print(f"❌ 'yt-dlp' indirilemedi: {e}")
        return None

def ensure_git():
    """Git binary'sini web üzerinden indirir (ARM64 Android / Linux uyumlu)."""
    git_bin = shutil.which("git")
    if git_bin:
        return git_bin

    local_git = os.path.join(os.getcwd(), "git")
    if os.path.exists(local_git):
        return local_git

    print("⏬ 'git' binary bulunamadı, web üzerinden indiriliyor...")
    # Android arm64 / Linux static git binary bağlantısı
    url = "https://raw.githubusercontent.com/andrew-d/static-binaries/master/binaries/linux/arm64/git"
    
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response, open(local_git, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(local_git, 0o755)
        print("✅ 'git' binary başarıyla indirildi.")
        return local_git
    except Exception as e:
        print(f"❌ Git indirilemedi: {e}")
        return None

# ==================== AKIŞ VE M3U İŞLEMLERİ ====================

def get_m3u8_ytdlp(ytdlp_path, youtube_url):
    """yt-dlp kullanarak YouTube canlı yayın m3u8 adresini çözer."""
    try:
        cmd = [ytdlp_path, "-g", "-f", "best", youtube_url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        url = result.stdout.strip()
        if url and ".m3u8" in url:
            return url
    except Exception:
        pass
    return None

def get_m3u8_fallback(youtube_url):
    """Urllib ve Regex ile doğrudan m3u8 tespiti yapar."""
    try:
        req = urllib.request.Request(youtube_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            html = response.read().decode('utf-8')
            match = re.search(r'(https://[^\s"\'\\]+\.m3u8[^\s"\'\\]*)', html)
            if match:
                return match.group(1).replace('\\u0026', '&')
    except Exception:
        pass
    return None

def get_m3u8(ytdlp_path, youtube_url):
    if ytdlp_path:
        url = get_m3u8_ytdlp(ytdlp_path, youtube_url)
        if url: return url
    return get_m3u8_fallback(youtube_url)

def safe_filename(name):
    filename = name.lower()
    for tr, en in [('ç','c'), ('ğ','g'), ('ı','i'), ('ö','o'), ('ş','s'), ('ü','u'), (' ','_')]:
        filename = filename.replace(tr, en)
    return re.sub(r'[^a-z0-9_]', '', filename)

# ==================== GIT İŞLEMLERİ ====================

def setup_git_repo(git_cmd):
    """Git repoyu başlatır ve remote url'i ayarlar."""
    try:
        if not os.path.exists(".git"):
            subprocess.run([git_cmd, "init"], check=True, stdout=subprocess.DEVNULL)
            
        subprocess.run([git_cmd, "config", "user.name", "Auto Updater"], stdout=subprocess.DEVNULL)
        subprocess.run([git_cmd, "config", "user.email", "auto@updater.com"], stdout=subprocess.DEVNULL)
        
        remote_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
        
        # Remote önceden eklendiyse sil ve tekrar ekle
        subprocess.run([git_cmd, "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
        subprocess.run([git_cmd, "remote", "add", "origin", remote_url], check=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"⚠️ Git yapılandırma uyarısı: {e}")

def git_commit_and_push(git_cmd):
    """Web'den indirilen git binary'si ile değişiklikleri GitHub'a gönderir."""
    try:
        setup_git_repo(git_cmd)
        
        print("🚀 Git Push İşlemi Başlatılıyor...")
        subprocess.run([git_cmd, "add", "."], check=True)
        
        commit_msg = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run([git_cmd, "commit", "-m", commit_msg], stderr=subprocess.DEVNULL)
        
        # Main dalına push yap
        result = subprocess.run([git_cmd, "push", "-u", "origin", "main", "--force"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("✅ Değişiklikler GitHub'a başarıyla push edildi!")
        else:
            print(f"❌ Git Push Hatası: {result.stderr.strip()}")
    except Exception as e:
        print(f"❌ Git işlemi başarısız oldu: {e}")

# ==================== ANA DÖNGÜ ====================

def run_update():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("==========================================")
    print(f"🔄 Güncelleme Başladı: {now_str}")
    print("==========================================\n")

    ytdlp_path = ensure_ytdlp()
    git_path = ensure_git()

    if not os.path.exists(STREAMS_DIR):
        os.makedirs(STREAMS_DIR)

    playlist_lines = ["#EXTM3U\n"]

    for channel in CHANNELS:
        print(f"➡️  {channel['name']} ... ", end="", flush=True)
        m3u8_url = get_m3u8(ytdlp_path, channel['url'])
        
        if m3u8_url:
            clean_name = safe_filename(channel['name'])
            stream_filename = f"{clean_name}.m3u8"
            stream_filepath = os.path.join(STREAMS_DIR, stream_filename)

            # Özel .m3u8 dosyası oluştur
            with open(stream_filepath, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"#EXT-X-STREAM-INF:PROGRAM-ID=1,NAME=\"{channel['name']}\"\n")
                f.write(f"{m3u8_url}\n")

            # Ana çalma listesi için ekle
            extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
            playlist_lines.append(extinf)
            playlist_lines.append(f"{STREAMS_DIR}/{stream_filename}\n")
            print("✅ OK")
        else:
            print("❌ BAŞARISIZ (Akış alınamadı)")

    # Ana playlist.m3u yaz
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)

    print("\n📁 Güncelleme yerel olarak kaydedildi.")

    # Git ile otomatik Push
    if git_path:
        git_commit_and_push(git_path)
    else:
        print("⚠️ Git indirilemediği için push atılamadı.")

if __name__ == "__main__":
    while True:
        run_update()
        
        next_run = time.strftime('%H:%M:%S', time.localtime(time.time() + 10800))
        print(f"\n😴 3 saatlik uyku moduna geçiliyor. Sonraki çalışma saati: {next_run}\n")
        time.sleep(10800)
