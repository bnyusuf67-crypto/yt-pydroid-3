#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import shutil
import gc
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# -------------------- REPO VE GİT AYARLARI --------------------
# Standart ve güvenli repo URL'si
GITHUB_REPO_URL = "https://github.com/bnyusuf67-crypto/youtube-iptv.git"

# -------------------- KANAL LİSTESİ --------------------
kanallar = [
    {"slug": "trthaber", "name": "TRT Haber", "youtube_url": "https://www.youtube.com/@trthaber/live"},
    {"slug": "cnnturk", "name": "CNN Turk", "youtube_url": "https://www.youtube.com/@cnnturk/live"},
    {"slug": "ntv", "name": "NTV", "youtube_url": "https://www.youtube.com/@ntv/live"},
    {"slug": "ahaber", "name": "A Haber", "youtube_url": "https://www.youtube.com/@Ahaber/live"},
    {"slug": "haberturk", "name": "Haber Turk", "youtube_url": "https://www.youtube.com/@haberturktv/live"},
    {"slug": "halktv", "name": "Halk TV", "youtube_url": "https://www.youtube.com/@Halktvkanali/live"},
    {"slug": "sozcutelevizyonu", "name": "Sozcu TV", "youtube_url": "https://www.youtube.com/@sozcutelevizyonu/live"},
    {"slug": "tgrthaber", "name": "TGRT Haber", "youtube_url": "https://www.youtube.com/@tgrthaber/live"},
    {"slug": "flashhaber", "name": "Flash Haber", "youtube_url": "https://www.youtube.com/@flashhabertv/live"},
    {"slug": "haberglobal", "name": "Haber Global", "youtube_url": "https://www.youtube.com/@haberglobal/live"},
    {"slug": "tv100", "name": "TV 100", "youtube_url": "https://www.youtube.com/@tv100/live"},
    {"slug": "bloomberght", "name": "Bloomberg HT", "youtube_url": "https://www.youtube.com/@bloomberght/live"},
    {"slug": "benguturk", "name": "Bengu Turk", "youtube_url": "https://www.youtube.com/@tvbenguturk/live"},
    {"slug": "krttv", "name": "KRT TV", "youtube_url": "https://www.youtube.com/@krtcanli/live"},
    {"slug": "ulusalkanal", "name": "Ulusal Kanal", "youtube_url": "https://www.youtube.com/@ulusalkanaltv/live"},
    {"slug": "ulketv", "name": "Ulke TV", "youtube_url": "https://www.youtube.com/@ulketv/live"},
    {"slug": "ekoturk", "name": "Eko Turk", "youtube_url": "https://www.youtube.com/@ekoturktv/live"},
    {"slug": "tv24", "name": "24 TV", "youtube_url": "https://www.youtube.com/@YirmidortTV/live"},
    {"slug": "aspor", "name": "A Spor", "youtube_url": "https://www.youtube.com/@aspor/live"},
    {"slug": "htspor", "name": "HT Spor", "youtube_url": "https://www.youtube.com/@htspor/live"},
    {"slug": "tvnet", "name": "TV Net", "youtube_url": "https://www.youtube.com/@tvnet/live"},
    {"slug": "beinsportshaber", "name": "Bein Spor Haber", "youtube_url": "https://www.youtube.com/@beINSPORTSTurkiye/live"},
    {"slug": "cnbce", "name": "CNBC-e", "youtube_url": "https://www.youtube.com/@cnbce/live"}
]

# -------------------- GENEL AYARLAR --------------------
STREAMS_DIR = "streams"
PLAYLIST_FILE = "playlist.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
YT_DLP_TIMEOUT = 45
BEKLEME_SURESI_SANIYE = 3 * 60 * 60  # 3 Saat (10800 saniye)

