
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:5000"

class LoginTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get(BASE_URL + "/?skip_lang=true")

    def tearDown(self):
        self.driver.quit()

    def test_01_empty_fields(self):
        form = self.driver.find_element(By.TAG_NAME, "form")

        self.assertFalse(
            self.driver.execute_script(
                "return arguments[0].checkValidity()", form
            )
        )

        print("TC01 PASSED: Empty fields validation")


if __name__ == "__main__":
    unittest.main(verbosity=2)
