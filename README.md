# Marktplaats Bike Scraper

A Python-based web scraper that automatically collects bike listings data from Marktplaats.nl and stores it in Google Drive. The scraper monitors racing bike listings, extracts detailed information, and can continuously check for new listings.

## Features

- Scrapes detailed bike listing information including:
  - Upload date/time
  - Seller information
  - Ad title and description
  - Price
  - Frame size
  - Condition
  - Number of gears
  - Frame material
  - Brand
  - Location
  - Ad ID
- Automatic Google Drive integration for data storage
- Option to scrape all pages or just the first page
- Continuous monitoring for new listings (4-hour intervals)
- Handles both new file creation and updates to existing files
- Robust error handling and retry mechanisms

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account
- Chrome browser installed
- Chrome WebDriver matching your Chrome version

## Installation

1. Clone the repository:
   
```git clone https://github.com/SafeerAbbas624/Marktplaats_Bike_Scraper.git```
```cd marktplaats-bike-scraper```

3. Install required packages:
   
```pip install -r requirements.txt```

5. Set up Google Cloud Platform:
   - Create a new project in Google Cloud Console
   - Enable the Google Drive API
   - Create a service account and download the JSON credentials
   - Rename the credentials file to `bikescraper.json` and place it in the project root directory

## Configuration

1. Update the following constants in `bike.py`:
```
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'bikescraper.json'
DRIVE_FILE_NAME = 'listings.csv'
FOLDER_ID = "your_google_drive_folder_id"
```
2. Create a `requirements.txt` file with the following dependencies:
```
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
selenium==4.15.2
google-auth==2.23.4
httplib2==0.22.0
oauthlib==3.2.2
requests==2.31.0
urllib3==2.0.7
webdriver-manager==4.0.1
```

## Usage

Run the script using Python:
bash
```python bike.py```

When prompted, choose:
- `YES` to scrape all pages, then monitor for new ads every 4 hours
- `NO` to scrape only the first page, then monitor for new ads every 4 hours

## Data Structure

The scraper collects the following information for each listing:

| Field | Description |
|-------|-------------|
| Uploaded Date/Time | When the listing was posted |
| User Name | Seller's username |
| Ad Name | Title of the listing |
| Ad Description | Full description of the bike |
| Ad Price | Listed price |
| Frame Size | Size of the bike frame |
| Condition | Condition of the bike |
| Number of Gears | Number of gears on the bike |
| Material of the Frame | Frame material |
| Brand | Bike manufacturer |
| Ad ID | Unique identifier for the listing |
| Location | Geographic location |
| Page Number | Page where the listing was found |
| Link | URL to the original listing |

## File Storage

- Data is stored in a CSV file named `listings.csv`
- The file is automatically uploaded to Google Drive
- A temporary file `temp_listings.csv` is used for checking new listings

## Error Handling

The script includes comprehensive error handling for:
- Network issues
- Missing webpage elements
- Google Drive API errors
- File operations
- Browser automation issues

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This scraper is for educational purposes only. Please review Marktplaats.nl's terms of service and robots.txt before using this scraper. Ensure you comply with their scraping policies and rate limits.

## Support

For support, please open an issue in the GitHub repository or contact [https://github.com/SafeerAbbas624].


