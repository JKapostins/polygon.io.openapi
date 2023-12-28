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
            attributes_md += f"- **{name}{required_text}** ({attr_type}): {description}\n"
            if attr_type.lower() == 'array':
                # Handle nested structure for array type
                nested_attrs = attr_div.find_next_sibling('div')
                if nested_attrs:
                    attributes_md += "  - **Attributes**:\n"
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
                            attributes_md += f"    - **{nested_name}{nested_required_text}** ({nested_attr_type}): {nested_description}\n"
    return attributes_md

# TODO: This OUTPUT is what endpoint_response_attributes generates, but i'm looking for this EXPECTED_OUTPUT. Notice the 'results' array and the c, h, l, n, o, otc, t, v, vw attributes are all nested under the results array. which was good, but they were also listed outside the array which is bad.

#OUTPUT
### Response Attributes

# - **ticker <span style='color: red'>*</span>** (string): The exchange symbol that this item is traded under.
# - **adjusted <span style='color: red'>*</span>** (boolean): Whether or not this response was adjusted for splits.
# - **queryCount <span style='color: red'>*</span>** (integer): The number of aggregates (minute or day) used to generate the response.
# - **request_id <span style='color: red'>*</span>** (string): A request id assigned by the server.
# - **resultsCount <span style='color: red'>*</span>** (integer): The total number of results for this request.
# - **status <span style='color: red'>*</span>** (string): The status of this request's response.
# - **results** (array): 
#   - **Attributes**:
#     - **c <span style='color: red'>*</span>** (number): The close price for the symbol in the given time period.
#     - **h <span style='color: red'>*</span>** (number): The highest price for the symbol in the given time period.
#     - **l <span style='color: red'>*</span>** (number): The lowest price for the symbol in the given time period.
#     - **n** (integer): The number of transactions in the aggregate window.
#     - **o <span style='color: red'>*</span>** (number): The open price for the symbol in the given time period.
#     - **otc** (boolean): Whether or not this aggregate is for an OTC ticker. This field will be left off if false.
#     - **t <span style='color: red'>*</span>** (integer): The Unix Msec timestamp for the start of the aggregate window.
#     - **v <span style='color: red'>*</span>** (number): The trading volume of the symbol in the given time period.
#     - **vw** (number): The volume weighted average price.
# - **c <span style='color: red'>*</span>** (number): The close price for the symbol in the given time period.
# - **h <span style='color: red'>*</span>** (number): The highest price for the symbol in the given time period.
# - **l <span style='color: red'>*</span>** (number): The lowest price for the symbol in the given time period.
# - **n** (integer): The number of transactions in the aggregate window.
# - **o <span style='color: red'>*</span>** (number): The open price for the symbol in the given time period.
# - **otc** (boolean): Whether or not this aggregate is for an OTC ticker. This field will be left off if false.
# - **t <span style='color: red'>*</span>** (integer): The Unix Msec timestamp for the start of the aggregate window.
# - **v <span style='color: red'>*</span>** (number): The trading volume of the symbol in the given time period.
# - **vw** (number): The volume weighted average price.
# - **next_url** (string): If present, this value can be used to fetch the next page of data.
#
#EXPECTED_OUTPUT
# - **ticker <span style='color: red'>*</span>** (string): The exchange symbol that this item is traded under.
# - **adjusted <span style='color: red'>*</span>** (boolean): Whether or not this response was adjusted for splits.
# - **queryCount <span style='color: red'>*</span>** (integer): The number of aggregates (minute or day) used to generate the response.
# - **request_id <span style='color: red'>*</span>** (string): A request id assigned by the server.
# - **resultsCount <span style='color: red'>*</span>** (integer): The total number of results for this request.
# - **status <span style='color: red'>*</span>** (string): The status of this request's response.
# - **results** (array): 
#   - **c <span style='color: red'>*</span>** (number): The close price for the symbol in the given time period.
#   - **h <span style='color: red'>*</span>** (number): The highest price for the symbol in the given time period.
#   - **l <span style='color: red'>*</span>** (number): The lowest price for the symbol in the given time period.
#   - **n** (integer): The number of transactions in the aggregate window.
#   - **o <span style='color: red'>*</span>** (number): The open price for the symbol in the given time period.
#   - **otc** (boolean): Whether or not this aggregate is for an OTC ticker. This field will be left off if false.
#   - **t <span style='color: red'>*</span>** (integer): The Unix Msec timestamp for the start of the aggregate window.
#   - **v <span style='color: red'>*</span>** (number): The trading volume of the symbol in the given time period.
#   - **vw** (number): The volume weighted average price.
# - **next_url** (string): If present, this value can be used to fetch the next page of data.

