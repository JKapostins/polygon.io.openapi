# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started 

# 2.) Remove the first nav element from the document

# 3.) The Second nav element is the main navigation (side bar) which contains links and hierarchy to the various endpoints.
#     Dump this element to an html file so we can use it for hierarchy reference and then remove it from the document.

# 4.) The first div element is the main content of the page, write this to a file called body.html

# 5.) Find all the anchors in the body.html

# 6.) For each anchor, find the corresponding div element and write it to a file called {endponit_name}_endpoint.htmlimport requests
# Missing import for requests added
import requests
import re
from markdownify import markdownify as md
from bs4 import BeautifulSoup

def parse_html_document(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        raise Exception(f"Failed to retrieve the document. Status code: {response.status_code}")

def remove_first_nav_element(soup):
    nav = soup.find('nav')
    if nav:
        nav.decompose()

def extract_and_save_main_nav(soup):
    nav = soup.find('nav')
    if nav:
        with open('sidebar.html', 'w') as file:
            file.write(str(nav))
        nav.decompose()

def extract_and_save_main_content(soup):
    div = soup.find('div')
    if div:
        with open('body.html', 'w') as file:
            file.write(str(div))


def find_anchors_and_corresponding_divs():
    with open('body.html', 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    anchors = soup.find_all('a')
    for anchor in anchors:
        h2 = anchor.find('h2')
        endpoint_name = h2.text if h2 else None
        if endpoint_name:
            endpoint_element = anchor.find_parent('div')
            while True:
                # Find the parent <div> element
                endpoint_element = endpoint_element.find_parent('div')

                # If the parent <div> has no class attribute, break the loop
                if endpoint_element is None or not endpoint_element.has_attr('class'):
                    break
            if endpoint_element:
                with open(f'{endpoint_name}_endpoint.html', 'w') as file:
                    file.write(str(endpoint_element))
                #convert_to_markdown_and_save(endpoint_name, endpoint_element)


# TODO: Create a generic function that uses the classes of the ELEMENT to pick it out and parse out the POINTS_OF_INTEREST in this FORMAT.
# ELEMENT
#     <a
#     class="ScrollTargetLink__Anchor-sc-yy6ew6-0 iCcuRo StyledSpacing-sc-wahrw5-0 dsgUMc"
#     href="https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to"
#     role="button" tabindex="0" type="button">
#     <h2 class="Text__StyledText-sc-6aor3p-0 cCFnnL Typography__StyledText-sc-102sqjl-0 gHCXHz"
#         color="primary" size="7">Aggregates (Bars)</h2>
# </a>
# POINTS_OF_INTEREST
# -Aggregates (Bars)
# -https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to
# FORMAT
# ## <a href='https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to'> Aggregates (Bars) </a>




#-----------------OLD CODE-----------------#


# def convert_to_markdown(element):
#     """ Convert HTML elements to Markdown. """

#     if element.name == 'a' and element.get('href'):
#         return f"## <a href='{element['href']}'> {element.get_text().strip()} </a>\n\n"
#     elif element.name == 'p':
#         return f"{element.get_text().strip()}\n\n"
#     elif element.name == 'pre':
#         return f"```\n{element.get_text().strip()}\n```\n\n"
#     elif element.name == 'div' and 'StyledSpacing-sc-wahrw5-0' in element.get('class', []) and 'jpImIW' in element.get('class', []):
#         return handle_parameters(element)
#     return ""

# def handle_parameters(element):
#     """ Handle the parameters section. """
#     params_md = "\n### Parameters\n\n"
#     # Find all parameter containers
#     param_containers = element.find_all('div', class_='Parameters__MaxWidth-sc-ize944-0', recursive=True)
    
#     for container in param_containers:
#         # Extracting parameter name from the label
#         label = container.find('label')
#         if label:
#             param_name = ' '.join(label.stripped_strings).strip()

#             # Check if the parameter is required (indicated by an asterisk)
#             is_required = '*' in param_name
#             if is_required:
#                 param_name = param_name.replace('*', '').strip()  # Remove asterisk
#                 required_text = " (required)"
#             else:
#                 required_text = ""

#             # Finding the corresponding description
#             description_container = container.find_next_sibling('div', class_='Parameters__Description-sc-ize944-1')
#             if description_container:
#                 param_desc = description_container.get_text().strip()


#                 params_md += f"- **{param_name}{required_text}** - {param_desc}\n"


#     return params_md

# def html_to_markdown(html_content):
#     """ Convert HTML content to Markdown. """
#     soup = BeautifulSoup(html_content, 'html.parser')
#     markdown = []

#     # Start from the main container div
#     main_container = soup.find('div', class_='Grid__Component-sc-h1tb5o-0')
#     if not main_container:
#         main_container = soup

#     for element in main_container.find_all(recursive=True):
#         text = convert_to_markdown(element)
#         text = text.replace('‘', '`').replace('’', '`')
#         markdown.append(text)

#     return ''.join(markdown)

# def convert_to_markdown_and_save(endpoint_name, html_content):
#     markdown_content = html_to_markdown(str(html_content))
#     with open(f'{endpoint_name}_endpoint.md', 'w') as file:
#         file.write(markdown_content)
                

if __name__ == '__main__':
    url = 'https://polygon.io/docs/stocks/getting-started'
    soup = parse_html_document(url)
    remove_first_nav_element(soup)
    extract_and_save_main_nav(soup)
    extract_and_save_main_content(soup)
    find_anchors_and_corresponding_divs()
