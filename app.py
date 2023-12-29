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
import os
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
        os.makedirs('output/html', exist_ok=True)
        with open('output/html/sidebar.html', 'w') as file:
            file.write(str(nav))
        nav.decompose()

def extract_and_save_main_content(soup):
    div = soup.find('div')
    if div:
        os.makedirs('output/html', exist_ok=True)
        with open('output/html/body.html', 'w') as file:
            file.write(str(div))


def endpoint_heading(element):
    """Extract and format the endpoint heading from the given HTML element."""
    classes = element.get('class', [])
    if 'ScrollTargetLink__Anchor-sc-yy6ew6-0' in classes:
        endpoint_name = element.find('h2').get_text().strip()
        endpoint_url = element.get('href').strip()
        return f"## <a href='{endpoint_url}'> {endpoint_name} </a>\n\n"
    return ""

def endpoint_parameters(element):
    """Extract and format the parameters from the given HTML element."""
    parameters_md = "\n#### Parameters\n\n<span style='color: red'>*</span> indicates a required parameter.\n\n"
    param_divs = element.find_all('div', class_='Parameters__MaxWidth-sc-ize944-0')
    for param_div in param_divs:
        label = param_div.find('label')
        if label:
            param_name = ' '.join(label.stripped_strings).strip()
            is_required = '*' in param_name
            param_name = param_name.replace('*', '').strip()
            required_text = " <span style='color: red'>*</span>" if is_required else ""
            description_div = param_div.find_next_sibling('div', class_='Parameters__Description-sc-ize944-1')            
            param_desc = ""
            if description_div:
                for content in description_div.contents:
                    if content.name == 'a' and content.has_attr('href'):
                        link_text = content.get_text().strip()
                        link_href = content['href']
                        param_desc += f"[{link_text}]({link_href})"
                    else:
                        param_desc += content if isinstance(content, str) else content.get_text()
            param_desc = param_desc.strip()
            parameters_md += f"- **{param_name}{required_text}**: {param_desc}\n"
            param_options = param_div.find('menu')
            if param_options:
                options_md = '\n'.join([f"  - `{li.get_text().strip()}`" for li in param_options.find_all('li')])
                parameters_md += options_md + "\n\n"
    return parameters_md
def sanitize_filename(name):
    """Sanitize the filename to remove special characters."""
    sanitized_name = re.sub(r'[^\w\s-]', '_', name)
    sanitized_name = re.sub(r'\s+', '_', sanitized_name)
    sanitized_name = sanitized_name.lower()
    sanitized_name = re.sub(r'_{2,}', '_', sanitized_name)  # Ensure only one underscore before '_endpoint'
    return sanitized_name

