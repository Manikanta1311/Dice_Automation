import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

class DiceAutoApply:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:config = json.load(f)

        self.email = config.get("email")
        self.password = config.get("password")
        self.keyword = config.get("keyword")
        self.location = config.get("location")

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

 #login   
    def login(self):
        self.driver.get("https://www.dice.com/dashboard/login")

        #email input
        email_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "email")))
        email_input.clear()
        email_input.send_keys(self.email)

        continue_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        continue_button.click()

        #password input
        password_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "password")))
        password_input.clear()
        password_input.send_keys(self.password)
        time.sleep(3)

        #cookie banner
        try:
            cookie_banner = self.wait.until(EC.presence_of_element_located((By.ID, "cmpwrapper")))
            print("Cookie banner detected — closing it...")
            self.driver.execute_script("""let banner = document.getElementById('cmpwrapper');if (banner) banner.style.display = 'none';""")
        except TimeoutException:
            pass
        time.sleep(2)

        #sign in button
        sign_in_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign In')]")))
        self.driver.execute_script("arguments[0].click();", sign_in_button)

        print("Logged in")
        time.sleep(2)

    #job search button
    def navigate_to_search(self):
        job_search=self.wait.until(EC.presence_of_element_located((By.NAME, "q")))
        job_search.click()
        print("Job search page is loaded")

    #search jobs
    def search_jobs(self):
        
        what_input = self.wait.until(EC.presence_of_element_located((By.NAME, "q")))
        what_input.clear()
        what_input.send_keys(self.keyword)

        where_input = self.wait.until(EC.presence_of_element_located((By.NAME, "location")))
        where_input.clear()
        where_input.send_keys(self.location)

        search_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Search')]")))
        self.driver.execute_script("arguments[0].click();", search_button)
        print("Job search completed")
        time.sleep(5)

#easy apply button
    def click_apply_button(self):
        try:
            time.sleep(2)
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, "//h1")))

            #easy apply button
            easyapply_button = self.driver.execute_script("""const shadowHost = document.querySelector('#applyButton > apply-button-wc');if (!shadowHost) return null;const shadowRoot = shadowHost.shadowRoot;if (!shadowRoot) return null;const innerButton = shadowRoot.querySelector('apply-button > div > button');return innerButton;""")

            if not easyapply_button:
                print("Already applied or not available")
                return 

            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", easyapply_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", easyapply_button)
            time.sleep(3)

            # next button
            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']")))
            next_button.click()
            time.sleep(2)

            #submit button
            submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Submit']")))
            submit_button.click()
            time.sleep(2)
            print("Application submitted successfully")

        except Exception as e:
            print(f"Error while applying: {e}")

#apply job application
    def apply_to_jobs(self):
        applied_links = set()
        original_tab = self.driver.current_window_handle
        page_number = 1

        while True:
            print(f"\n Processing Page {page_number}")

            try:
                job_cards = WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//a[@data-testid='job-search-job-detail-link']")))
            except TimeoutException:
                break

            links = list({card.get_attribute("href") for card in job_cards if card.get_attribute("href")})
            print(f"Found {len(links)} job listings on this page.")

            for idx, link in enumerate(links, start=1):
                if link in applied_links:
                    continue
                applied_links.add(link)

                print(f"\n Opening job {idx}/{len(links)}: {link}")

                try:    
                    self.driver.execute_script(f"window.open('{link}', '_blank');")
                    WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)

                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(3)

                    WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, "//button | //a")))

                    self.click_apply_button()

                except Exception as e:
                    print(f"Error applying to job: {e}")

                finally:

                    try:
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                        self.driver.switch_to.window(original_tab)
                    except Exception:
                        pass

                time.sleep(random.uniform(3, 7))

            # next page
            try:
                next_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//nav[@aria-label='Pagination']//span[@aria-label='Next' and @role='link']")))

                class_attr = next_button.get_attribute("class") or ""
                if "cursor-pointer" not in class_attr:
                    print("\n Last page reached.process complete")
                    break

                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_button)
                time.sleep(random.uniform(1, 2))

                try:
                    next_button.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", next_button)

                print(f"Moving to next page {page_number}")
                page_number += 1

                WebDriverWait(self.driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//a[@data-testid='job-search-job-detail-link']")))
                time.sleep(random.uniform(5, 9))

            except TimeoutException:
                print("\n No more pages")
                break

            except Exception as e:
                print(f"Pagination error: {e}")
                break

    def run(self):
        self.login()
        self.navigate_to_search()
        self.search_jobs()
        self.apply_to_jobs()
        print(" Automation complete")
        self.driver.quit()

if __name__ == "__main__":
    bot = DiceAutoApply("config.json")
    bot.run()
