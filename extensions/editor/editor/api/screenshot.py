"""Screenshotting utility for the editor."""

DEFAULT_SCREENSHOT_DIR = '/static/img/_screenshot'
WAIT_TIMEOUT = 10


class ScreenshotResolution:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    @property
    def resolution(self):
        return f'{self.width}x{self.height}'

    def filename(self, base):
        return f'{base}-{self.width}x{self.height}.png'
