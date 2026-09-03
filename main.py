import urllib.request
import re
import os
import time
import subprocess
import json
import shutil
import base64
from datetime import datetime

# ==================== YAPILANDIRMA ====================
PLAYLIST_FILE = "playlist.m3u"
STREAMS_DIR = "streams"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FETCH_TIMEOUT = 15

# GITHUB BİLGİLERİNİZ
GITHUB_USER = "KULLANICI_ADINIZ"
GITHUB_REPO = "youtube-iptv"
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Personal Access Token
BRANCH = "main"

# KANAL LİSTESİ (YZ'nin verdiği linklerden birkaçı canlı olanlarla restore edildi.)
CHANNELS = [
    {"name": "TRT Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/2/29/TRT_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@trthaber/live"},
    {"name": "CNN Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b2/CNN_Turk_logo.png", "group": "Haber", "url": "https://www.youtube.com/@cnnturk/live"},
    {"name": "NTV", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d7/NTV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@NTV/live"},
    {"name": "A Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/8/87/A_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@ahaber/live"},
    {"name": "Haber Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/07/Haberturk_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@HaberturkTV/live"},
    {"name": "Halk TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/dc/Halk_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@Halktvkanali/live"},
    {"name": "Sozcu TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Sozcu_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/watch?v=ztmY_cCtUl0"},
    {"name": "TGRT Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/TGRT_Haber_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tgrthaber/live"},
    {"name": "Flash Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/08/Flash_Haber_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@FlashHaberTV/live"},
    {"name": "Haber Global", "logo": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Haber_Global_logo.png", "group": "Haber", "url": "https://www.youtube.com/@haberglobal/live"},
    {"name": "TV 100", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/7b/TV100_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tv100/live"},
    {"name": "Bloomberg HT", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Bloomberg_HT_logo.png", "group": "Ekonomi", "url": "https://www.youtube.com/@bloomberght/live"},
    {"name": "Bengu Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Bengu_Turk_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tvbenguturk/live"},
    {"name": "KRT TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/2/23/KRT_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@krttv/live"},
    {"name": "Ulusal Kanal", "logo": "https://upload.wikimedia.org/wikipedia/commons/a/a8/Ulusal_Kanal_logo.png", "group": "Haber", "url": "https://www.youtube.com/@UlusalKanalTV/live"},
    {"name": "Ulke TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Ulke_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@ulketv/live"},
    {"name": "Eko Turk", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/52/Ekoturk_logo.png", "group": "Ekonomi", "url": "https://www.youtube.com/@ekoturktv/live"},
    {"name": "24 TV", "logo": "https://upload.wikimedia.org/wikipedia/commons/1/14/24_TV_logo.png", "group": "Haber", "url": "https://www.youtube.com/@YirmidortTV/live"},
    {"name": "A Spor", "logo": "https://upload.wikimedia.org/wikipedia/commons/b/b9/A_Spor_logo.png", "group": "Spor", "url": "https://www.youtube.com/@aspor/live"},
    {"name": "HT Spor", "logo": "https://upload.wikimedia.org/wikipedia/commons/5/5f/HT_Spor_logo.png", "group": "Spor", "url": "https://www.youtube.com/@HTSpor/live"},
    {"name": "TV Net", "logo": "https://upload.wikimedia.org/wikipedia/commons/7/75/TVNET_logo.png", "group": "Haber", "url": "https://www.youtube.com/@tvnet/live"},
    {"name": "Bein Spor Haber", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/37/BeIN_Sports_Haber_logo.png", "group": "Spor", "url": "https://www.youtube.com/@beINSPORTSTurkiye/live"},
    {"name": "CNBC-e", "logo": "https://upload.wikimedia.org/wikipedia/commons/3/30/CNBC-e_2024_logo.png", "group": "Genel", "url": "https://www.youtube.com/@cnbce/live"}
]

# ==================== WEB BINARY İNDİRİCİSİ ====================

def ensure_ytdlp():
    """yt-dlp binary dosyasını kontrol eder veya indirir."""
    ytdlp_bin = shutil.which("yt-dlp")
    if ytdlp_bin:
        return ytdlp_bin

    local_ytdlp = os.path.join(os.getcwd(), "yt-dlp")
    if os.path.exists(local_ytdlp):
        return local_ytdlp

    print("⏬ 'yt-dlp' indiriliyor...")
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response, open(local_ytdlp, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(local_ytdlp, 0o755)
        print("✅ 'yt-dlp' indirildi.")
        return local_ytdlp
    except Exception as e:
        print(f"❌ 'yt-dlp' indirilemedi: {e}")
        return None

# ==================== MANIFEST & HLS VARIANT AYRIŞTIRMA ====================

def get_variant_m3u8_url(ytdlp_path, youtube_url):
    """
    yt-dlp ile JSON verisini çeker. Master manifest içindeki doğrudan oynatılabilir
    HLS variant (çözünürlük/stream) URL'sini elde eder (.ts parçaları içermez).
    """
    try:
        cmd = [ytdlp_path, "--dump-single-json", "--no-warnings", youtube_url]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=25)
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            
            Doğrudan master manifest URL'si
            manifest = data.get("manifest_url")
            if manifest and ".m3u8" in manifest:
                return manifest
    except Exception:
        pass
    return None

def fetch_m3u8_content(m3u8_url):
    """
    Elde edilen HLS variant M3U8 URL'sine istek atıp içeriği metin olarak indirir.
    .ts parçalarını ayıklamak yerine yayın bilgisinin geçerliliğini doğrular.
    """
    try:
        req = urllib.request.Request(m3u8_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            content = response.read().decode('utf-8', errors='ignore')
            if "#EXTM3U" in content:
                return content
    except Exception:
        pass
    return None

def safe_filename(name):
    filename = name.lower()
    for tr, en in [('ç','c'), ('ğ','g'), ('ı','i'), ('ö','o'), ('ş','s'), ('ü','u'), (' ','_')]:
        filename = filename.replace(tr, en)
    return re.sub(r'[^a-z0-9_]', '', filename)

# ==================== GITHUB REST API UPLOAD ====================

def github_upload_file(file_path):
    """Hazırlanan M3U ve M3U8 dosyalarını doğrudan GitHub REST API ile depoya yükler."""
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_path}"
    
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
        
    sha = None
    req_get = urllib.request.Request(
        url, 
        headers={"Authorization": f"token {GITHUB_TOKEN}", "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req_get) as response:
            data = json.loads(response.read().decode())
            sha = data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  ⚠️ SHA alınamadı ({file_path}): {e}")

    payload = {
        "message": f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    req_put = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        },
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req_put) as response:
            if response.status in (200, 201):
                print(f"  ☁️ {file_path} GitHub'a yüklendi.")
    except Exception as e:
        print(f"  ❌ {file_path} yüklenemedi: {e}")

def push_all_to_github():
    """Tüm güncellenen dosyaları GitHub reposuna gönderir."""
    print("\n🚀 GitHub API ile Senkronizasyon Başlatılıyor...")
    
    if os.path.exists(PLAYLIST_FILE):
        github_upload_file(PLAYLIST_FILE)

    if os.path.exists(STREAMS_DIR):
        for fname in os.listdir(STREAMS_DIR):
            if fname.endswith(".m3u8"):
                fpath = os.path.join(STREAMS_DIR, fname)
                github_upload_file(fpath)

# ==================== ANA DÖNGÜ ====================

def run_update():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("==========================================")
    print(f"🔄 Güncelleme Başladı: {now_str}")
    print("==========================================\n")

    ytdlp_path = ensure_ytdlp()

    if not os.path.exists(STREAMS_DIR):
        os.makedirs(STREAMS_DIR)

    playlist_lines = ["#EXTM3U\n"]

    for channel in CHANNELS:
        print(f"➡️  {channel['name']} ... ", end="", flush=True)
        
        # 1. Manifest / HLS variant m3u8 URL'sini al
        m3u8_variant_url = get_variant_m3u8_url(ytdlp_path, channel['url'])
        
        if m3u8_variant_url:
            # 2. HLS variant URL'sinin içeriğini web'den indir
            m3u8_content = fetch_m3u8_content(m3u8_variant_url)
            
            clean_name = safe_filename(channel['name'])
            stream_filename = f"{clean_name}.m3u8"
            stream_filepath = os.path.join(STREAMS_DIR, stream_filename)

            # M3U8 dosyasını yerel yerleşkeye yaz
            with open(stream_filepath, "w", encoding="utf-8") as f:
                if m3u8_content:
                    f.write(m3u8_content)
                else:
                    f.write("#EXTM3U\n")
                    f.write(f"#EXT-X-STREAM-INF:PROGRAM-ID=1,NAME=\"{channel['name']}\"\n")
                    f.write(f"{m3u8_variant_url}\n")

            extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
            playlist_lines.append(extinf)
            playlist_lines.append(f"{STREAMS_DIR}/{stream_filename}\n")
            print("✅ OK")
        else:
            print("❌ BAŞARISIZ (Akış bulunamadı)")

    # Ana playlist.m3u oluştur
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)

    print("\n📁 Güncelleme yerel olarak kaydedildi.")

    # GitHub REST API Push
    push_all_to_github()

if __name__ == "__main__":
    while True:
        run_update()
        
        next_run = time.strftime('%H:%M:%S', time.localtime(time.time() + 10800))
        print(f"\n😴 3 saatlik uyku moduna geçiliyor. Sonraki çalışma saati: {next_run}\n")
        time.sleep(10800)
