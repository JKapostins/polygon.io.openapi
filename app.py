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
    parameters_md = "\n### Parameters\n\n<span style='color: red'>*</span> indicates a required parameter.\n\n"
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

def find_anchors_and_corresponding_divs():
    os.makedirs('output/html', exist_ok=True)
    os.makedirs('output/markdown', exist_ok=True)
    with open('output/html/body.html', 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    anchors = soup.find_all('a')
    for anchor in anchors:
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
                markdown += endpoint_parameters(endpoint_element)
                markdown += endpoint_response_attributes(endpoint_element)
                markdown += endpoint_response_object(endpoint_element)
                markdown = markdown.replace('‘', '`').replace('’', '`')
                with open(f'output/markdown/{endpoint_file_name}.md', 'w') as file:
                    file.write(markdown)


def endpoint_details(element):
    """Extract and format the endpoint details from the given HTML element."""
    details_md = "\n### Endpoint\n\n"
    method_element = element.find('span', class_='base__RequestMethod-sc-127j6tq-1')
    url_element = element.find('div', class_='Text__StyledText-sc-6aor3p-0')
    if method_element and url_element:
        method = method_element.get_text().strip().upper()
        url = url_element.get_text().strip()
        details_md += f"- Method: `{method}`\n"
        details_md += f"- Url: `{url}`\n\n"
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
    attributes_md = "\n### Response Attributes\n\n"
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



# TODO: Create a gneric function called endpointResponseObject that uses the classes of the ELEMENT using the CONSIDERATIONS.
# CONSIDERATIONS
# -This should be a code block in json format. You should pretty print the json.
# ELEMENT
# <div class="GridItem__StyledGridItem-sc-1xj2soh-0 jHuWkP">
# <div class="StyledSpacing-sc-wahrw5-0 bERlWl">
#     <div class="Text__StyledText-sc-6aor3p-0 iGHfaJ SubsectionLabel__StyledLabel-sc-ynvayg-0 kgOCfx"
#         color="secondary" size="3">Response Object</div>
#     <pre class="CodeBlock__StyledHighlighter-sc-14zdm7l-0 dEqsNg"
#         style="display:block;overflow-x:auto;padding:0.5em;color:#383a42;background:#fafafa"><code class="language-json" style="white-space:pre"><span>{
# </span><span>  </span><span style="color:#986801">"adjusted"</span><span>: </span><span style="color:#0184bb">true</span><span>,
# </span><span>  </span><span style="color:#986801">"next_url"</span><span>: </span><span style="color:#50a14f">"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/1578114000000/2020-01-10?cursor=bGltaXQ9MiZzb3J0PWFzYw"</span><span>,
# </span><span>  </span><span style="color:#986801">"queryCount"</span><span>: </span><span style="color:#986801">2</span><span>,
# </span><span>  </span><span style="color:#986801">"request_id"</span><span>: </span><span style="color:#50a14f">"6a7e466379af0a71039d60cc78e72282"</span><span>,
# </span><span>  </span><span style="color:#986801">"results"</span><span>: [
# </span>    {
# <span>      </span><span style="color:#986801">"c"</span><span>: </span><span style="color:#986801">75.0875</span><span>,
# </span><span>      </span><span style="color:#986801">"h"</span><span>: </span><span style="color:#986801">75.15</span><span>,
# </span><span>      </span><span style="color:#986801">"l"</span><span>: </span><span style="color:#986801">73.7975</span><span>,
# </span><span>      </span><span style="color:#986801">"n"</span><span>: </span><span style="color:#986801">1</span><span>,
# </span><span>      </span><span style="color:#986801">"o"</span><span>: </span><span style="color:#986801">74.06</span><span>,
# </span><span>      </span><span style="color:#986801">"t"</span><span>: </span><span style="color:#986801">1577941200000</span><span>,
# </span><span>      </span><span style="color:#986801">"v"</span><span>: </span><span style="color:#986801">135647456</span><span>,
# </span><span>      </span><span style="color:#986801">"vw"</span><span>: </span><span style="color:#986801">74.6099</span><span>
# </span>    },
# <!-- -->    {
# <span>      </span><span style="color:#986801">"c"</span><span>: </span><span style="color:#986801">74.3575</span><span>,
# </span><span>      </span><span style="color:#986801">"h"</span><span>: </span><span style="color:#986801">75.145</span><span>,
# </span><span>      </span><span style="color:#986801">"l"</span><span>: </span><span style="color:#986801">74.125</span><span>,
# </span><span>      </span><span style="color:#986801">"n"</span><span>: </span><span style="color:#986801">1</span><span>,
# </span><span>      </span><span style="color:#986801">"o"</span><span>: </span><span style="color:#986801">74.2875</span><span>,
# </span><span>      </span><span style="color:#986801">"t"</span><span>: </span><span style="color:#986801">1578027600000</span><span>,
# </span><span>      </span><span style="color:#986801">"v"</span><span>: </span><span style="color:#986801">146535512</span><span>,
# </span><span>      </span><span style="color:#986801">"vw"</span><span>: </span><span style="color:#986801">74.7026</span><span>
# </span>    }
# <!-- -->  ],
# <span>  </span><span style="color:#986801">"resultsCount"</span><span>: </span><span style="color:#986801">2</span><span>,
# </span><span>  </span><span style="color:#986801">"status"</span><span>: </span><span style="color:#50a14f">"OK"</span><span>,
# </span><span>  </span><span style="color:#986801">"ticker"</span><span>: </span><span style="color:#50a14f">"AAPL"</span><span>
# </span>}</code></pre>
#             </div>
#         </div>

def endpoint_response_object(element):
    """Extract and format the response object from the given HTML element."""
    response_object_md = "\n### Response Object\n\n```json\n"
    response_object_div = element.find('div', class_='GridItem__StyledGridItem-sc-1xj2soh-0')
    if response_object_div:
        pre = response_object_div.find('pre')
        if pre:
            response_object_md += pre.get_text().strip() + "\n"
    response_object_md += "```\n\n"
    return response_object_md
                

if __name__ == '__main__':
    url = 'https://polygon.io/docs/stocks/getting-started'
    soup = parse_html_document(url)
    remove_first_nav_element(soup)
    extract_and_save_main_nav(soup)
    extract_and_save_main_content(soup)
    find_anchors_and_corresponding_divs()

