from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
import io
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
from datetime import datetime, timedelta, timezone

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'bikescraper.json'
DRIVE_FILE_NAME = 'listings.csv'
FOLDER_ID = "your_google_drive_folder_id"

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)


def upload_file(service, filename, filepath, mimetype, folder_id, file_id=None):
    media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
    
    if file_id:
        # Update the existing file
        file = service.files().update(
            fileId=file_id,
            media_body=media,
            addParents=folder_id,  # Add the folder as a parent
            fields='id'  # Only return the file ID
        ).execute()
        print(f'Updated file ID: {file.get("id")}')
    else:
        # Create a new file
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f'Created file ID: {file.get("id")}')
    
    return file.get('id')



def download_file(service, file_id, filepath):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    
    with io.open(filepath, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())

# Set up the browser options
options = Options()
options.add_argument("--disable-gpu")
options.add_argument('log-level=3')

# Set up the browser
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

def read_csv(filename):
    existing_data = []
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_data = list(reader)
    except FileNotFoundError:
        print("No existing CSV file found. Starting fresh.")
    return existing_data



def get_element_text(wait, element_id):
    """Get text from an element"""
    element = wait.until(EC.element_to_be_clickable((By.XPATH, element_id)))
    return element.text

def scrape_listing(wait, driver, link, page_number):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(link)
    time.sleep(10)
    
    data = {
        "Uploaded Date/Time": "",
        "User Name": "",
        "Ad Name": "",
        "Ad Description": "",
        "Ad Price": "",
        "Frame Size": "",
        "Condition": "",
        "Number of Gears": "",
        "Material of the Frame": "",
        "Brand": "",
        "Ad ID": "",
        "Location": "",
        "Page Number": page_number,
        "Link": link
    }
    
    # Extract the required fields (using try-except to handle missing elements)
    try:
        date_time = get_element_text(wait, '//*[@id="listing-root"]/div/div[3]/span[3]/span')
        date = date_time.split()
        data["Uploaded Date/Time"] = " ".join(date[1:])
    except Exception:
        data["Uploaded Date/Time"] = ""
        pass
    try:
        data["User Name"] = get_element_text(wait, '//*[@id="seller-sidebar-root"]/div[1]/div[1]/div[1]/span/a')
    except Exception:
        data["User Name"] = ''
        pass
    try:
        data["Ad Name"] = get_element_text(wait, '//*[@id="listing-root"]/div/header/h1')
    except Exception:
        data["Ad Name"] = ''
        pass
    try:
        data["Ad Description"] = get_element_text(wait, '//*[@id="page-wrapper"]/div[3]/div[2]/section[1]/div[1]/div[6]/div[1]/div[1]')
    except Exception:
        data["Ad Description"] = ''
        pass

    try:
        price = get_element_text(wait, '//*[@id="listing-root"]/div/div[2]/div[1]')
        if 'Zie' in price:
            data["Ad Price"] = ''
        else:
            data['Ad Price'] = price
    except Exception:
        data["Ad Price"] = ''
        pass


    try:
        for i in range(1, 6):
            xpath = f'(//div[@class="Attributes-item "])[{i}]'
            fields = get_element_text(wait, xpath)
            if 'Conditie' in fields:
                field = fields.split()
                data["Condition"] = " ".join(field[1:])
            elif 'Framehoogte' in fields:
                field = fields.split()
                data["Frame Size"] = " ".join(field[1:])
            elif 'Aantal versnellingen' in fields:
                field = fields.split()
                data["Number of Gears"] = " ".join(field[1:])
            elif 'Materiaal' in fields:
                field = fields.split()
                data["Material of the Frame"] = " ".join(field[1:])
            elif 'Merk' in fields:
                field = fields.split()
                data["Brand"] = " ".join(field[1:])
    except Exception:
        pass
    try:
        data["Ad ID"] = get_element_text(wait, '//*[@id="page-wrapper"]/div[3]/div[2]/div[2]/nav/span')
    except Exception:
        data["Ad ID"] = ''
        pass
    try:
        data["Location"] = get_element_text(wait, '//*[@id="seller-sidebar-root"]/div[1]/div[3]/div[1]/button')
    except Exception:
        data["Location"] = ''
        pass
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return data

