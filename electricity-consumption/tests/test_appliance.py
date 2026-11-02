
import unittest
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"

USERNAME = "laya"
PASSWORD = "123456"


class ApplianceTests(unittest.TestCase):

    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False
        })

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def tearDown(self):
        self.driver.quit()

    def test_01_appliance_page_load(self):
        self.driver.get(BASE_URL + "/?skip_lang=true")

        self.driver.find_element(By.NAME, "username").send_keys(USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(self.driver, 20).until(
            EC.url_contains("/dashboard/")
        )

        self.assertIn("/dashboard/", self.driver.current_url)

        print("TC01 PASSED: Appliance dashboard accessed successfully")


if __name__ == "__main__":
    unittest.main(verbosity=2)
