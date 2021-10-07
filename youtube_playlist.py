from threading import Thread

import pafy
from googleapiclient.discovery import build


thread_tasks: list = []
result: list = []


def get_pid(url: str):
    """Receives a link to the playlist as input and returns its identifier"""

    pid: str = ''
    for s in url[::-1]:
        if s == '=':
            break
        pid += s
    pid = pid[::-1]

    return pid

def track_url(video_url: str, title: str):
    """gets a link to a track"""

    url: str = pafy.new(video_url).getbestaudio().url
    result.append((url, title))

def create_tasks(request):
    """Creates tasks to get a direct link to each element of the playlist and form a playlist"""

    for item in request['items']:
        snippet: dict = item['snippet']
        title: str = snippet['title']
        video_id: str = snippet['resourceId']['videoId']
        video_url: str = f'https://www.youtube.com/watch?v={video_id}'

        thread_tasks.append(Thread(target=track_url, args=(video_url, title)))    

def playlist_parse(url: str, token: str):
    """Returns a list of cots containing the title and link to each video in the playlist"""

    if result:
        result.clear()

    youtube = build('youtube', 'v3', developerKey=token)

    playlist_id: str = get_pid(url)

    request = youtube.playlistItems().list(playlistId=playlist_id, 
            part='snippet', maxResults=50) 
    request = request.execute()

    next_page_token = request.get('nextPageToken')

    # Playlist has less than 50 items
    if next_page_token is None:        
        create_tasks(request)

    # There are more than 50 items in the playlist 
    while 'nextPageToken' in request:
        request = youtube.playlistItems().list(playlistId=playlist_id, 
                part='snippet', maxResults=50, pageToken=next_page_token) 
        request = request.execute()

        create_tasks(request)

        if 'nextPageToken' not in request:
            request.pop('nextPageToken', None)
        else:
            next_page_token = request['nextPageToken']

    [task.start() for task in thread_tasks]
    [task.join() for task in thread_tasks]
    thread_tasks.clear()

    return result


if __name__ == '__main__':
    """Here's the tests"""

    from datetime import datetime
    from configparser import ConfigParser
    from sys import argv, exit
    from os import path

    file_config: str = None
    for iter, arg in enumerate(argv):
        if arg == '--config':
            file_config = argv[iter + 1]
    
    config: ConfigParser = ConfigParser()
    if file_config:
        if path.isfile(file_config):
            config.read(file_config)
        else:
            print("File config not found!")
            exit(1)
    else:
        start_path: str = path.abspath(path.dirname(__file__))
        file_config = path.normpath(path.join(start_path, 'config.ini'))
        if path.isfile(file_config):
            config.read(file_config)
        else:
            print("File config not found!")
            exit(1)

    token: str = config['Youtube']['token']
    
    # Playlist has less than 50 items 
    url: str = 'https://youtube.com/playlist?list=PLxoVxR2_avl_sPsQljlyjhBRFc9_I6RGJ'
    if 'list=' in url:
        start_time: datetime = datetime.now()

        playlist_parse(url, token)

        end_time: datetime =  datetime.now() - start_time
        print(f"[TEST 1] - score: {end_time}\n")

    # There are more than 50 items in the playlist 
    url: str = 'https://youtube.com/playlist?list=PLQOaTSbfxUtD6kMmAYc8Fooqya3pjLs1N'
    if 'list=' in url:
        start_time: datetime = datetime.now()

        playlist_parse(url, token)

        end_time: datetime =  datetime.now() - start_time
        print(f"[TEST 2] - score: {end_time}\n")