def download_existing_file(service, folder_id, filename):
    # Search for the existing file in the specified folder
    query = f"'{folder_id}' in parents and name='{filename}'"
    results = service.files().list(q=query, fields="files(id)").execute()
    items = results.get('files', [])

    if items:
        file_id = items[0]['id']
        download_file(service, file_id, filename)  # Download the existing file
        print(f'Downloaded existing file: {filename} with ID: {file_id}')
        return file_id  # Return the file ID
    else:
        print(f'No existing file found: {filename}')
        return None  # Return None if the file does not exist

def save_to_csv_and_upload(service, data, folder_id, filename=DRIVE_FILE_NAME, file_id=None):
    # Check if the file already exists and get its ID
    if file_id is None:
        file_id = download_existing_file(service, folder_id, filename)

    # Read existing data if the file exists
    existing_data = []
    if file_id:
        existing_data = read_csv(filename)  # Read existing data if file exists

    # Combine existing data with new data
    existing_data.extend(data)

    # Write combined data to the CSV file
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=existing_data[0].keys() if existing_data else [])
        writer.writeheader()
        writer.writerows(existing_data)

    # Upload the updated file
    try:
        file_id = upload_file(service, filename, filename, 'text/csv', folder_id, file_id)
        print(f'Successfully uploaded file with ID: {file_id}')
    except Exception as e:
        print(f"Error uploading file: {e}")
    
    return file_id

all_pages = input('\nDo You want to scrape all pages?\nIf you say "YES" it will scrape all pages then wait for 4 hours, then check for new ads.\nIf you say "NO" it will scrape first page only, wait for 4 hours and check for new ads.\nSelect YES or NO: ').lower()

