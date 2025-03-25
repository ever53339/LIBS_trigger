from calendar import TUESDAY
import socketio
import pyautogui
import cv2
import numpy as np
import imutils
import eventlet
from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
from enum import Enum
import time
import threading
from libs_analyzer import LIBSAnalyzer, AnalyzerStatus, DeviceRunningError, ButtonNotFoundError, UnkonwnButtonNameError

class Z300WebServer:
    """
    A socket.io server class for the SciAps Z300 LIBS gun based on GUI automation.
    """
    def __init__(self):
        self.sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
        self.app = socketio.WSGIApp(self.sio)

        # self.libs_analyzer = LIBSAnalyzer(cache_folder_path='C:/Users/LIBS_VM/sciaps/cache', export_folder_path='Y:/')
        self.libs_analyzer = LIBSAnalyzer(cache_folder_path='C:/Users/Whittaker Lab/sciaps/cache', export_folder_path='C:/Users/Whittaker Lab/Documents/LIBS_auto_export')

        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        # self.sio.on('pull_trigger', self.on_pull_trigger)
        # self.sio.on('set_desktop_id', self.on_set_desktop_id)
        self.sio.on('measure', self.on_measure)
        self.sio.on('export', self.on_export)
        self.sio.on('analyze', self.on_analyze)

    def on_connect(self, sid, environ, auth):
        print('connect ', sid)

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    def on_measure(self, sid, data):
        if self.libs_analyzer.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                self.libs_analyzer.measure()
            except Exception as e:
                return str(e)
            else:
                return 'measurement done successfully'
    
    def on_export(self, sid, data):
        if self.libs_analyzer.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                self.libs_analyzer.export()
            except Exception as e:
                return str(e)
            else:
                return 'export done successfully'
    
    def on_analyze(self, sid, data):
        if self.libs_analyzer.status == AnalyzerStatus.RUNNING:
            return 'The analyzer is currently running. Please wait until it is done.'
        else:
            try:
                res = self.libs_analyzer.analyze()
            except Exception as e:
                return str(e)
            else:
                return res

    # def on_set_desktop_id(self, sid, data):
    #     self.desktop_id = data
    #     print(f'Virtual desktop id for Profile Builder has been set to {self.desktop_id}.')

    def update_status(self):
        while True:
            self.sio.sleep(0.5)
            self.sio.emit('status', self.libs_analyzer.status.name)
        

if __name__ == '__main__':
    z300_web_server = Z300WebServer()
    z300_web_server.sio.start_background_task(z300_web_server.update_status)
    eventlet.wsgi.server(eventlet.listen(('', 1234)), z300_web_server.app)


