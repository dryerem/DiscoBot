from datetime import datetime

import pytube
import youtube_dl
import pafy


def pytube_score(url: str):
    audio_url:str = pytube.YouTube(url='https://youtu.be/J0y6wM0aAgE').streams.get_audio_only().url
    print("pytube: ", audio_url)

def ytdl_score(url: str):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        info: dict = ydl.extract_info(url, download=False)
        print("ytdl: ", info.get('url'))

def pafy_score(url: str):
    video = pafy.new(url)
    bestaudio = video.getbestaudio()
    print("pafy: ", bestaudio.url)


if __name__ == "__main__":
    url: str = 'https://youtu.be/J0y6wM0aAgE'

    start_time: datetime = datetime.now()
    pytube_score(url=url)
    end_time: datetime =  datetime.now() - start_time
    print(f"pytube_score: {end_time}\n")

    start_time: datetime = datetime.now()
    ytdl_score(url=url)
    end_time: datetime = datetime.now() - start_time
    print(f"ytdl_score: {end_time}\n")

    start_time: datetime = datetime.now()
    pafy_score(url=url)
    end_time: datetime = datetime.now() - start_time
    print(f"pafy_score: {end_time}")
