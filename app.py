# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started

# 2.) The First nav element is the header, which can be discarded

# 3.) The Second nav element is the main navigation (side bar) which contains links and hierarchy to the various endpoints.
#     Convert this to a markdown file and maintain the hierarchy defined in the html.
#     Save the markdown to a file called "navigation.md"


import requests
from bs4 import BeautifulSoup

def parse_html(url):
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')

def convert_nav_to_markdown(nav_element):
    markdown = ""
    for item in nav_element.find_all(['a', 'ul', 'li']):
        if item.name == 'a':
            markdown += f"### [{item.text.strip()}]({item['href']})\n"
        elif item.name == 'ul':
            markdown += "\n"
        elif item.name == 'li':
            markdown += "    "  # Indentation for hierarchy
    return markdown

def save_markdown_to_file(markdown, filename):
    with open(filename, 'w') as file:
        file.write(markdown)

def main():
    url = "https://polygon.io/docs/stocks/getting-started"
    soup = parse_html(url)
    nav_elements = soup.find_all('nav')
    if len(nav_elements) > 1:
        nav_markdown = convert_nav_to_markdown(nav_elements[1])
        save_markdown_to_file(nav_markdown, "navigation.md")

if __name__ == "__main__":
    main()
