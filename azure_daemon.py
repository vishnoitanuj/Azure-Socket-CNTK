import cv2
import json
import time
import threading
import logging.config
from devicehive_webconfig import Server, Handler

# from models.yolo import Yolo2Model
from utils.general import format_predictions, format_notification
from web.routes import routes
from log_config import LOGGING

##Azure
import requests
from PIL import Image
from io import BytesIO
##

##
import time 
from time import sleep 
from sinchsms import SinchSMS 
from multiprocessing import Process
##

logging.config.dictConfig(LOGGING)

logger = logging.getLogger('detector')

##
subscription_key = "f9ab31f762d440a789fb4164132a7471"
assert subscription_key

vision_base_url = "https://centralindia.api.cognitive.microsoft.com/vision/v2.0/"
analyze_url = vision_base_url + "analyze"

headers    = {'Ocp-Apim-Subscription-Key': subscription_key,
                'Content-Type': 'application/octet-stream'}
params     = {'visualFeatures': 'Categories,Description,Color'}
    
##

class DeviceHiveHandler(Handler):
    _device = None

    def handle_connect(self):
        self._device = self.api.put_device(self._device_id)
        super(DeviceHiveHandler, self).handle_connect()

    def send(self, data):
        if isinstance(data, str):
            notification = data
        else:
            try:
                notification = json.dumps(data)
            except TypeError:
                notification = str(data)

        self._device.send_notification(notification)

f=0

class Daemon(Server):
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, cv2.COLOR_LUV2LBGR]

    _detect_frame_data = None
    _detect_frame_data_id = None
    _cam_thread = None

    def __init__(self, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self._detect_frame_data_id = 0
        self._cam_thread = threading.Thread(target=self._cam_loop, name='cam')
        self._cam_thread.setDaemon(True)

    def _on_startup(self):
        self._cam_thread.start()

    def _cam_loop(self):
        logger.info('Start camera loop')
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise IOError('Can\'t open "{}"'.format(0))

        source_h = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
        source_w = cam.get(cv2.CAP_PROP_FRAME_WIDTH)

        # model = Yolo2Model(input_shape=(source_h, source_w, 3))
        # model.init()
        # image_path = "check.jpeg"

        start_time = time.time()
        frame_num = 0
        fps = 0
        f=0
        try:
            while self.is_running:
                ret, frame = cam.read()
                cv2.imwrite('check.jpeg', frame)
                image_path = 'check.jpeg'

                # Read the image into a byte array
                image_data = open(image_path, "rb").read()

                if not ret:
                    logger.warning('Can\'t read video data')
                    continue

                response = requests.post(
                    analyze_url, headers=headers, params=params, data=image_data)
                response.raise_for_status()
                analysis = response.json()
                try:
                    image_caption = analysis["description"]["captions"][0]["text"].capitalize()
                    tags = analysis["description"]["tags"]
                    if 'man' in tags and f==0:
                        f=1
                        number = '918826022510'
                        app_key = 'e31dabc6-aa8d-46bb-aab8-bfb91b58d13c'
                        app_secret = 'J7js1xm+m0665hYgrzW6+w=='

                        # enter the message to be sent 
                        message = 'Alert Triggered'

                        client = SinchSMS(app_key, app_secret) 
                        print("Sending '%s' to %s" % (message, number)) 

                        response = client.send_message(number, message) 
                        message_id = response['messageId'] 
                        response = client.check_status(message_id) 

                        # keep trying unless the status retured is Successful 
                        while response['status'] != 'Successful': 
                            print(response['status']) 
                            time.sleep(1) 
                            response = client.check_status(message_id) 

                        print(response['status'])
                    else:
                        print("wbbb")
                except:
                    print("Exception occured")
                # Draw label
                # (test_width, text_height), baseline = cv2.getTextSize(
                #     image_caption, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 1)
                # end_time = time.time()
                # fps = fps * 0.9 + 1/(end_time - start_time) * 0.1
                # start_time = end_time

                # Draw additional info
                frame_info = 'Frame: {0}, FPS: {1:.2f}'.format(frame_num, fps)
                cv2.putText(frame, image_caption, (10, frame.shape[0]-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)

                self._detect_frame_data_id = frame_num
                _, img = cv2.imencode('.jpg', frame, self.encode_params)
                self._detect_frame_data = img

                frame_num += 1
                image_caption = ""

        finally:
            cam.release()
            # model.close()

    def _send_dh(self, data):
        if not self.dh_status.connected:
            logger.error('Devicehive is not connected')
            return

        self.deviceHive.handler.send(data)

    def get_frame(self):
        return self._detect_frame_data, self._detect_frame_data_id
    
    def find_match(list_of_tags):
        word='man'
        if word in list_of_tags:
            return True
        else:
            return False

if __name__ == '__main__':
    server = Daemon(DeviceHiveHandler, routes=routes)
    server.start()
