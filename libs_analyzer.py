import numpy as np
import cv2
import imutils
import pyautogui
import os
from enum import Enum
import time
from typing import Tuple, List, Dict


class AnalyzerStatus(Enum):
    IDLE = 1
    RUNNING = 2

class DeviceRunningError(Exception):
    """Exception raised when an operation is attempted while the analyzer is running."""
    def __init__(self, message: str = 'The analyzer is currently running. Please wait until it is done.') -> None:
        self.message = message
        super().__init__(self.message)

class ButtonNotFoundError(Exception):
    """Exception raised when a press-button is requested but the button has not been found."""
    def __init__(self, message: str = 'The button was not found.') -> None:
        self.message = message
        super().__init__(self.message)

class UnkonwnButtonNameError(Exception):
    """Exception raised when an unknown button name is provided."""
    def __init__(self, message: str = 'The button name is unknown.') -> None:
        self.message = message
        super().__init__(self.message)

class LIBSAnalyzer:
    """Base driver class for the SciAps Z300 LIBS analyzer based on GUI automation."""

    def __init__(self, cache_folder_path: str, export_folder_path: str, measure_button_img_path: str = 'measure_button.png', export_button_img_path: str = 'export_button.png') -> None:
        """
        Initialize the LIBSAnalyzer.

        Args:
            cache_folder_path (str): Path to the folder where the analyzer stores measurement cache files.
            export_folder_path (str): Path to the folder where to store the exported data.
            measure_button_img_path (str, optional): Path to the image of the measurement button. Defaults to 'measure_button.png'.
            export_button_img_path (str, optional): Path to the image of the export button. Defaults to 'export_button.png'.
        """
        self.cache_folder_path = cache_folder_path
        self.export_folder_path = export_folder_path
        self.buttons = {
            'measure': {
                'pos': None,
                'found': False,
                'img_path': measure_button_img_path
            },
            'export': {
                'pos': None,
                'found': False,
                'img_path': export_button_img_path
            }
        }
        self.status = AnalyzerStatus.IDLE
        self.find_all_buttons()

    def measure(self) -> None:
        """
        Perform a measurement operation.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested measurement operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            try:
                n = len(os.listdir(self.cache_folder_path))
                self.press_a_button('measure')          
            except Exception as e:
                print(e)
                raise
            else:
                # check the number of files and folders in the cache folder
                # if the number of files and folders increased, then the measurement is done
                while len(os.listdir(self.cache_folder_path)) == n:
                    time.sleep(0.5)
            finally:
                self.status = AnalyzerStatus.IDLE
        
    def export(self) -> None:
        """
        Perform an export operation.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested export operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            try:
                self.press_a_button('export')
                # todo: complete export operation
            except Exception as e:
                print(e)
                raise
            finally:
                self.status = AnalyzerStatus.IDLE
    
    def analyze(self) -> List[float]:
        """
        Perform an analysis operation.

        Returns:
            List[float]: The analysis results.

        Raises:
            DeviceRunningError: If the analyzer is currently running.
        """
        if self.status is not AnalyzerStatus.IDLE:
            raise DeviceRunningError('The analyzer is currently running. Please wait until it is done. The requested analysis operation cannot be performed.')
        else:
            self.status = AnalyzerStatus.RUNNING
            try:
                res = self.find_all_peaks('foo.csv')
            except Exception as e:
                print(e)
                raise
            else:
                return res
            finally:
                self.status = AnalyzerStatus.IDLE

    def press_a_button(self, button_name: str) -> None:
        """
        Press the button with the given name.

        Args:
            button_name (str): The name of the button to press.

        Raises:
            UnkonwnButtonNameError: If the button name is unknown.
            ButtonNotFoundError: If the button is not found.
        """
        if button_name not in self.buttons:
            raise UnkonwnButtonNameError(f'The button name {button_name} is unknown.')
        elif not self.buttons[button_name]['found']:
            raise ButtonNotFoundError(f'The button {button_name} was not found.')
        else:
            pyautogui.click(self.buttons[button_name]['pos'])

    def find_all_buttons(self) -> None:
        """
        Find all buttons on the screen.
        """
        for button in self.buttons:
            self.buttons[button]['pos'] = self.locate_button_multi_scale(self.buttons[button]['img_path'])
            self.buttons[button]['found'] = True

    def locate_button_multi_scale(self, button_template_path: str) -> Tuple[int, int]:
        """
        Locate the button on the screen using multi-scale template matching.

        Args:
            button_template_path (str): Path to the image file of the button template.

        Returns:
            Tuple[int, int]: The (x, y) coordinates of the center of the button.
        """
        screenshot = pyautogui.screenshot()
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        template = cv2.imread(button_template_path, cv2.IMREAD_GRAYSCALE) # return shape(height * width, y * x)
        template = cv2.Canny(template, 50, 200)
        (template_height, template_width) = template.shape[:2]

        found = None
        # loop over the scales of the image
        for scale in np.linspace(0.2, 2.0, 10)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            resized = imutils.resize(screenshot_gray, width = int(screenshot_gray.shape[1] * scale))
            r = screenshot_gray.shape[1] / float(resized.shape[1])
            # if the resized image is smaller than the template, then break
            # from the loop
            if resized.shape[0] < template_height or resized.shape[1] < template_width:
                break
            
            # detect edges in the resized, grayscale image and apply template
            # matching to find the template in the image
            edged = cv2.Canny(resized, 50, 200)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
            (_, max_val, _, max_loc) = cv2.minMaxLoc(result)

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
        cv2.rectangle(screenshot_gray, (start_x, start_y), (end_x, end_y), (0, 0, 255), 2)
        cv2.imshow(button_template_path, screenshot_gray)
        cv2.waitKey(0)
        self.detected_x, self.detected_y = (start_x + end_x) // 2, (start_y + end_y) // 2
        # self.button_detected = True
        return self.detected_x, self.detected_y

    def find_all_peaks(self, csv_file_path: str) -> List[float]:
        """
        Find all peaks in the given CSV file.

        Args:
            csv_file_path (str): Path to the CSV file.

        Returns:
            List[float]: A list of detected peaks.
        """
        pass
        #todo: finishi this method