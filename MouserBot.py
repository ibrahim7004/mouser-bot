import os
from Selenium_Utils import SeleniumUtils
import json
from datetime import datetime
import gzip
from files import home_page_dir, detail_page_dir, cookies_dir


class MouserBot:
    def __init__(self, tsv_file):
        self.tsv_file = tsv_file
        self._selenium = SeleniumUtils()
        self.execute_process()
        self._selenium.close_session()

    def execute_process(self):
        is_navigated = self.navigate_on_mouser()
        if is_navigated is False:
            return
        self.search_part_numbers()

    def navigate_on_mouser(self, re_init=False, cookies=[]):
        if re_init is True:
            self._selenium = SeleniumUtils()

        self._selenium.go_to_url("https://www.mouser.com/")

        cookies_added = self.add_cookies(cookies)
        if cookies_added is False:
            return False

        captcha_page = '//p[@class="captcha__human__title"]'
        mouser_logo = '//h1[@id="logo"]/a[@id="mouserLogo"]'
        mouser_searchbar = '//input[@aria-label="Search by part numbers or keywords"]'
        nav_bar = '//nav[@role="navigation"]'
        iframe_path = "//iframe[@sandbox]"

        # self._selenium.switch_to_iframe(iframe_path, wait_secs=2)
        # self._selenium.wait_for_element_intractable(captcha_page, wait_secs=2)
        # if self._selenium.isElementPresent(captcha_page) is True:
        #     self._selenium.driver.refresh()
        #     self._selenium.driver.switch_to.default_content()

        self._selenium.wait_for_element_intractable(mouser_logo, wait_secs=5)
        self._selenium.wait_for_element_intractable(
            mouser_searchbar, wait_secs=5)
        self._selenium.wait_for_element_intractable(nav_bar, wait_secs=5)

    def search_part_numbers(self):
        searchbar_box = '//input[@aria-label="Search by part numbers or keywords" or @aria-label="Enter a part number or keyword"]'
        searchbar_loading = searchbar_box + \
            '/parent::div//*[contains(@class, "fa-spinner")]'
        searchbar_icon = searchbar_box + \
            '//ancestor::div[@id="search-bar"]//button[@id="hdrSrch"]'
        part_number_link = '(//div[@class="search-table-wrapper"]//tbody//td[contains(@class, "part-column")]//a)[1]'
        part_row_search = '//div[@class="search-table-wrapper"]/table[contains(@class, "SearchResultsTable")]'
        panel_search = '//div[@class="container-fluid"]//div[@class="panel panel-default"]'
        no_result_search = '//div[@class="container-fluid no-results-heading"]'
        wait_after_search = '(//div[@class="row"]//div[contains(@class, "breadcrumb")])[1]'
        scroll_to_table = '//div[@class="search-table-wrapper"]'
        captcha_page = '//p[@class="captcha__human__title"]'

        part_numbers_list = [
            o for o in self.tsv_file.read().split("\n") if o != ""]

        for current_part_index, part_number in enumerate(part_numbers_list, start=1):
            current_time = datetime.now().strftime("%H:%M:%S")
            print(
                f"{current_time} --> Current Part# {part_number} --> {current_part_index}")

            if current_part_index % 10 == 0:
                refreshed_cookies = self._selenium.driver.get_cookies()
                self.add_cookies(refreshed_cookies)
                self._selenium.wait_for_element_presence(searchbar_box)

            if self._selenium.isElementPresent(captcha_page):
                print("Captcha page appears. Solve it manually and update the cookies.")
                self.navigate_on_mouser()

            try:
                self._selenium.fill_keys_value(searchbar_box, part_number)
                self._selenium.wait_for_loading_to_finish(searchbar_loading)
                self._selenium.click_element(searchbar_icon)
                self._selenium.wait_for_element_intractable(wait_after_search)

                if self._selenium.isElementPresent(panel_search) or self._selenium.isElementPresent(no_result_search) or self._selenium.isElementPresent(part_row_search):
                    print(f"Home Page Result Part# {part_number}")
                    home_page_html_content = self._selenium.driver.page_source.encode(
                        "UTF-8")
                    file_path = os.path.join(
                        home_page_dir, part_number + ".html")
                    encoded_html_file(file_path, home_page_html_content)

                    if self._selenium.isElementPresent(part_row_search):
                        print(f"Inside Detail Page Part# {part_number}")
                        self._selenium.scroll_to_element(scroll_to_table)
                        self._selenium.click_element(part_number_link)
                        self._selenium.wait_for_element_intractable(
                            wait_after_search)
                        detail_page_html_content = self._selenium.driver.page_source.encode(
                            "UTF-8")
                        file_path = os.path.join(
                            detail_page_dir, part_number + ".html")
                        encoded_html_file(file_path, detail_page_html_content)
                else:
                    print(
                        f"Navigate on another page or the website is not accessible. Current Part# {part_number}")
                    current_url = self._selenium.driver.current_url
                    print(f"URL: {current_url}")
                    print("Re-Navigating to home page of the website")
                    self._selenium.close_session()
                    self._selenium.initialize_chrome_webdriver()
                    self.navigate_on_mouser()

            except Exception as error:
                print(f"Error occurred in Part# {part_number} Error: {error}")

            # After processing the part number, remove it from the list and rewrite the file
            del part_numbers_list[current_part_index - 1]
            with open(self.tsv_file.name, 'w', encoding='utf-8') as updated_file:
                updated_file.write("\n".join(part_numbers_list))
            print(f"File updated after processing Part# {part_number}")

        print("Loop end for current part numbers...")

    def add_cookies(self, cookies_list=[]):
        mouser_logo = '//h1[@id="logo"]/a[@id="mouserLogo"]'
        max_attempts = 5
        retries_attempt = 1
        cookies_added = False

        while not cookies_added and retries_attempt <= max_attempts:
            print(f"Attempt at adding cookies: {retries_attempt}")
            try:
                if cookies_list == []:
                    cookies_file = open_text_file(cookies_dir, mode="r")
                    cookies_json = json.load(cookies_file)
                else:
                    cookies_json = cookies_list

                for cookie in cookies_json:
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                        del cookie['sameSite']
                    self._selenium.driver.add_cookie(cookie)

                cookies_added = True
                print("Cookies added successfully.")
                self._selenium.driver.refresh()
                return cookies_added

            except Exception as err:
                self._selenium.driver.refresh()
                self._selenium.wait_for_element_intractable(
                    mouser_logo, wait_secs=5)
                if self._selenium.isElementPresent(mouser_logo):
                    return True

                print(
                    f"Error adding cookies on attempt {retries_attempt}: {err}")
                input(
                    "Is captcha solved manually from local browser and cookies updated into json file? ")
                retries_attempt += 1
                self.re_initialize_webdriver()

            if retries_attempt == max_attempts:
                print("Max retry attempts reached. Cookies could not be added.")
                return False

    def re_initialize_webdriver(self, refreshed_cookies=[], part_number=""):
        print("Re initializing chrome webdriver end")
        # print(f"Navigate on other page or website is not accessible. Current Part# {part_number}")
        # current_url = self._selenium.driver.current_url
        # print(f"URL: {current_url}")
        # print("Re-Navigating to home page of the website")
        self._selenium.close_session()
        # print(f"Current close has been closed {part_number} --> {current_part_index}")
        print(f"Current close has been closed {part_number}")
        self.navigate_on_mouser(re_init=True, cookies=refreshed_cookies)
        print("Re initializing chrome webdriver end")


def open_text_file(directory, mode=""):
    print("open_text_file() start")
    file_txt = False
    try:
        file_txt = open(directory, mode, encoding='utf-8')
        if file_txt is not None:
            print("open_text_file() end")
            return file_txt
    except Exception as err:
        print(f"open_text_file() Error: {err}")
        return file_txt
    print("open_text_file() end")
    return file_txt


def encoded_html_file(directory, html_content):
    print("save_encoded_file() start")
    file_txt = False
    try:
        file_txt = gzip.open(directory, 'wb')
        if file_txt is not None:
            file_txt.write(html_content)
    except Exception as err:
        print(f"save_encoded_file() Error: {err}")
        return file_txt
    print("save_encoded_file() end")
