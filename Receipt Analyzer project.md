The goal of the project is to build a web app that can receive a link to a receipt, scrap the HTML from that link to get the details in it, such as the date of the receipt, the items on the receipt with the price of each, etc. At the first stage we just want to update a google sheets document with the items(logic for which cells to update still needed to be decided).

## Technologies

- Front End - react + vite
- Backend - Python(FastAPI)

## Architecture
- Monorepo that includes a frontend and a backend folders
## UI
- The main Language should be Hebrew(RTL Support), the second one is English
- The UI should be minimalistic and clean. On the main page of the application there will be an input to paste a link to the receipt. After pasting the link and clicking on "Send receipt button".
- There should be a loading effect after clicking the button.
- Display errors if the are any

## Backend
- Using Python with FastAPI for the server
- Support an endpoint for receiving the link, extracting the data from it, and updating the relevant google sheet document.
