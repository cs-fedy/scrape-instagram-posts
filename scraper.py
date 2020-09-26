from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from time import sleep
import json

# TODO: use multiple threads to scrape data from posts.
# TODO: make this script as a cli using typer


def load_full_page_source_code(browser, callback=None):
    if callback:
        callback()
    return browser.page_source


def wait_until_page_is_loaded(browser, page_url):
    browser.get(page_url)
    sleep(10)
    print(f"@@@ {page_url} is loaded @@@")


def create_headless_browser():
    # options = Options()
    # options.set_headless()
    # assert options.headless  # assert Operating in headless mode
    # return webdriver.Chrome(options=options)
    return webdriver.Chrome()


class InstagramPostScraper:
    def __init__(self, post_url, browser=None):
        self.post_url = post_url
        if not browser:
            self.browser = create_headless_browser()
        else:
            self.browser = browser

    def get_post_details(self):
        wait_until_page_is_loaded(self.browser, self.post_url)
        source_code = load_full_page_source_code(self.browser)
        soup = BeautifulSoup(source_code, 'html.parser')
        article = soup.find("article")
        # * get post picture
        pictures_list = []
        try:
            go_to_the_right_element = self.browser.find_element_by_css_selector(
                ".coreSpriteRightChevron")
            while go_to_the_right_element:
                picture_element = self.browser.find_elements_by_css_selector(
                    "article img")[1]
                pictures_list.append(picture_element.get_attribute("src"))
                go_to_the_right_element.click()
                sleep(2)
                try:
                    go_to_the_right_element = self.browser.find_element_by_css_selector(
                        ".coreSpriteRightChevron")
                except:
                    go_to_the_right_element = None
        except:
            pictures = article.find_all("img")[1]
            pictures_list.append(pictures["src"])

        # * get post description
        description_element = soup.find("h2").find_next_sibling()
        description = description_element.getText()

        # * get likes count
        likes_section = article.select("section")
        likes = likes_section[1].getText()

        # * get share date
        date_element = article.find_all("time")[-1]
        date = date_element["datetime"]

        return {
            "url": self.post_url,
            "picture_url": pictures_list,
            "description": description,
            "likes_count": likes,
            "share_date": date
        }


class InstagramAccountScraper:
    def __init__(self, account_url, browser):
        self.account_url = account_url
        self.browser = browser

    def __scroll_to_the_buttom(self):
        # * scroll to buttom of the webpage
        scrolling_script = "window.scrollTo(0,document.body.scrollHeight)"
        content_page = ""
        while content_page != self.browser.page_source:
            content_page = self.browser.page_source
            self.browser.execute_script(scrolling_script)
            try:
                see_more = self.browser.find_element_by_xpath(
                    "//*[contains(text(), 'Show More Posts from')]")
                see_more.click()
            except:
                pass
            sleep(5)
        print("@@@ page is fully loaded @@@")

    def __get_profile_details(self, source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        account_details_section = soup.find_all("section")[-1]

        # * get profile picture
        profile_pict_element = soup.select("header img")[0]
        profile_pict = profile_pict_element["src"]

        statistics_element = account_details_section.find("ul")
        # * get account statistics
        stat = [
            child.getText() for child in statistics_element.findChildren()
        ][::3]
        posts, followers, following = stat

        details_element = statistics_element.find_next_sibling("div")
        # * get account name
        account_name = details_element.find("h1").getText()

        # * get account username
        account_username_element = soup.select_one("header section h2")
        account_username = account_username_element.getText()

        # * get account status: verified or not
        account_status_parent = account_username_element.find_next_sibling()
        account_status_element = account_status_parent.select_one("span")
        if account_status_element:
            account_status = account_status_element.getText()
        else:
            account_status = "not verified"

        # * get account bio
        bio = details_element.find("span").getText()

        return {
            "account_name": account_name,
            "account_username": account_username,
            "account_status": account_status,
            "profile_pict": profile_pict,
            "posts_count": posts,
            "followers_count": followers,
            "following_count": following,
            "bio": bio
        }

    def __get_posts_links(self, source_code):
        article = BeautifulSoup(source_code, 'html.parser').find("article")
        links = article.find_all("a")
        return [f"https://www.instagram.com/{link['href']}" for link in links]

    def __get_posts_details(self, source_code):
        urls = self.__get_posts_links(source_code)
        posts_details = []
        for url in urls:
            post_scraper = InstagramPostScraper(url, self.browser)
            posts_details.append(post_scraper.get_post_details())
        return posts_details

    def __form_final_data(self, profile_details, posts_details):
        data = {
            "profile_details": profile_details,
            "posts_details": posts_details
        }
        with open(r"data.json", mode="w+") as json_file:
            json.dump(data, json_file)

    def __call__(self):
        wait_until_page_is_loaded(self.browser, self.account_url)
        source_code = load_full_page_source_code(self.browser)
        account_details = self.__get_profile_details(source_code)
        posts_details = self.__get_posts_details(source_code)
        self.__form_final_data(account_details, posts_details)


class InstagramLogIn:
    def __init__(self, username, password, browser):
        self.browser = browser
        self.username = username
        self.password = password
        self.instagram_url = "https://www.instagram.com/"

    def __log_in(self):
        # * load page
        wait_until_page_is_loaded(self.browser, self.instagram_url)

        # * get username element and fill it
        username_element = self.browser.find_element_by_css_selector(
            "input[name=username]")
        username_element.send_keys(self.username)
        sleep(2)

        # * get password element and fill it
        password_element = self.browser.find_element_by_css_selector(
            "input[name=password]")
        password_element.send_keys(self.password)
        sleep(2)

        # * get submit element and submit
        submit_element = self.browser.find_elements_by_css_selector(
            "button")[1]
        submit_element.click()
        sleep(2)

        if "Sorry, your password was incorrect." in self.browser.page_source:
            raise Exception("check your username or password")

    def __call__(self):
        self.__log_in()


if __name__ == "__main__":
    browser = create_headless_browser()
    log = InstagramLogIn("your username", "your password here", browser)
    log()
    url = "https://www.instagram.com/medium/?hl=en"
    instagram_scraper = InstagramAccountScraper(url, browser)
    instagram_scraper()

