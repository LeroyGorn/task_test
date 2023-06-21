import csv
import re
import urllib.request
from collections import Counter
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class NewsParser:
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename

    def get_publications_per_page(self):
        response = urllib.request.urlopen(self.url)
        html = response.read().decode('utf-8')

        soup = BeautifulSoup(html, 'html.parser')
        publications = soup.find_all('picture')
        return set(publications)

    def get_article_stats(self):
        articles = self.get_articles()

        for article_url in articles:
            response = urllib.request.urlopen(article_url)
            article = response.read().decode('utf-8')
            soup = BeautifulSoup(article, 'html.parser')
            section = soup.find('section', class_='advanced-grid-main-area')

            titles = soup.select('p', class_='.body-paragraph')
            images = section.find_all('img')
            words = self.get_common_words(titles)
            tags = soup.find_all('a', class_='linkHovers__LinkBackgroundHover-sc-1ad8end-0')

            yield {
                    'name': soup.find('h1', class_='headline false').text,
                    'url': article_url,
                    'titles': len(titles),
                    'images': len(images),
                    'tags': [i.text for i in tags]
            } | words

    def get_common_words(self, titles):
        common_words = Counter()
        paragraphs = [i.text for i in titles]

        text = ' '.join(paragraphs)
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()

        excluded_words = {'a', 'an', 'the'}
        filtered_words = [word for word in words if word.lower() not in excluded_words]
        common_words.update(filtered_words)
        most_common = common_words.most_common(1)[0][0]

        return {'words': len(words), 'common_words': most_common}

    def get_articles(self):
        domain = 'https://www.thenationalnews.com/'
        return [
            urljoin(domain, i.parent['href'])
            for i in self.get_publications_per_page()
        ]

    def save_data(self):
        fieldnames = ['name', 'url', 'titles', 'images', 'words', 'tags', 'common_words']

        with open(self.filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for stats in self.get_article_stats():
                writer.writerow(stats)


if __name__ == '__main__':
    url = 'https://www.thenationalnews.com/travel/'
    filename = 'stats.csv'
    parser = NewsParser(url, filename)
    parser.save_data()
