class Logger():
    "Simple logger for youtube-dl"
    def debug(self, msg):
        "Debug case"
        pass

    def warning(self, msg):
        "Warning case"
        pass

    def error(self, msg):
        "Error case"
        print(msg)


def hook(d):
    "Simple hook"
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

DOWNLOAD_OPTIONS = {
    'format': 'worstaudio/worst',
    'keepvideo': True,
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': '16'}],
    'logger': Logger(),
    'progress_hooks': [hook],
    'outtmpl': '%(id)s.%(ext)s'
}
