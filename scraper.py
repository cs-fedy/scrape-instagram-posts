from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import json

# TODO: use multiple threads to scrape data from posts.
# TODO: scroll to the buttom of the page and get all post url.
# TODO: allow user to login to his account to explore private accounts
# TODO: make a class that scrape post data
# TODO: add account status verified or not
# TODO: scrape instagram account picture


class InstagramAccountScraper:
    def __init__(self, account_url):
        self.account_url = account_url
        self.browser = webdriver.Chrome()

    def __wait_until_page_is_loaded(self, page_url=None):
        if not page_url:
            page_url = self.account_url
        self.browser.get(page_url)
        sleep(10)
        print(f"@@@ {page_url} is loaded @@@")

    def __load_full_page_source_code(self):
        # * scroll to buttom of the webpage
        scrolling_script = "window.scrollTo(0,document.body.scrollHeight)"
        content_page = ""
        while content_page != self.browser.page_source:
            content_page = self.browser.page_source
            self.browser.execute_script(scrolling_script)
            try:
                see_more = self.browser.find_element_by_xpath("//*[contains(text(), 'Show More Posts from')]")
                see_more.click()
            except:
                pass

            sleep(5)
        print("@@@ page is fully loaded @@@")
        return self.browser.page_source

    def __get_profile_details(self, source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        account_details_section = soup.find_all("section")[-1]

        statistics_element = account_details_section.find("ul")
        # * get account statistics
        stat = [
            child.getText() for child in statistics_element.findChildren()
        ][::3]
        posts, followers, following = stat

        details_element = statistics_element.find_next_sibling("div")
        # * get account name
        account_name = details_element.find("h1").getText()

        # * get account bio
        bio = details_element.find("span").getText()

        return {
            "account_name": account_name,
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
        return [self.__get_post_details(url) for url in urls]

    def __get_post_details(self, post_url):
        self.__wait_until_page_is_loaded(post_url)
        source_code = self.__load_full_page_source_code()
        soup = BeautifulSoup(source_code, 'html.parser')
        article = soup.find("article")
        # * get post picture
        pictures = article.find_all("img")[1]
        post_pict = pictures["src"]

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
            "url": post_url,
            "picture_url": post_pict,
            "description": description,
            "likes_count": likes,
            "share_date": date
        }

    def __form_final_data(self, profile_details, posts_details):
        data = {
            "profile_details": profile_details,
            "posts_details": posts_details
        }
        with open(r"data.json", mode="w+") as json_file:
            json.dump(data, json_file)

    def __call__(self):
        self.__wait_until_page_is_loaded()
        source_code = self.__load_full_page_source_code()
        account_details = self.__get_profile_details(source_code)
        posts_details = self.__get_posts_details(source_code)
        self.__form_final_data(account_details, posts_details)


if __name__ == "__main__":
    url = "https://www.instagram.com/medium/?hl=en"
    instagram_scraper = InstagramAccountScraper(url)
    instagram_scraper()
