import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import pandas as pd
import re 
from dateutil import parser

news_pattern = re.compile(r'^/news/\d{1,3}/$') #news pattern /news/123 etc 
total_pages = 27 #of news, put your own 
date_pattern = re.compile(r'([A-Z][a-z]+\.? \d{1,2}, \d{4})')
base_url = "https://alumnieuropae.org" #your URL
post_author = 1 #set your own
post_category = 1 #set your own

# Function to get the HTML content of a page
def get_html(url):
    print(f"Fetching URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"Successfully fetched URL: {url}")
        return response.text
    except requests.RequestException as e:
        print(f"Request failed for URL: {url} with error: {e}")
        return None

#  Function to extract sub-page URLs from a given page
def extract_sub_page_urls(html):
    print("Extracting sub-page URLs...")
    soup = BeautifulSoup(html, 'html.parser')
    sub_page_urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if news_pattern.match(href):  # Ensuring it matches '/news/123' format
            sub_page_urls.append(base_url + href)
    print(f"Found {len(sub_page_urls)} sub-page URLs")
    return sub_page_urls

# Main function to scrape all the sub-page URLs
def scrape_sub_pages(base_url, total_pages, output_file):
    all_sub_page_urls = []

    for page_number in range(1, total_pages + 1):
        main_page_url = f"{base_url}?page={page_number}"
        print(f"Processing main page: {main_page_url}")
        html = get_html(main_page_url)
        if html:
            sub_page_urls = extract_sub_page_urls(html)
            all_sub_page_urls.extend(sub_page_urls)
        else:
            print(f"Failed to retrieve or parse page {page_number}")

    print(f"Writing {len(all_sub_page_urls)} sub-page URLs to {output_file}")
    with open(output_file, 'w') as file:
        for url in all_sub_page_urls:
            file.write(url + '\n')

    print(f"Saved {len(all_sub_page_urls)} sub-page URLs to {output_file}")

# Define news base URL 
base_url_news = base_url + "/news/"
output_file = 'news_urls.txt'

# Run the scraper
scrape_sub_pages(base_url_news, total_pages, output_file)


def remove_duplicates(input_file, output_file):
    # Read the file and store all lines in a set to remove duplicates
    with open(input_file, 'r') as file:
        lines = file.readlines()

    unique_lines = set(lines)  # Set automatically removes duplicates

    # Write the unique lines back to the file
    with open(output_file, 'w') as file:
        for line in unique_lines:
            file.write(line)

# Define input and output file paths
input_file = 'news_urls.txt'
output_file = 'unique_news_urls.txt'

# Remove duplicates from the input file
remove_duplicates(input_file, output_file)

print(f"Duplicates removed and unique URLs saved to {output_file}")

# Function to scramble the filename with a random integer
def scramble_filename(filename):
    name, ext = os.path.splitext(filename)
    random_int = random.randint(1000, 9999)
    scrambled_name = f"{name}_{random_int}"
    return scrambled_name + ext

# Function to process each URL
def process_url(url):
    # Fetch the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the title
    title = soup.find('h1', class_='font-weight-bold').text.strip()

    # Extract the image URL
    image_tag = soup.find('img', class_='img-fluid shadow rounded-lg')
    image_url = base_url + image_tag['src'] if image_tag else ''

    

    # Extract the content within the 'main-content' class
    content_div = soup.find('section', class_='main-content')
    content = ''
    if content_div:
        paragraphs = content_div.find_all('p')
        content = '\n'.join(p.prettify() for p in paragraphs)

    # Format content for SQL
    content = content.replace("'", "''")

    # Extract the published date using the provided regex pattern
    page_content = response.text
    date_match = date_pattern.search(page_content)

    if date_match:
        date_string = date_match.group(1)
        try:
            # List of possible date formats
            try:
            # Use dateutil.parser to parse the date string
                timestamp = parser.parse(date_string)
            except ValueError:
                # If parsing fails, use the current date as fallback
                 print (date_string)
                 print("Error with the date")
                 exit(1)

            # Format the datetime object to "Y-m-d H:i:s"
            published_date_sql = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            year = timestamp.strftime('%Y')
            month = timestamp.strftime('%m')

           
        except ValueError:
            print (date_string)
            print("Error with the date")
            exit(1)
    else:
        # Fallback to current date if pattern does not match
        print("Error with the date")
        exit(1)


    # Create the local directory to save the image
    if image_url:
    
        image_path_parts = image_tag['src'].split('/')
        image_folder = os.path.join('wp-content', 'uploads', year, month)
        os.makedirs(image_folder, exist_ok=True)
        original_filename = image_path_parts[-1]
        scrambled_filename = scramble_filename(original_filename)
        image_local_path = os.path.join(image_folder, scrambled_filename)

    # Download the image and save it locally
    if image_url:
        image_response = requests.get(image_url)
        with open(image_local_path, 'wb') as f:
            f.write(image_response.content)

    # Format the image path for SQL (assuming images are stored in 'wp-content/uploads/{year}/{month}/')
    wp_image_path = ''
    if image_url:
    
        wp_image_path = f'/wp-content/uploads/{year}/{month}/{scrambled_filename}'

    # Prepare the data for Excel
    data = {
        'post_title': title,
        'post_content': content,
        'post_date': published_date_sql,
        'post_status': 'publish',
        'post_category': post_category,
        'post_author': post_author,
        'post_img_dir': wp_image_path,
        'original_url': url
    }
    
    print("Processing " + url, end='\n')

    return data

# Read URLs from the text file
with open('unique_news_urls.txt', 'r') as file:
    urls = file.readlines()

# Process each URL and collect the data
data_list = []
for url in urls:
    url = url.strip()
    if url:
        data = process_url(url)
        data_list.append(data)

# Create a DataFrame and save to Excel
df = pd.DataFrame(data_list)
df.to_excel('posts.xlsx', index=False)

print("Data has been saved to 'posts.xlsx'.")