# Main function to control the flow
def main():
    service = get_drive_service()
    # folder_id = get_or_create_folder(service, FOLDER_NAME)
    folder_id = FOLDER_ID
    filename = DRIVE_FILE_NAME
    file_id = None
    print(folder_id)
    print('1cM7SliGhgxVppVu7ZBklmiWFB-EvgW-E')
    
    # Opening link on browser
    driver.get("https://www.marktplaats.nl/l/fietsen-en-brommers/fietsen-racefietsen/")
    # time to wait for page loading
    time.sleep(8)
    
    # Logic to go for all pages extracting and then looking for news ads only, if input is yes.
    if all_pages == 'yes':
        # Variable to get page number
        page_number = 1
        # While loop for going all the pages one by one.
        for i in range(2, 427):
            # Try except to check for page end and check for new ads in except block in one hour interval.
            try:
                # getting links of listings on each page in range loop 
                links = []
                for i in range(1, 36):
                    try:
                        xpath = f'(//ul[@class="hz-Listings hz-Listings--list-view"]/li[@class="hz-Listing hz-Listing--list-item"]/div/div/a[@class="hz-Link hz-Link--block hz-Listing-coverLink"])[{i}]'
                        link = driver.find_element(By.XPATH, xpath).get_attribute("href")
                        # checking the link is none or not. if none it will not be appended
                        if link is not None:
                            links.append(link)
                    # Breaking loop if range of listings ended.
                    except NoSuchElementException:
                        print(f"\ntotal listings found on page: {page_number} are: " + str(len(links)))
                        break
                print(f'Total links found on page number {page_number} are: '+ str(len(links)))
                try:
                    # links appended is looped again to go on that page and run scraping function and put data into csv.
                    all_data = []
                    link_num = 1
                    for link in links:
                        print(f'Scraping now link number: {link_num}')
                        data = scrape_listing(wait, driver, link, page_number)
                        all_data.append(data)
                        link_num += 1

                    file_id = save_to_csv_and_upload(service, all_data, folder_id, filename, file_id)
                    print('data saved to csv and uploaded to Google Drive')
                except Exception as e:
                    print(f"An error occurred: {e}")
                
                # clicking on next page
                driver.get(f'https://www.marktplaats.nl/l/fietsen-en-brommers/fietsen-racefietsen/p/{i}/')
                page_number += 1
                print(f'Going on next page: number {page_number}')
                time.sleep(10)
            # except block to stop pages running and checking for the new ads.
            except Exception:
                pass
        print('All pages data has been extracted.\nNow waiting for 4 hours and look for new ads.')
                # Sleep for 4 hours and repeat
        while True:
            time.sleep(14400)
            driver.get("https://www.marktplaats.nl/l/fietsen-en-brommers/fietsen-racefietsen/")
            time.sleep(8)
            download_file(service, file_id, 'temp_listings.csv')
            existing_data = read_csv('temp_listings.csv')
            existing_links = set(item['Link'] for item in existing_data)
            new_links = []
            for i in range(1, 36):
                try:
                    xpath = f'(//ul[@class="hz-Listings hz-Listings--list-view"]/li[@class="hz-Listing hz-Listing--list-item"]/div/div/a[@class="hz-Link hz-Link--block hz-Listing-coverLink"])[{i}]'
                    link = driver.find_element(By.XPATH, xpath).get_attribute("href")
                    # checking the link is none or not. if none it will not be appended
                    if link is not None:
                        new_links.append(link)
                    # Breaking loop if range of listings ended.
                except Exception:
                    print(f"\ntotal listings found on page are: " + str(len(new_links))+"\n")
                    break
            print(f'Total links found on page number {page_number} are: '+ str(len(new_links)))
            # links appended is looped again to go on that page and run scraping function and put data into csv.
                    
            new_data = []
            for link in new_links:
                if link not in existing_links:
                    data = scrape_listing(wait, driver, link, page_number)
                    new_data.append(data)
                    existing_links.add(link)
                    print(f"New ad found: {data['Ad Name']}")
                else:
                    print('No New ad found.')
                    
            if new_data:
                file_id = save_to_csv_and_upload(service, all_data, folder_id, filename, file_id)
                print('New data saved to csv and uploaded to Google Drive')
                print('Checked all the links. Now waiting for 4 hours.')

    # go for else if input is no and get the listings of first page and then check for new ads with interval time of one hour
    else:
        # Variable to get page number
        page_number = 1
        # getting links of listings on each page in range loop 
        links = []
        for i in range(1, 36):
            try:
                xpath = f'(//ul[@class="hz-Listings hz-Listings--list-view"]/li[@class="hz-Listing hz-Listing--list-item"]/div/div/a[@class="hz-Link hz-Link--block hz-Listing-coverLink"])[{i}]'
                link = driver.find_element(By.XPATH, xpath).get_attribute("href")
                # checking the link is none or not. if none it will not be appended
                if link is not None:
                    links.append(link)
            # Breaking loop if range of listings ended.
            except Exception:
                print(f"\ntotal listings found on First page are: " + str(len(links))+"\n")
                break
              
        print(f'Total links found on page number {page_number} are: '+ str(len(links)))
        # links appended is looped again to go on that page and run scraping function and put data into csv.
        
        all_data = []
        link_num = 1
        for link in links:
            print(f'Scraping now link number: {link_num}')
            data = scrape_listing(wait, driver, link, page_number)
            all_data.append(data)
            link_num += 1
        file_id = save_to_csv_and_upload(service, all_data, folder_id, filename, file_id)
        print('All listings on first page data has been extracted and uploaded to Google Drive.\nNow waiting for 4 hours and look for new ads.')
        # Sleep for 4 hours and repeat
        while True:
            time.sleep(14400)
            driver.get("https://www.marktplaats.nl/l/fietsen-en-brommers/fietsen-racefietsen/")
            time.sleep(8)
            download_file(service, file_id, 'temp_listings.csv')
            existing_data = read_csv('temp_listings.csv')
            existing_links = set(item['Link'] for item in existing_data)
            new_links = []
            for i in range(1, 36):
                try:
                    xpath = f'(//ul[@class="hz-Listings hz-Listings--list-view"]/li[@class="hz-Listing hz-Listing--list-item"]/div/div/a[@class="hz-Link hz-Link--block hz-Listing-coverLink"])[{i}]'
                    link = driver.find_element(By.XPATH, xpath).get_attribute("href")
                    # checking the link is none or not. if none it will not be appended
                    if link is not None:
                        new_links.append(link)
                # Breaking loop if range of listings ended.
                except Exception:
                    print(f"\ntotal listings found on First page are: " +str(len(new_links))+"\n")
                    break
                
            # links appended is looped again to go on that page and run scraping function and put data into csv.
            
            new_data = []
            for link in new_links:
                if link not in existing_links:
                    data = scrape_listing(wait, driver, link, page_number)
                    new_data.append(data)
                    existing_links.add(link)
                    print(f"New ad found: {data['Ad Name']}")
                else:
                    print('No New ad found.')
            
            if new_data:
                file_id = save_to_csv_and_upload(service, all_data, folder_id, filename, file_id)
                print('New data saved to csv and uploaded to Google Drive')
            print('Checked all the links. Now waiting for 4 hours.')

if __name__ == "__main__":
    main()

