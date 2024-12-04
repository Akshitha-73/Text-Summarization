# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 09:39:23 2024

@author: akshi
"""
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_news():
    base_url = "https://www.malaymail.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    news_data = []
    
    try:
        # Fetch the main page
        r = requests.get(base_url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            headlines = soup.find_all(['h2', 'h3'])
            today = datetime.today().strftime('%Y-%m-%d')

            for i in headlines:
                title = i.get_text(strip=True)
                link = i.find('a', href=True)
                article_url = None
                article_text = None

                if link:
                    article_url = link['href']
                    # Ensure the link is absolute
                    if article_url.startswith('/'):
                        article_url = base_url.rstrip('/') + article_url
                    
                    # Fetch the article content
                    article_text = fetch_article_text(article_url, headers)
                
                # Append to the news data
                news_data.append({
                    "Date": today,
                    "Title": title,
                    "Link": article_url if article_url else "No link available",
                    "Article Text": article_text if article_text else "Content not found"
                })
        else:
            print(f"Failed to retrieve the webpage. Status code: {r.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # Save the news data to a CSV file
    save_to_csv(news_data, "news_data.csv")


def fetch_article_text(url, headers):
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            content_container = soup.find("div", class_="article-body")  # Adjust based on site structure
            if content_container:
                paragraphs = content_container.find_all("p")
                return " ".join([p.get_text(strip=True) for p in paragraphs])
            else:
                return "Content not found"
        elif r.status_code == 403:
            return "Access denied (403)."
        else:
            return f"Failed to fetch article. Status code: {r.status_code}"
    except Exception as e:
        return f"Error fetching article: {e}"


def save_to_csv(data, filename):
    try:
        keys = ["Date", "Title", "Link", "Article Text"]
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data has been written to {filename}")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")


# Call the function to fetch and save news
get_news()
