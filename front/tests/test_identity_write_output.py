
from seleniumbase import BaseCase
import time



class ComponentsTest(BaseCase):
    def test_basic(self):

        # open the app and take a screenshot
        self.open("http://localhost:8501")

        time.sleep(5)  # give leaflet time to load from web
        self.check_window(name="first_test", level=2)

        
        self.assert_text("Identity")

