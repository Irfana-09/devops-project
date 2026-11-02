
import unittest
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://127.0.0.1:5000"


class RegistrationTests(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get(BASE_URL + "/register")

    def tearDown(self):
        self.driver.quit()

    def test_01_valid_registration(self):
        username = "test_" + uuid.uuid4().hex[:8]

        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "email").send_keys(
            username + "@example.com"
        )
        self.driver.find_element(By.NAME, "phone").send_keys("9876543210")
        self.driver.find_element(By.NAME, "password").send_keys("Test@12345")

        self.driver.find_element(
            By.CSS_SELECTOR, "button[type='submit']"
        ).click()

        WebDriverWait(self.driver, 10).until(
            lambda d: "/register" not in d.current_url
        )

        self.assertIn("skip_lang=true", self.driver.current_url)
        print("TC01 PASSED: Valid registration")

    def test_02_empty_fields(self):
        form = self.driver.find_element(By.TAG_NAME, "form")

        self.assertFalse(
            self.driver.execute_script(
                "return arguments[0].checkValidity()", form
            )
        )

        print("TC02 PASSED: Empty fields validation")

    def test_03_invalid_email(self):
        email = self.driver.find_element(By.NAME, "email")
        email.send_keys("invalid-email")

        self.assertFalse(
            self.driver.execute_script(
                "return arguments[0].checkValidity()", email
            )
        )

        print("TC03 PASSED: Invalid email validation")


if __name__ == "__main__":
    unittest.main(verbosity=2)
