from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep
import json

# TODO: scroll to the buttom of the page and get all post url.
# TODO: use multiple threads to scrape data from posts.
# TODO: allow user to login to his instagram account.
#! TO FIX: fix scraping posts description

class GetData:
    def __init__(self, page_url):
        self.page_url = page_url
        # self.options = Options()
        # self.options.set_headless()
        # assert self.options.headless  # assert Operating in headless mode
        # self.driver = webdriver.Chrome(options=self.options)
        self.driver = webdriver.Chrome()

    def get_posts_urls(self, posts):
        return [post.get_attribute('href')
                for post in posts]

    def __wait_until_page_is_loaded(self, tag, page_url=None):
        if not page_url:
            page_url = self.page_url
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, tag))
            )
        finally:
            print(f"==== url {page_url} is loaded ====")
        return element

    def get_post_data(self, url):
        self.driver.get(url)
        article = self.__wait_until_page_is_loaded("article", url)
        post_img = article.find_element_by_tag_name("img")
        img_src = post_img.get_attribute("src")
        description_element = article.find_element_by_xpath("/html/body/div[6]/div[2]/div/article/div[3]/div[1]/ul/div/li/div/div/div[2]/span")
        print("="*20)
        print(f"scraping data from {url} done")
        print(description_element.text)
        return { "img_src": img_src, "description": description_element.text}

    def get_posts_data(self):
        self.driver.get(self.page_url)
        article = self.__wait_until_page_is_loaded("article")
        posts = article.find_elements_by_tag_name("a")
        urls = self.get_posts_urls(posts)
        result_data = []
        for url in urls:
            data = self.get_post_data(url)
            result_data.append(data)

        with open("result.json", mode="w+") as json_file:
            json.dump(result_data, json_file)


if __name__ == "__main__":
    url = "instagram profile to scrape url here"
    data_scraper = GetData(url)
    data_scraper.get_posts_data()
    data_scraper.driver.close()
