# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started

# 2.) The First nav element is the header, which can be discarded

# 3.) The Second nav element is the main navigation (side bar) which contains links and hierarchy to the various endpoints.
#     Convert this to a markdown file and maintain the hierarchy defined in the html.
#     Save the markdown to a file called "navigation.md"


