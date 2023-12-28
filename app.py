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
import re

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
            required_text = "<span style='color: red'>*</span>" if is_required else ""
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
    return re.sub(r'[^\w\s-]', '_', name)

def find_anchors_and_corresponding_divs():
    with open('body.html', 'r') as file:
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
                with open(f'{endpoint_name}_endpoint.html', 'w') as file:
                    file.write(str(endpoint_element))
                heading_markdown = endpoint_heading(anchor)
                parameters_markdown = endpoint_parameters(endpoint_element)
                with open(f'{endpoint_name}_endpoint.md', 'w') as file:
                    file.write(heading_markdown + parameters_markdown)


# Create a generic function called endpointHeading that uses the classes of the ELEMENT to pick it out and parse out the POINTS_OF_INTEREST in this FORMAT.
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

# Create a gneric function called endpointParameters that uses the classes of the ELEMENT using the CONSIDERATIONS.
# CONSIDERATIONS
# -The heading should always be named Parameters
# -Some Parameters have a * at the end indicating they are required. this can have an impact on formatting but it is important to indicate what params are required in md.
# -Some parameters are accept fixed values usually in the form of menu items. These <li> tags should be preserved.
# ELEMENT
# <div class="StyledSpacing-sc-wahrw5-0 jpImIW">
# <div class="Text__StyledText-sc-6aor3p-0 eXjcsS StyledSpacing-sc-wahrw5-0 hKvqOb" color="inherit"
#     size="5">Parameters</div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#             <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                     class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                     color="secondary" size="2"><span class="Text__StyledText-sc-6aor3p-0 jNvGLe"
#                         color="primary" size="2">stocksTicker</span> <span
#                         class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                         size="2">*</span></label>
#                 <div class="Input__InputContainer-sc-c1zkxq-0 gwDeuf"><input
#                         class="Input__StyledInput-sc-c1zkxq-1 kuOwsY"
#                         name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_stocksTicker"
#                         placeholder="" type="text" /></div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>Specify a case-sensitive ticker symbol. For example, AAPL represents Apple Inc.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#             <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                     class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                     color="secondary" size="2"><span class="Text__StyledText-sc-6aor3p-0 jNvGLe"
#                         color="primary" size="2">multiplier</span> <span
#                         class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                         size="2">*</span></label>
#                 <div class="Input__InputContainer-sc-c1zkxq-0 gwDeuf"><input
#                         class="Input__StyledInput-sc-c1zkxq-1 kuOwsY"
#                         name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_multiplier"
#                         placeholder="" type="number" /></div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>The size of the timespan multiplier.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div>
#             <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#                 <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                         class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                         color="secondary" for="bqcr0085zqu" size="2"><span
#                             class="Text__StyledText-sc-6aor3p-0 jNvGLe" color="primary"
#                             size="2">timespan</span> <span class="Text__StyledText-sc-6aor3p-0 iBsCAz"
#                             color="danger" size="2">*</span></label><button
#                         class="indexstyles__SelectWrapper-sc-1r27fmm-0 kjFlhD" type="button"><span
#                             class="indexstyles__StyledSelect-sc-1r27fmm-1 bPlNsp" id="bqcr0085zqu"
#                             name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_timespan"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ieZVsm" color="secondary"
#                                 size="3"></span></span><i
#                             class="indexstyles__Icon-sc-1r27fmm-5 jyRPIT fas fa-caret-down"></i></button>
#                     <menu class="indexstyles__OptionList-sc-1r27fmm-2 cxxLoj"
#                         style="position:absolute;left:0;top:0">
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">second</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">minute</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">hour</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">day</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">week</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">month</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">quarter</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">year</span></button></li>
#                     </menu>
#                 </div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>The size of the time window.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#             <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                     class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                     color="secondary" size="2"><span class="Text__StyledText-sc-6aor3p-0 jNvGLe"
#                         color="primary" size="2">from</span> <span
#                         class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                         size="2">*</span></label>
#                 <div class="Input__InputContainer-sc-c1zkxq-0 gwDeuf"><input
#                         class="Input__StyledInput-sc-c1zkxq-1 kuOwsY"
#                         name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_from"
#                         placeholder="" type="text" /></div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>The start of the aggregate time window. Either a date with the format YYYY-MM-DD or a
#             millisecond timestamp.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#             <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                     class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                     color="secondary" size="2"><span class="Text__StyledText-sc-6aor3p-0 jNvGLe"
#                         color="primary" size="2">to</span> <span
#                         class="Text__StyledText-sc-6aor3p-0 iBsCAz" color="danger"
#                         size="2">*</span></label>
#                 <div class="Input__InputContainer-sc-c1zkxq-0 gwDeuf"><input
#                         class="Input__StyledInput-sc-c1zkxq-1 kuOwsY"
#                         name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_to"
#                         placeholder="" type="text" /></div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>The end of the aggregate time window. Either a date with the format YYYY-MM-DD or a
#             millisecond timestamp.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div>
#             <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#                 <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                         class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                         color="secondary" for="voq111nksyh" size="2"><span
#                             class="Text__StyledText-sc-6aor3p-0 jNvGLe" color="primary"
#                             size="2">adjusted</span> </label><button
#                         class="indexstyles__SelectWrapper-sc-1r27fmm-0 kjFlhD" type="button"><span
#                             class="indexstyles__StyledSelect-sc-1r27fmm-1 bPlNsp" id="voq111nksyh"
#                             name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_adjusted"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ieZVsm" color="secondary"
#                                 size="3"></span></span><i
#                             class="indexstyles__Icon-sc-1r27fmm-5 jyRPIT fas fa-caret-down"></i></button>
#                     <menu class="indexstyles__OptionList-sc-1r27fmm-2 cxxLoj"
#                         style="position:absolute;left:0;top:0">
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3"></span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">true</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">false</span></button></li>
#                     </menu>
#                 </div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>Whether or not the results are adjusted for splits. By default, results are adjusted.
#             Set this to false to get results that are NOT adjusted for splits.</p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div>
#             <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#                 <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                         class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                         color="secondary" for="5vvru47vh7g" size="2"><span
#                             class="Text__StyledText-sc-6aor3p-0 jNvGLe" color="primary"
#                             size="2">sort</span> </label><button
#                         class="indexstyles__SelectWrapper-sc-1r27fmm-0 kjFlhD" type="button"><span
#                             class="indexstyles__StyledSelect-sc-1r27fmm-1 bPlNsp" id="5vvru47vh7g"
#                             name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_sort"><span
#                                 class="Text__StyledText-sc-6aor3p-0 ieZVsm" color="secondary"
#                                 size="3"></span></span><i
#                             class="indexstyles__Icon-sc-1r27fmm-5 jyRPIT fas fa-caret-down"></i></button>
#                     <menu class="indexstyles__OptionList-sc-1r27fmm-2 cxxLoj"
#                         style="position:absolute;left:0;top:0">
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3"></span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">asc</span></button></li>
#                         <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                 type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">desc</span></button></li>
#                     </menu>
#                 </div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>Sort the results by timestamp.
#             <code>asc</code> will return results in ascending order (oldest at the top),
#             <code>desc</code> will return results in descending order (newest at the top).
#         </p>
#     </div>
# </div>
# <div class="StyledSpacing-sc-wahrw5-0 dsgUMc">
#     <div class="Parameters__MaxWidth-sc-ize944-0 hIxfcy StyledSpacing-sc-wahrw5-0 gClFQA">
#         <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH">
#             <div class="AddOnLabel__Flex-sc-1xxztq9-0 gVBZRg"><label
#                     class="Text__StyledText-sc-6aor3p-0 eXRtXK NoWrapLabel-sc-q6mxcu-0 AddOnLabel__Label-sc-1xxztq9-1 ctLntY guPIIn"
#                     color="secondary" size="2"><span class="Text__StyledText-sc-6aor3p-0 jNvGLe"
#                         color="primary" size="2">limit</span> </label>
#                 <div class="Input__InputContainer-sc-c1zkxq-0 gwDeuf"><input
#                         class="Input__StyledInput-sc-c1zkxq-1 kuOwsY"
#                         name="/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}_limit"
#                         placeholder="" type="number" /></div>
#             </div>
#         </div>
#     </div>
#     <div class="Parameters__Description-sc-ize944-1 RrnQG StyledSpacing-sc-wahrw5-0 dsgUMc">
#         <p>Limits the number of base aggregates queried to create the aggregate results. Max 50000 and
#             Default 5000.
#             Read more about how limit is used to calculate aggregate results in our article on
#             <a alt="Aggregate Data API Improvements" href="https://polygon.io/blog/aggs-api-updates/"
#                 target="_blank">Aggregate Data API Improvements</a>.
#         </p>
#     </div>
# </div>
# <div class="base__QueryContainer-sc-127j6tq-3 hfXbJX">
#     <div class="Copy__Background-sc-71i6s4-0 cqbdLN">
#         <div class="Container__StyledContainer-sc-83etil-0 fODFXk" spacing="0">
#             <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hOBmCZ" order="0">
#                 <div class="Copy__TextWrapper-sc-71i6s4-1 bsrJTO"><span
#                         class="Text__StyledText-sc-6aor3p-0 kjHyPJ" color="inherit" height="1.3"
#                         size="2">https://api.polygon.io/v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}?apiKey=*</span>
#                 </div>
#             </div>
#             <div class="ContainerItem__StyledContainerItem-sc-1kmvqlm-0 hQPwVq" order="0"><button
#                     class="Button__StyledButton-sc-1gkx93s-0 hISVkJ Copy__StyledCopyButton-sc-71i6s4-2 kJkhwx"><span
#                         class="styles__CenteredContentSpan-sc-1vm3dn3-1 dfBape"><span
#                             class="styles__CenteredContentSpan-sc-1vm3dn3-1 styles__LoadingSpan-sc-1vm3dn3-2 dfBape eTnjgJ">Copy</span></span></button>
#             </div>
#         </div>
#     </div>
#     <div class="Container__StyledContainer-sc-83etil-0 jDgJDT" spacing="0">
#         <div class="Container__StyledContainer-sc-83etil-0 fODFXk StyledSpacing-sc-wahrw5-0 doupJv"
#             spacing="0">
#             <div class="StyledSpacing-sc-wahrw5-0 djTPsc">
#                 <div>
#                     <div class="InputWrapper__Gutter-sc-10wrlv4-0 kwcAIH"><button
#                             class="indexstyles__SelectWrapper-sc-1r27fmm-0 jgDKLw" type="button"><span
#                                 class="indexstyles__StyledSelect-sc-1r27fmm-1 bPlNsp" id="w2j5ui981eg"
#                                 value="json"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                     color="primary" size="3">JSON</span></span><i
#                                 class="indexstyles__Icon-sc-1r27fmm-5 jyRPIT fas fa-caret-down"></i></button>
#                         <menu class="indexstyles__OptionList-sc-1r27fmm-2 cxxLoj"
#                             style="position:absolute;left:0;top:0">
#                             <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                     type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                         color="primary" size="3">JSON</span></button></li>
#                             <li class="indexstyles__StyledListItem-sc-1r27fmm-3 ccpeub"><button
#                                     type="button"><span class="Text__StyledText-sc-6aor3p-0 ilOVUE"
#                                         color="primary" size="3">CSV</span></button></li>
#                         </menu>
#                     </div>
#                 </div>
#             </div><button class="Button__StyledButton-sc-1gkx93s-0 hWyDNS"><span
#                     class="styles__CenteredContentSpan-sc-1vm3dn3-1 dfBape"><span
#                         class="styles__CenteredContentSpan-sc-1vm3dn3-1 styles__LoadingSpan-sc-1vm3dn3-2 dfBape eTnjgJ">Run
#                         Query</span></span></button>
#         </div>
#     </div>
# </div>
# </div>


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
