# This application is responsible for converting the Polygon.io API documentation to an OPEN API 3.0 specification.
# The source of the documentation is on the polygon.io website in html form.
# The application will parse the html and minimize content to only the relevant information required to generate the Open API Spec.

# 1.) Parse the html document found at https://polygon.io/docs/stocks/getting-started and extract the anchors out of the fith <div/> element. These anchors will be our urls for differnet documentations (stocks, forex, crypto, etc.)

# 2.) Print the anchors so we can see what we are working with.
