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
                markdown += "### Request\n\n"
                markdown += endpoint_parameters(endpoint_element)
                markdown += example_endpoint_request(endpoint_element)
                markdown += "### Response\n\n"
                markdown += endpoint_response_attributes(endpoint_element)                
                markdown += endpoint_response_object(endpoint_element)
                markdown = markdown.replace('‘', '`').replace('’', '`')
                with open(f'output/markdown/{endpoint_file_name}.md', 'w') as file:
                    file.write(markdown)


def example_endpoint_request(element):
    """Extract and format the example endpoint request from the given HTML element."""
    example_request_md = "\n#### Example Request\n\n"
    text_wrapper = element.find('div', class_='Copy__TextWrapper-sc-71i6s4-1 bsrJTO')
    if text_wrapper:
        request_url = text_wrapper.get_text().strip()
        example_request_md += f"```\n{request_url}\n```\n"
    return example_request_md

# TODO: There were are two sections missing in create_api_overview_markdown. See CONSIDERATIONS.
#CONSIDERATIONS:
#- https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-09/2023-01-09?apiKey=* should be in a code block
#-Authorization: Bearer should be in a code block

# EXAMPLE:
# <div
#     class="Grid__Component-sc-h1tb5o-0 Grid__StyledGrid-sc-h1tb5o-1 eKoQMw hNiMUQ StyledSpacing-sc-wahrw5-0 NOTdS">
#     <div class="GridItem__StyledGridItem-sc-1xj2soh-0 fUyjCB">
#         <div class="ScrollTrackedSection__ScrollTargetWrapper-sc-1r3wlr6-0 ejmzQM">
#             <div class="ScrollTrackedSection__ScrollTarget-sc-1r3wlr6-1 SsvbF"></div>
#             <div><a class="ScrollTargetLink__Anchor-sc-yy6ew6-0 iCcuRo"
#                     href="https://polygon.io/docs/stocks/getting-started" role="button"
#                     tabindex="0" type="button">
#                     <h1 class="Text__StyledText-sc-6aor3p-0 cCFnnL Typography__StyledText-sc-102sqjl-0 gHCXHz StyledSpacing-sc-wahrw5-0 bgcozF"
#                         color="primary" size="7">Stocks<!-- --> API Documentation</h1>
#                 </a>
#                 <p class="Text__StyledText-sc-6aor3p-0 fcoMFQ Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroParagraph-sc-1lz0rk3-1 jgWzFC"
#                     color="primary" size="4">The Polygon.io Stocks API provides REST endpoints
#                     that let you
#                     query the latest market data from all US stock exchanges. You
#                     can also find data on company financials, stock market
#                     holidays, corporate actions, and more.</p>
#                 <div class="base__ImageWrapper-sc-m66r7j-1 kTSEDX"><img alt="Documentation"
#                         src="/docs/imgs/docs.svg" width="1000" /></div>
#                 <section class="text__IntroSection-sc-1lz0rk3-2 ewCtP">
#                     <h3 class="Text__StyledText-sc-6aor3p-0 hLpLcI Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroSubheader-sc-1lz0rk3-0 duOjBR"
#                         color="primary" size="6">Authentication</h3>
#                     <p class="Text__StyledText-sc-6aor3p-0 fcoMFQ Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroBlockDescription-sc-1lz0rk3-3 djOhnS"
#                         color="primary" size="4">Pass your API key in the query string like
#                         follows:</p>
#                     <div class="text__IntroBlock-sc-1lz0rk3-4 fCthNE">
#                         <div class="Copy__Background-sc-71i6s4-0 cqbdLN">
#                             <div class="Container__StyledContainer-sc-83etil-0 fODFXk"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hOBmCZ"
#                                     order="0">
#                                     <div class="Copy__TextWrapper-sc-71i6s4-1 bsrJTO"><span
#                                             class="Text__StyledText-sc-6aor3p-0 kjHyPJ"
#                                             color="inherit" height="1.3"
#                                             size="2">https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2023-01-09/2023-01-09?apiKey=*</span>
#                                     </div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0"><button
#                                         class="Button__StyledButton-sc-1gkx93s-0 hISVkJ Copy__StyledCopyButton-sc-71i6s4-2 kJkhwx"><span
#                                             class="styles__CenteredContentSpan-sc-1vm3dn3-1 dfBape"><span
#                                                 class="styles__CenteredContentSpan-sc-1vm3dn3-1 styles__LoadingSpan-sc-1vm3dn3-2 dfBape eTnjgJ">Copy</span></span></button>
#                                 </div>
#                             </div>
#                         </div>
#                     </div>
#                     <p class="Text__StyledText-sc-6aor3p-0 fcoMFQ Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroBlockDescription-sc-1lz0rk3-3 djOhnS"
#                         color="primary" size="4">Alternatively, you can add an Authorization
#                         header to the request with your API Key as the token in the following
#                         form:</p>
#                     <div class="Copy__Background-sc-71i6s4-0 cqbdLN">
#                         <div class="Container__StyledContainer-sc-83etil-0 fODFXk" spacing="0">
#                             <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hOBmCZ"
#                                 order="0">
#                                 <div class="Copy__TextWrapper-sc-71i6s4-1 bsrJTO"><span
#                                         class="Text__StyledText-sc-6aor3p-0 kjHyPJ"
#                                         color="inherit" height="1.3" size="2">Authorization:
#                                         Bearer &lt;token&gt;</span></div>
#                             </div>
#                             <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                 order="0"><button
#                                     class="Button__StyledButton-sc-1gkx93s-0 hISVkJ Copy__StyledCopyButton-sc-71i6s4-2 kJkhwx"><span
#                                         class="styles__CenteredContentSpan-sc-1vm3dn3-1 dfBape"><span
#                                             class="styles__CenteredContentSpan-sc-1vm3dn3-1 styles__LoadingSpan-sc-1vm3dn3-2 dfBape eTnjgJ">Copy</span></span></button>
#                             </div>
#                         </div>
#                     </div>
#                 </section>
#                 <section class="text__IntroSection-sc-1lz0rk3-2 ewCtP">
#                     <h3 class="Text__StyledText-sc-6aor3p-0 hLpLcI Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroSubheader-sc-1lz0rk3-0 duOjBR"
#                         color="primary" size="6">Usage</h3>
#                     <p class="Text__StyledText-sc-6aor3p-0 fcoMFQ Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroParagraph-sc-1lz0rk3-1 czACEG"
#                         color="primary" size="4">Many of Polygon.io's REST endpoints allow you
#                         to<!-- --> <a
#                             class="Link__StyledLink-sc-wnesr1-0 cfajpz InlineLink-sc-163zztk-0 fBowrm"
#                             href="https://polygon.io/blog/api-pagination-patterns/"
#                             size="1">extend query parameters</a> <!-- -->with inequalities
#                         like<!-- --> <span class="Text__StyledText-sc-6aor3p-0 bTkseI"
#                             color="secondary" size="3">date.lt=2023-01-01</span> <!-- -->(less
#                         than) and<!-- --> <span class="Text__StyledText-sc-6aor3p-0 bTkseI"
#                             color="secondary" size="3">date.gte=2023-01-01</span>
#                         <!-- -->(greater than or equal to) to search ranges of values. You can
#                         also use the field name without any extension to query for exact
#                         equality. Fields that support extensions will have an "Additional filter
#                         parameters" dropdown beneath them in the docs that detail the supported
#                         extensions for that parameter.</p>
#                 </section>
#                 <section class="text__IntroSection-sc-1lz0rk3-2 ewCtP">
#                     <h3 class="Text__StyledText-sc-6aor3p-0 hLpLcI Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroSubheader-sc-1lz0rk3-0 duOjBR"
#                         color="primary" size="6">Response Types</h3>
#                     <p class="Text__StyledText-sc-6aor3p-0 fcoMFQ Typography__StyledText-sc-102sqjl-0 gHCXHz text__IntroParagraph-sc-1lz0rk3-1 czACEG"
#                         color="primary" size="4">By default, all endpoints return a JSON
#                         response. Users with<!-- --> <span
#                             class="base__StyledText-sc-m66r7j-0 hMpQcG" size="4">Stocks</span>
#                         <!-- -->Starter plan and above can request a CSV response by
#                         including<!-- --> <span class="Text__StyledText-sc-6aor3p-0 bTkseI"
#                             color="secondary" size="3">'Accept': 'text/csv'</span> <!-- -->as a
#                         request parameter.</p>
#                 </section>
#             </div>
#         </div>
#     </div>
#     <div class="GridItem__StyledGridItem-sc-1xj2soh-0 jHuWkP">
#         <div class="Grid__Component-sc-h1tb5o-0 Grid__StyledGrid-sc-h1tb5o-1 jkEOHr hNiMUQ">
#             <div class="GridItem__StyledGridItem-sc-1xj2soh-0 isWvay"></div>
#             <div class="GridItem__StyledGridItem-sc-1xj2soh-0 Mqtlr">
#                 <div class="StyledSpacing-sc-wahrw5-0 doupJv">
#                     <div class="StyledSpacing-sc-wahrw5-0 hKvqOb">
#                         <div class="Text__StyledText-sc-6aor3p-0 iGHfaJ SubsectionLabel__StyledLabel-sc-ynvayg-0 kgOCfx"
#                             color="secondary" size="3">Client Libraries</div>
#                     </div>
#                     <div><a class="repoLink__StyledLink-sc-qaanzw-1 erDtuF"
#                             href="https://github.com/polygon-io/client-python"
#                             rel="nofollow noreferrer" target="_blank">
#                             <div class="Container__StyledContainer-sc-83etil-0 cibvzg StyledSpacing-sc-wahrw5-0 hYiXxL"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div
#                                         class="repoLink__ImageWrapper-sc-qaanzw-0 kAmzzR StyledSpacing-sc-wahrw5-0 cHhFWW">
#                                         <img alt="Python Logo" height="20"
#                                             src="/docs/icons/python.svg" width="24" /></div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div class="Text__StyledText-sc-6aor3p-0 cBFSFL"
#                                         color="primary" size="3">Python</div>
#                                     <div class="Text__StyledText-sc-6aor3p-0 ieZVsm"
#                                         color="secondary" size="3">client-python</div>
#                                 </div>
#                             </div>
#                         </a></div>
#                     <div><a class="repoLink__StyledLink-sc-qaanzw-1 erDtuF"
#                             href="https://github.com/polygon-io/client-go"
#                             rel="nofollow noreferrer" target="_blank">
#                             <div class="Container__StyledContainer-sc-83etil-0 cibvzg StyledSpacing-sc-wahrw5-0 hYiXxL"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div
#                                         class="repoLink__ImageWrapper-sc-qaanzw-0 kAmzzR StyledSpacing-sc-wahrw5-0 cHhFWW">
#                                         <img alt="Go Logo" height="12" src="/docs/icons/go.svg"
#                                             width="32" /></div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div class="Text__StyledText-sc-6aor3p-0 cBFSFL"
#                                         color="primary" size="3">Go</div>
#                                     <div class="Text__StyledText-sc-6aor3p-0 ieZVsm"
#                                         color="secondary" size="3">client-go</div>
#                                 </div>
#                             </div>
#                         </a></div>
#                     <div><a class="repoLink__StyledLink-sc-qaanzw-1 erDtuF"
#                             href="https://github.com/polygon-io/client-js"
#                             rel="nofollow noreferrer" target="_blank">
#                             <div class="Container__StyledContainer-sc-83etil-0 cibvzg StyledSpacing-sc-wahrw5-0 hYiXxL"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div
#                                         class="repoLink__ImageWrapper-sc-qaanzw-0 kAmzzR StyledSpacing-sc-wahrw5-0 cHhFWW">
#                                         <img alt="Javascript Logo" height="24"
#                                             src="/docs/icons/javascript.svg" width="24" /></div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div class="Text__StyledText-sc-6aor3p-0 cBFSFL"
#                                         color="primary" size="3">Javascript</div>
#                                     <div class="Text__StyledText-sc-6aor3p-0 ieZVsm"
#                                         color="secondary" size="3">client-js</div>
#                                 </div>
#                             </div>
#                         </a></div>
#                     <div><a class="repoLink__StyledLink-sc-qaanzw-1 erDtuF"
#                             href="https://github.com/polygon-io/client-php"
#                             rel="nofollow noreferrer" target="_blank">
#                             <div class="Container__StyledContainer-sc-83etil-0 cibvzg StyledSpacing-sc-wahrw5-0 hYiXxL"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div
#                                         class="repoLink__ImageWrapper-sc-qaanzw-0 kAmzzR StyledSpacing-sc-wahrw5-0 cHhFWW">
#                                         <img alt="PHP Logo" height="16"
#                                             src="/docs/icons/php.svg" width="31" /></div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div class="Text__StyledText-sc-6aor3p-0 cBFSFL"
#                                         color="primary" size="3">PHP</div>
#                                     <div class="Text__StyledText-sc-6aor3p-0 ieZVsm"
#                                         color="secondary" size="3">client-php</div>
#                                 </div>
#                             </div>
#                         </a></div>
#                     <div><a class="repoLink__StyledLink-sc-qaanzw-1 erDtuF"
#                             href="https://github.com/polygon-io/client-jvm"
#                             rel="nofollow noreferrer" target="_blank">
#                             <div class="Container__StyledContainer-sc-83etil-0 cibvzg StyledSpacing-sc-wahrw5-0 hYiXxL"
#                                 spacing="0">
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div
#                                         class="repoLink__ImageWrapper-sc-qaanzw-0 kAmzzR StyledSpacing-sc-wahrw5-0 cHhFWW">
#                                         <img alt="Kotlin Logo" height="24"
#                                             src="/docs/icons/kotlin.svg" width="24" /></div>
#                                 </div>
#                                 <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq"
#                                     order="0">
#                                     <div class="Text__StyledText-sc-6aor3p-0 cBFSFL"
#                                         color="primary" size="3">Kotlin</div>
#                                     <div class="Text__StyledText-sc-6aor3p-0 ieZVsm"
#                                         color="secondary" size="3">client-jvm</div>
#                                 </div>
#                             </div>
#                         </a></div>
#                 </div>
#             </div>
#         </div>
#     </div>
# </div>

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
        soup = BeautifulSoup(file.read(), 'html.parser')
    api_overview_md = "# Stocks API Documentation\n\n"

    overview_section = soup.find('div', class_='ScrollTrackedSection__ScrollTargetWrapper-sc-1r3wlr6-0')
    if overview_section:
        h1 = overview_section.find('h1', class_='Text__StyledText-sc-6aor3p-0')
        if h1:
            api_overview_md += f"## {h1.get_text().strip()}\n\n"

        sections = ['Authentication', 'Usage', 'Response Types']
        for section_title in sections:
            section = overview_section.find('h3', text=section_title)
            if section:
                api_overview_md += f"### {section.get_text().strip()}\n\n"
                # Find all paragraphs and code blocks within the section
                content_elements = section.find_next_siblings(['p', 'div'], limit=2)
                for element in content_elements:
                    if element.name == 'p':
                        api_overview_md += f"{element.get_text().strip()}\n\n"
                    elif element.name == 'div' and 'Copy__Background-sc-71i6s4-0' in element.get('class', []):
                        # Extract code blocks from the div
                        code_blocks = element.find_all('span', class_='Text__StyledText-sc-6aor3p-0')
                        for code_block in code_blocks:
                            if 'kjHyPJ' in code_block.get('class', []):  # This class is used for inline code in the HTML
                                code_text = code_block.get_text().strip()
                                # Replace placeholder with YOUR_API_KEY_HERE
                                if 'apiKey=*' in code_text:
                                    code_text = code_text.replace('apiKey=*', 'apiKey=YOUR_API_KEY_HERE')
                                if '<token>' in code_text:
                                    code_text = code_text.replace('<token>', 'YOUR_API_KEY_HERE')
                                api_overview_md += f"```\n{code_text}\n```\n\n"
    os.makedirs('output/markdown', exist_ok=True)
    with open('output/markdown/api_overview.md', 'w') as file:
        file.write(api_overview_md)

if __name__ == '__main__':
    url = 'https://polygon.io/docs/stocks/getting-started'
    soup = parse_html_document(url)
    remove_first_nav_element(soup)
    extract_and_save_main_nav(soup)
    extract_and_save_main_content(soup)
    create_api_overview_markdown()
    find_anchors_and_corresponding_divs()