def create_websocket_api_overview_markdown():
    with open('output/html/body.html', 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    websocket_section = soup.find('div', class_='Grid__Component-sc-h1tb5o-0 Grid__StyledGrid-sc-h1tb5o-1 eKoQMw hNiMUQ StyledSpacing-sc-wahrw5-0 bbSzhC StyledSpacing-sc-wahrw5-0 NOTdS')
    if not websocket_section:
        raise ValueError("WebSocket section not found in the HTML document.")

    websocket_overview_md = ""

    # Extract the WebSocket Documentation section
    websocket_heading = websocket_section.find('h2', class_=['Text__StyledText-sc-6aor3p-0', 'cCFnnL'])
    if websocket_heading:
        websocket_overview_md += f"## {websocket_heading.get_text().strip()}\n\n"

    # Extract the paragraphs and sections under the WebSocket Documentation
    for element in websocket_section.find_all(['p', 'h3', 'pre', 'span'], recursive=True):
        if element.name == 'p':
            text = element.get_text().strip()
            if 'connecting to a cluster' in text.lower() :
                text = f"#### {text}\n\n"
            websocket_overview_md += f"{text}\n\n"
        elif element.name == 'h3':
            websocket_overview_md += f"### {element.get_text().strip()}\n\n"
        elif element.name == 'pre' or (element.name == 'span' and 'Text__StyledText-sc-6aor3p-0' in element.get('class', []) and 'kjHyPJ' in element.get('class', [])):
            websocket_overview_md += f"```\n{element.get_text().strip()}\n```\n\n"
        elif (element.name == 'span' and 'Text__StyledText-sc-6aor3p-0' in element.get('class', []) and 'zZEZj' in element.get('class', [])):
            websocket_overview_md += f"##### {element.get_text().strip()}\n\n"

    # Write to markdown file
    websocket_markdown_path = 'output/markdown/websocket'
    os.makedirs(websocket_markdown_path, exist_ok=True)
    with open(f'{websocket_markdown_path}/websocket_api_overview.md', 'w') as file:
        file.write(websocket_overview_md)

def find_anchors_and_corresponding_divs():
    os.makedirs('output/html', exist_ok=True)
    rest_markdown_path = 'output/markdown/rest'
    os.makedirs(rest_markdown_path, exist_ok=True)
    with open('output/html/body.html', 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    anchors = soup.find_all('a')
    for anchor in anchors:
        # Skip the Stocks WebSocket Documentation section
        if 'ws_getting-started' in anchor.get('href', ''):
            continue
        h2 = anchor.find('h2')
        endpoint_name = sanitize_filename(h2.text) if h2 else None
        if endpoint_name:
            endpoint_element = anchor.find_parent('div')
            while True:
                # Find the parent <div> element
                endpoint_element = endpoint_element.find_parent('div')

                # If the parent <div> has no class attribute, break the loop
                if endpoint_element is None or not endpoint_element.has_attr('class'):
                    break
            if endpoint_element:
                endpoint_file_name = sanitize_filename(f"{endpoint_name}_endpoint")
                with open(f'output/html/{endpoint_file_name}.html', 'w') as file:
                    file.write(str(endpoint_element))
                markdown = endpoint_heading(anchor)
                markdown += endpoint_details(endpoint_element)
                markdown += endpoint_description(endpoint_element)
                markdown += "### Request\n\n"
                markdown += endpoint_parameters(endpoint_element)
                markdown += example_endpoint_request(endpoint_element)
                markdown += "### Response\n\n"
                markdown += endpoint_response_attributes(endpoint_element)                
                markdown += endpoint_response_object(endpoint_element)
                markdown = markdown.replace('‘', '`').replace('’', '`')
                with open(f'{rest_markdown_path}/{endpoint_file_name}.md', 'w') as file:
                    file.write(markdown)


def example_endpoint_request(element):
    """Extract and format the example endpoint request from the given HTML element."""
    example_request_md = "\n#### Example Request\n\n"
    text_wrapper = element.find('div', class_='Copy__TextWrapper-sc-71i6s4-1 bsrJTO')
    if text_wrapper:
        request_url = text_wrapper.get_text().strip()
        example_request_md += f"```\n{request_url.replace('*', '{POLYGON_API_KEY}')}\n```\n"
    return example_request_md


def endpoint_details(element):
    """Extract and format the endpoint details from the given HTML element."""
    details_md = "\n### Endpoint\n\n"
    method_elements = element.find_all('span', class_='base__RequestMethod-sc-127j6tq-1')
    url_elements = element.find_all('div', class_='Text__StyledText-sc-6aor3p-0')
    if method_elements and url_elements:
        methods_urls = zip(method_elements, url_elements)
        for method_element, url_element in methods_urls:
            method = method_element.get_text().strip().upper()
            urls = url_element.find_all('div')
            if urls:
                details_md += f"- Method: `{method}`\n"
                if len(urls) > 1:
                    details_md += "- Urls:\n"
                    for url in urls:
                        label = url.find('label')
                        if label:
                            label_text = label.get_text().strip()
                            url_text = url.get_text().strip().replace(label_text, '').strip()
                            details_md += f"  - {label_text} `{url_text}`\n"
                        else:
                            url_text = url.get_text().strip()
                            details_md += f"  - `{url_text}`\n"
                else:
                    url_text = urls[0].get_text().strip()
                    details_md += f"- Url: `{url_text}`\n"
            else:
                # Fallback to the text of the url_element itself if no divs are found
                url_text = url_element.get_text().strip()
                details_md += f"- Method: `{method}`\n"
                details_md += f"- Url: `{url_text}`\n"
        details_md += "\n"
    return details_md


def endpoint_description(element):
    """Extract and format the endpoint description from the given HTML element."""
    description_md = "\n### Description\n\n"
    description_elements = element.find_all('div', class_='Text__StyledText-sc-6aor3p-0')
    for desc_element in description_elements:
        if 'jugoJw' in desc_element.get('class', []):
            description_md += f"{desc_element.get_text().strip()}\n\n"
    return description_md.replace('<br />', '\n').replace('<br>', '\n')


def endpoint_response_attributes(element):
    """Extract and format the response attributes from the given HTML element."""
    attributes_md = "\n#### Attributes\n\n"
    attributes_md += "<span style='color: red'>*</span> indicates the attribute is gaurenteed to be returned, otherwise the attribtue may not be returned so ensure your parser can handle these cases.\n\n"
    attribute_divs = element.find_all('div', class_='ResponseAttributes__OverflowXAuto-sc-hzb6em-0')
    for attr_div in attribute_divs:
        name_span = attr_div.find('span', class_='Text__StyledText-sc-6aor3p-0 ggvwlD')
        type_span = attr_div.find('span', class_='Text__StyledText-sc-6aor3p-0 eelqYu')
        description_p = attr_div.find('div', class_='ResponseAttributes__Description-sc-hzb6em-1')
        if name_span and type_span and description_p:
            name = name_span.get_text().strip()
            is_required = '*' in name
            name = name.replace('*', '').strip()
            required_text = " <span style='color: red'>*</span>" if is_required else ""
            attr_type = type_span.get_text().strip()
            description = description_p.get_text().strip()
            attribute =  f"- **{name}{required_text}** ({attr_type}): {description}\n"
                # Check if the attribute is already in attributes_md
            if attribute not in attributes_md:
                attributes_md += attribute
            if attr_type.lower() == 'array':
                # Handle nested structure for array type
                nested_attrs = attr_div.find_next_sibling('div')
                if nested_attrs:
                    nested_attribute_divs = nested_attrs.find_all('div', recursive=False)
                    for nested_attr_div in nested_attribute_divs:
                        nested_name_span = nested_attr_div.find('span', class_='Text__StyledText-sc-6aor3p-0 ggvwlD')
                        nested_type_span = nested_attr_div.find('span', class_='Text__StyledText-sc-6aor3p-0 eelqYu')
                        nested_description_p = nested_attr_div.find('div', class_='ResponseAttributes__Description-sc-hzb6em-1')
                        if nested_name_span and nested_type_span and nested_description_p:
                            nested_name = nested_name_span.get_text().strip()
                            nested_is_required = '*' in nested_name
                            nested_name = nested_name.replace('*', '').strip()
                            nested_required_text = " <span style='color: red'>*</span>" if nested_is_required else ""
                            nested_attr_type = nested_type_span.get_text().strip()
                            nested_description = nested_description_p.get_text().strip()
                            attributes_md += f"  - **{nested_name}{nested_required_text}** ({nested_attr_type}): {nested_description}\n"
    return attributes_md



def endpoint_response_object(element):
    """Extract and format the response object from the given HTML element."""
    response_object_md = "\n#### Example Response\n\n```json\n"
    pre = element.find('pre')
    if pre:
        response_object_md += pre.get_text().strip() + "\n"
    response_object_md += "```\n\n"
    return response_object_md
                

def create_api_overview_markdown():
    with open('output/html/body.html', 'r') as file:
        full_soup = BeautifulSoup(file.read(), 'html.parser')

    # Extract the overview section from the full body
    overview_section = full_soup.find('div', class_='ScrollTrackedSection__ScrollTargetWrapper-sc-1r3wlr6-0')
    if not overview_section:
        raise ValueError("Overview section not found in the HTML document.")

    api_overview_md = ""

    # Extract the Introduction section
    introduction = overview_section.find('h1')
    if introduction:
        api_overview_md += f"## {introduction.get_text().strip()}\n\n"
        intro_paragraph = overview_section.find('p', class_=['text__IntroParagraph-sc-1lz0rk3-1', 'jgWzFC'])
        if intro_paragraph:
            api_overview_md += f"{intro_paragraph.get_text().strip()}\n\n"

    # Extract the Authentication section
    authentication = overview_section.find('h3', text=re.compile('Authentication'))
    if authentication:
        api_overview_md += f"### {authentication.get_text().strip()}\n\n"
        query_string_description = authentication.find_next_sibling('p')
        bearer_description = query_string_description.find_next_sibling('p')
        if query_string_description:
            api_overview_md += f"{query_string_description.get_text().strip()}\n\n"

        code_sections = authentication.find_all_next('span', class_=['Text__StyledText-sc-6aor3p-0','kjHyPJ'])
        if code_sections:
            api_overview_md += f"```\n{code_sections[0].get_text().strip().replace('*', '{POLYGON_API_KEY}')}\n```\n\n"
        
        if(bearer_description):
            api_overview_md += f"{bearer_description.get_text().strip()}\n\n"

        if code_sections and len(code_sections) >= 2:
            api_overview_md += f"```\n{code_sections[1].get_text().strip().replace('<token>', '{POLYGON_API_KEY}')}\n```\n\n"

    # Extract the Usage section
    usage = overview_section.find('h3', text=re.compile('Usage'))
    if usage:
        api_overview_md += f"### {usage.get_text().strip()}\n\n"
        usage_description = usage.find_next_sibling('p')
        if usage_description:
            api_overview_md += f"{usage_description.get_text().strip()}\n\n"

    # Extract the Response Types section
    response_types = overview_section.find('h3', text=re.compile('Response Types'))
    if response_types:
        api_overview_md += f"### {response_types.get_text().strip()}\n\n"
        response_description = response_types.find_next_sibling('p')
        if response_description:
            api_overview_md += f"{response_description.get_text().strip()}\n\n"

    # Write to markdown file
    os.makedirs('output/markdown', exist_ok=True)
    with open('output/markdown/rest_api_overview.md', 'w') as file:
        file.write(api_overview_md)


if __name__ == '__main__':
    url = 'https://polygon.io/docs/stocks/getting-started'
    soup = parse_html_document(url)
    remove_first_nav_element(soup)
    extract_and_save_main_nav(soup)
    extract_and_save_main_content(soup)
    create_api_overview_markdown()
    create_websocket_api_overview_markdown()
    find_anchors_and_corresponding_divs()