# Create a gneric function called endpointResponseAttributes that uses the classes of the ELEMENT using the CONSIDERATIONS.
# CONSIDERATIONS
# -The heading should always be named Response Attributes
# -Some attributes have a * at the end indicating they are required. this can have an impact on formatting but it is important to indicate what params are required in md.
# -Some attributes are an 'array' type which have a nested structure. this should be indicated in the md. See the 'results' attribute for an array is structured in the html.
# -Be sure to include the name, type and description of each attribute.
# ELEMENT
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">ticker<span
#                             class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                             size="2">*</span></span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">string</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>The exchange symbol that this item is traded under.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">adjusted<span
#                             class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                             size="2">*</span></span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">boolean</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>Whether or not this response was adjusted for splits.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">queryCount<span
#                             class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                             size="2">*</span></span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">integer</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>The number of aggregates (minute or day) used to generate the response.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">request_id<span
#                             class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                             size="2">*</span></span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">string</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>A request id assigned by the server.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                         size="2">resultsCount<span class="Text__StyledText-sc-6aor3p-0 iBsCAz"
#                             color="danger" size="2">*</span></span></span><span
#                     class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary" size="2">integer</span>
#             </div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>The total number of results for this request.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">status<span
#                             class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                             size="2">*</span></span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">string</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>The status of this request's response.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                         size="2">results</span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">array</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd"></div>
#         </div>
#     </div>
#     <div class="StyledSpacing-sc-wahrw5-0 eJGJaX">
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">c<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The close price for the symbol in the given time period.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">h<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The highest price for the symbol in the given time period.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">l<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The lowest price for the symbol in the given time period.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                                 size="2">n</span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                             color="secondary" size="2">integer</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The number of transactions in the aggregate window.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">o<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The open price for the symbol in the given time period.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                                 size="2">otc</span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                             color="secondary" size="2">boolean</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>Whether or not this aggregate is for an OTC ticker. This field will be left off
#                             if false.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">t<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">integer</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The Unix Msec timestamp for the start of the aggregate window.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit" size="2">v<span
#                                     class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                                     size="2">*</span></span></span><span
#                             class="Text__StyledText-sc-6aor3p-0 eelqYu" color="secondary"
#                             size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The trading volume of the symbol in the given time period.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#         <div>
#             <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#                 <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#                     <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                             class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                                 size="2">vw</span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                             color="secondary" size="2">number</span></div>
#                     <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                         <p>The volume weighted average price.</p>
#                     </div>
#                 </div>
#             </div>
#             <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
#         </div>
#     </div>
# </div>
# <div>
#     <div class="ResponseAttributes__OverflowXAuto-sc-hzb6em-0 kvQDCw">
#         <div class="StyledSpacing-sc-wahrw5-0 ivOril">
#             <div class="StyledSpacing-sc-wahrw5-0 gClFQA"><span
#                     class="StyledSpacing-sc-wahrw5-0 fUSYAk"><span
#                         class="Text__StyledText-sc-6aor3p-0 ggvwlD" color="inherit"
#                         size="2">next_url</span></span><span class="Text__StyledText-sc-6aor3p-0 eelqYu"
#                     color="secondary" size="2">string</span></div>
#             <div class="ResponseAttributes__Description-sc-hzb6em-1 dxfgDd">
#                 <p>If present, this value can be used to fetch the next page of data.</p>
#             </div>
#         </div>
#     </div>
#     <hr class="HorizontalRule__HR-sc-r26c8-0 gBqUvA" />
# </div>


                

if __name__ == '__main__':
    url = 'https://polygon.io/docs/stocks/getting-started'
    soup = parse_html_document(url)
    remove_first_nav_element(soup)
    extract_and_save_main_nav(soup)
    extract_and_save_main_content(soup)
    find_anchors_and_corresponding_divs()
