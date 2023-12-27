# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started

# 2.) The First nav element is the header, which can be discarded

# 3.) The Second nav element is the main navigation (side bar) which contains links and hierarchy to the various endpoints.
#     Dump this element to an html file so we can use it for hierarchy reference.

# 4.) Convert the html file to a markdown file



# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import html2text

# Function to fetch and parse the HTML document
def fetch_documentation():
    url = 'https://polygon.io/docs/stocks/getting-started'
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        raise Exception(f'Failed to fetch documentation, status code: {response.status_code}')

# Function to process the HTML and extract relevant information
def process_documentation():
    soup = fetch_documentation()
    # Discard the first nav element (header)
    header_nav = soup.find('nav')
    header_nav.decompose()

    # Extract the second nav element (main navigation/sidebar)
    main_nav = soup.find('nav')
    with open('sidebar_hierarchy.html', 'w') as file:
        file.write(str(main_nav))

    # Convert the html file to a markdown file
    convert_html_to_markdown('sidebar_hierarchy.html')

# Function to convert HTML to Markdown
def convert_html_to_markdown(html_file_path):
    with open(html_file_path, 'r') as file:
        html_content = file.read()
    markdown_content = html2text.html2text(html_content)
    markdown_file_path = html_file_path.replace('.html', '.md')
    with open(markdown_file_path, 'w') as file:
        file.write(markdown_content)

# Main execution
if __name__ == '__main__':
    process_documentation()