def ensure_ytdlp():
    """System path üzerinde yoksa standalone yt-dlp binary'sini web'den indirir."""
    yt_bin = shutil.which("yt-dlp")
    if yt_bin:
        return yt_bin

    local_yt = os.path.join(os.getcwd(), "yt-dlp")
    if os.path.exists(local_yt):
        return local_yt

    print("⚠️ 'yt-dlp' bulunamadı, indiriliyor...")
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response, open(local_yt, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        os.chmod(local_yt, 0o755)
        print("✅ 'yt-dlp' indirildi.")
        return local_yt
    except Exception as e:
        print(f"❌ yt-dlp indirilemedi: {e}")
        sys.exit(1)

def get_manifest_url_via_json(yt_bin, youtube_url):
    """-J ile analiz eder, google manifest veya hls variant linkini döner."""
    try:
        cmd = [yt_bin, "-J", "--no-warnings", youtube_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=YT_DLP_TIMEOUT)
        
        if result.returncode != 0:
            return None, f"yt-dlp hata verdi: {result.stderr.strip()[:80]}"

        data = json.loads(result.stdout)
        
        manifest_url = data.get("manifest_url")
        if manifest_url and "googlevideo.com" in manifest_url:
            return manifest_url, None

        formats = data.get("formats", [])
        best_hls = None
        for fmt in formats:
            url = fmt.get("url", "")
            if "googlevideo.com" in url and "m3u8" in url:
                if fmt.get("vcodec") != "none":
                    best_hls = url
                    break
        
        if best_hls:
            return best_hls, None

        if manifest_url:
            return manifest_url, None

        return None, "HLS Manifest URL bulunamadı."

    except subprocess.TimeoutExpired:
        return None, "Zaman aşımı"
    except Exception as e:
        return None, str(e)

def download_m3u8_content(url):
    """urllib ile m3u8 içeriğini çeker."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

def write_channel_file(slug, name, m3u8_content, manifest_url):
    filepath = os.path.join(STREAMS_DIR, f"{slug}.m3u8")
    with open(filepath, "w", encoding="utf-8") as f:
        if m3u8_content:
            f.write(m3u8_content)
        else:
            f.write(f"#EXTM3U\n#EXTINF:-1 tvg-name=\"{name}\",{name}\n{manifest_url}\n")

def setup_git_repository():
    try:
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True)

        subprocess.run(["git", "config", "credential.helper", "store"], check=True)
        subprocess.run(["git", "config", "user.name", "Pydroid IPTV Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "pydroid@iptv.local"], check=True)

        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout.splitlines()
        if "origin" in remotes:
            subprocess.run(["git", "remote", "set-url", "origin", GITHUB_REPO_URL], check=True)
        else:
            subprocess.run(["git", "remote", "add", "origin", GITHUB_REPO_URL], check=True)

    except Exception as e:
        print(f"⚠️ Git konfigürasyon uyarısı: {e}")

def git_push():
    try:
        setup_git_repository()

        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("📭 Değişiklik yok, push atlanıyor.")
            return

        subprocess.run(["git", "add", "-A"], check=True)
        commit_msg = f"Auto update streams - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)

        branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = branch_res.stdout.strip() or "main"

        print(f"🚀 Repoya ({branch} dalı) push yapılıyor...")
        subprocess.run(["git", "push", "origin", branch], check=True)
        print("✅ Push tamamlandı!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git Push Hatası: {e}")
    except Exception as e:
        print(f"❌ Hata: {e}")

def guncelleme_dONGUSU():
    yt_bin = ensure_ytdlp()
    os.makedirs(STREAMS_DIR, exist_ok=True)
    
    while True:
        simdi = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n==========================================")
        print(f"🔄 Güncelleme Başladı: {simdi}")
        print(f"==========================================\n")

        ana_m3u = "#EXTM3U\n"

        for slug, isim, url in kanallar:
            print(f"➡️  {isim} ... ", end="", flush=True)
            
            manifest_url, hata = get_manifest_url_via_json(yt_bin, url)
            if not manifest_url:
                print(f"❌ {hata}")
                continue

            m3u8_content = download_m3u8_content(manifest_url)
            write_channel_file(slug, isim, m3u8_content, manifest_url)
            ana_m3u += f'#EXTINF:-1 tvg-name="{isim}" group-title="Canlı" http-user-agent="{USER_AGENT}",{isim}\n{manifest_url}\n'
            print("✅ OK")

        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.write(ana_m3u)

        print(f"\n📁 Güncelleme yerel olarak kaydedildi.")
        git_push()

        # Bellek Temizliği (Arka planda RAM şişmesini önler)
        gc.collect()

        # 3 Saat Bekleme Süresi
        sonraki = datetime.fromtimestamp(time.time() + BEKLEME_SURESI_SANIYE).strftime('%H:%M:%S')
        print(f"\n😴 3 saatlik uyku moduna geçiliyor. Sonraki çalışma saati: {sonraki}")
        time.sleep(BEKLEME_SURESI_SANIYE)

if __name__ == "__main__":
    guncelleme_dONGUSU()
