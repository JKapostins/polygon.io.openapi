# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started 

# 2.) write the first div element to body.html

# 3.) The Second nav element is the main navigation (side bar) which contains links and hierarchy to the various endpoints.
#     Dump this element to an html file so we can use it for hierarchy reference.



# Import necessary libraries
import requests
from bs4 import BeautifulSoup

# Function to fetch and parse HTML document
def fetch_and_parse_document(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        raise Exception(f"Failed to fetch the document, status code: {response.status_code}")

# Function to write the first div element to body.html
def write_first_div_to_file(soup, filename):
    first_div = soup.find('div')
    with open(filename, 'w') as file:
        file.write(str(first_div))

# Function to dump the second nav element to an HTML file
def dump_second_nav_to_file(soup, filename):
    nav_elements = soup.find_all('nav')
    if len(nav_elements) >= 2:
        second_nav = nav_elements[1]
        with open(filename, 'w') as file:
            file.write(str(second_nav))
    else:
        raise Exception("Second nav element not found.")

# Main execution
if __name__ == "__main__":
    url = "https://polygon.io/docs/stocks/getting-started"
    soup = fetch_and_parse_document(url)
    write_first_div_to_file(soup, 'body.html')
    dump_second_nav_to_file(soup, 'sidebar.html')
