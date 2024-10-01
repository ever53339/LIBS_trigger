import socketio
import pyautogui
import cv2
import numpy as np
import imutils
import eventlet

sio = socketio.Server()
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ, auth):
    print('connect ', sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

@sio.event
def pull_trigger(sid, data):
    x, y = get_button_pos_multi_scale(data)
    pyautogui.click(x, y)
    # print(data)
    return 'ok'

def get_button_pos_multi_scale(button_template_path: str) -> tuple[int]:
    """
    returns the (x, y) coordinates of the center 
    of the requested button in the screen window

    Args:
        button_template_path (str): path to the image file of the button template

    Returns:
        tuple[int]: the (x, y) coordinates of the center of the button
    """
    screenshot = np.array(pyautogui.screenshot())
    gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    template = cv2.imread(button_template_path, cv2.IMREAD_GRAYSCALE) # return shape(height * width, y * x)
    template = cv2.Canny(template, 50, 200)
    (template_height, template_width) = template.shape[:2]

    found = None
    # loop over the scales of the image
    for scale in np.linspace(0.2, 2.0, 10)[::-1]:
        # resize the image according to the scale, and keep track
        # of the ratio of the resizing
        resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
        r = gray.shape[1] / float(resized.shape[1])
        # if the resized image is smaller than the template, then break
        # from the loop
        if resized.shape[0] < template_height or resized.shape[1] < template_width:
            break
        
        # detect edges in the resized, grayscale image and apply template
        # matching to find the template in the image
        edged = cv2.Canny(resized, 50, 200)
        result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
        (_, max_val, _, max_loc) = cv2.minMaxLoc(result)
        # # check to see if the iteration should be visualized
        # if args.get("visualize", False):
        #     # draw a bounding box around the detected region
        #     clone = np.dstack([edged, edged, edged])
        #     cv2.rectangle(clone, (max_loc[0], max_loc[1]),
        #         (max_loc[0] + template_width, max_loc[1] + template_height), (0, 0, 255), 2)
        #     cv2.imshow("Visualize", clone)
        #     cv2.waitKey(0)
        # if we have found a new maximum correlation value, then update
        # the bookkeeping variable
        if found is None or max_val > found[0]:
            found = (max_val, max_loc, r)
    # unpack the bookkeeping variable and compute the (x, y) coordinates
    # of the bounding box based on the resized ratio
    (_, max_loc, r) = found
    (start_x, start_y) = (int(max_loc[0] * r), int(max_loc[1] * r))
    (end_x, end_y) = (int((max_loc[0] + template_width) * r), int((max_loc[1] + template_height) * r))
    
    # draw a bounding box around the detected result and display the image
    # cv2.rectangle(screenshot, (start_x, start_y), (end_x, end_y), (0, 0, 255), 2)
    # cv2.imshow("Image", screenshot)
    # cv2.waitKey(0)

    return (start_x + end_x) // 2, (start_y + end_y) // 2

eventlet.wsgi.server(eventlet.listen(('', 1234)), app)