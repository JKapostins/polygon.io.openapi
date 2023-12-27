# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started and extract the anchors out of the fith <div/> element. These anchors will be our urls for differnet documentations (stocks, forex, crypto, etc.)

# 2.) Print the anchors so we can see what we are working with.
# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started and extract the anchors out of the fifth <div/> element. These anchors will be our urls for different documentations (stocks, forex, crypto, etc.)

# 2.) Print the anchors so we can see what we are working with.

import requests
from bs4 import BeautifulSoup

def extract_documentation_urls():
    url = 'https://polygon.io/docs/stocks/getting-started'
    response = requests.get(url)
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    div_elements = soup.find_all('div')  # Find all div elements
    if len(div_elements) < 5:
        raise ValueError("Expected at least 5 div elements to parse the documentation URLs.")
    fifth_div = div_elements[4]  # Get the fifth div element
    anchors = fifth_div.find_all('a', href=True)

    # Extract URLs
    urls = [anchor['href'] for anchor in anchors]
    return urls

if __name__ == '__main__':
    documentation_urls = extract_documentation_urls()
    for url in documentation_urls:
        print(url)
