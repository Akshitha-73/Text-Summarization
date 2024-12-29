import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import streamlit as st
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import joblib

# Load T5-small model and tokenizer
model_path = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)

# Load SVM model and TF-IDF vectorizer
svm_model_path = "svm_sentiment_model.pkl"
vectorizer_path = "tfidf_vectorizer.pkl"
svm_model = joblib.load(svm_model_path)
vectorizer = joblib.load(vectorizer_path)

# Function to fetch article text
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

# Function to summarize text
def summarize_text(text):
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)
    summary_ids = model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Function to classify sentiment
def classify_sentiment(text):
    transformed_text = vectorizer.transform([text])
    sentiment = svm_model.predict(transformed_text)[0]
    sentiment_label = "Positive" if sentiment == 1 else "Negative"
    return sentiment_label

# Main function to get news from a user-provided URL
def get_news_from_url(user_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    news_data = []
    
    try:
        # Fetch the main page
        r = requests.get(user_url, headers=headers)
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
                        article_url = user_url.rstrip('/') + article_url
                    
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
            st.write(f"Failed to retrieve the webpage. Status code: {r.status_code}")
    except Exception as e:
        st.write(f"An error occurred: {e}")
    
    return news_data

# Streamlit UI
st.title("Custom URL News Scraper with Summarization and Sentiment Analysis")

# User input for URL
user_url = st.text_input("Enter the URL to scrape:")

# Button to fetch news from user-provided URL
if st.button("Extract News"):
    if user_url:
        extracted_data = get_news_from_url(user_url)
        st.session_state['extracted_data'] = extracted_data
        filtered_data = [news for news in extracted_data if news["Article Text"] != "Content not found"]
        st.session_state['extracted_data'] = filtered_data
    else:
        st.write("Please enter a valid URL.")

# Display extracted data
if 'extracted_data' in st.session_state:
    df = pd.DataFrame(st.session_state['extracted_data'])
    st.dataframe(df)

    # Button to summarize articles
    if st.button("Summarize Articles"):
        summarized_data = []
        for index, row in df.iterrows():
            summary = summarize_text(row["Article Text"])
            summarized_data.append({
                "Date": row["Date"],
                "Title": row["Title"],
                "Link": row["Link"],
                "Summary": summary
            })
        st.session_state['summarized_data'] = summarized_data
        st.dataframe(pd.DataFrame(summarized_data))

    # Button for sentiment analysis
    if 'summarized_data' in st.session_state and st.button("Classify Sentiment"):
        sentiment_data = []
        for row in st.session_state['summarized_data']:
            sentiment = classify_sentiment(row["Summary"])
            sentiment_data.append({
                "Date": row["Date"],
                "Title": row["Title"],
                "Link": row["Link"],
                "Summary": row["Summary"],
                "Sentiment": sentiment
            })
        st.session_state['sentiment_data'] = sentiment_data
        st.dataframe(pd.DataFrame(sentiment_data))
