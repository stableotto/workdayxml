import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import multiprocessing.dummy as multiprocessing
import tqdm

from .parse_args import parse_args
from .rss_funcs import generate_rss
from .email_funcs import compose_email, send_email


def clean_html(html_content):
    """Clean up the HTML content to remove unnecessary elements and preserve formatting."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove all SVG elements
    for svg in soup.find_all('svg'):
        svg.decompose()
        
    # Remove unnecessary nested divs while preserving content
    for div in soup.find_all('div', recursive=True):
        if div.find_all('div') and not div.find(['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            div.unwrap()
    
    # Clean up empty elements
    for element in soup.find_all(['div', 'p', 'span']):
        if not element.get_text(strip=True) and not element.find(['img', 'br']):
            element.decompose()
    
    # Add proper styling
    job_description_div = soup.new_tag('div')
    job_description_div['class'] = 'job-description'
    
    # Move all content into the job description div
    for element in soup.body.contents[:]:
        job_description_div.append(element.extract())
    
    soup.body.append(job_description_div)
    
    # Convert the cleaned HTML back to a string
    cleaned_html = str(job_description_div)
    
    # Add CSS styles
    css_styles = """
        <style>
            .job-description {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .job-description h1, .job-description h2, .job-description h3 {
                color: #2557a7;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                font-weight: 600;
            }
            .job-description ul, .job-description ol {
                margin: 1em 0;
                padding-left: 2em;
            }
            .job-description li {
                margin: 0.5em 0;
                line-height: 1.6;
                list-style-type: disc;
            }
            .job-description p {
                margin: 1em 0;
                line-height: 1.6;
            }
            .job-description b, .job-description strong {
                color: #2557a7;
                font-weight: 600;
            }
            .job-description a {
                color: #2557a7;
                text-decoration: none;
            }
            .job-description a:hover {
                text-decoration: underline;
            }
        </style>
    """
    
    return f"{css_styles}\n{cleaned_html}"


def read_file(file):
    company_urls = {}
    with open(f"configs/{file}", "r") as inputfile:
        for line in inputfile:
            name, url = line.strip().split(",")
            company_urls[name] = url
    return company_urls


def get_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_job_posting(jobtosend, company, seturl):
    max_retries = 3
    while max_retries > 0:
        try:
            driver = get_driver()
            wait = WebDriverWait(driver, 10)
            job_title = jobtosend[0]
            job_href = jobtosend[1]
            job_location_text = jobtosend[2]
            driver.get(job_href)
            time.sleep(1)
            job_posting_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@data-automation-id="job-posting-details"]')
                )
            )
            # Get the raw HTML and clean it
            job_posting_html = job_posting_element.get_attribute('outerHTML')
            cleaned_html = clean_html(job_posting_html)
            
            driver.close()
            
            # Clean the job title by removing company name and any leading/trailing whitespace
            clean_job_title = job_title
            if company in job_title:
                clean_job_title = job_title.replace(company, '').strip()
            # Remove any remaining colons and clean up whitespace
            clean_job_title = clean_job_title.replace(':', '').strip()
            
            job_info = {
                "company": company,
                "company_url": seturl,
                "job_title": clean_job_title,
                "job_href": job_href,
                "job_posting_html": cleaned_html,  # Store cleaned HTML
                "job_location": job_location_text,
            }
            return job_info
        except Exception as e:
            print(f"Failed! Error: {str(e)}")
            max_retries -= 1
            return None


def main():
    args = parse_args()
    file = args["file"]
    initial = args["initial"]
    no_json = args["no-json"]
    no_rss = args["no-rss"]

    # Load or initialize job_ids_dict from file
    try:
        with open("job_ids_dict.pkl", "rb") as f:
            job_ids_dict = pickle.load(f)
    except FileNotFoundError:
        job_ids_dict = {}

    company_urls = read_file(file)

    for company in company_urls:
        if company_urls[company] not in job_ids_dict:
            job_ids_dict[company_urls[company]] = []

    driver = get_driver()
    wait = WebDriverWait(driver, 10)

    jobs = []
    for company in company_urls:
        print(f"Scraping {company}...")
        company_url = company_urls[company]
        jobstosend = []
        driver.get(company_url)
        seturl = company_url
        try:
            today = True
            while today or initial:
                time.sleep(2)
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//li[@class="css-1q2dra3"]')
                    )
                )

                job_elements = driver.find_elements(
                    By.XPATH, '//li[@class="css-1q2dra3"]'
                )

                for job_element in job_elements:
                    job_title_element = job_element.find_element(By.XPATH, ".//h3/a")
                    job_id_element = job_element.find_element(
                        By.XPATH, './/ul[@data-automation-id="subtitle"]/li'
                    )
                    job_id = job_id_element.text
                    posted_on_element = job_element.find_element(
                        By.XPATH,
                        './/dd[@class="css-129m7dg"][preceding-sibling::dt[contains(text(),"posted on")]]',
                    )
                    posted_on = posted_on_element.text

                    # Scrape job location
                    try:
                        job_location_container = job_element.find_element(By.CLASS_NAME, "css-248241")
                        job_location_text = job_location_container.find_element(By.CLASS_NAME, "css-129m7dg").text
                    except Exception as e:
                        print(f"Could not find location for a job in {company}: {e}")
                        job_location_text = "Not found" # Default if not found

                    if "posted today" in posted_on.lower() or initial:
                        job_href = job_title_element.get_attribute("href")
                        job_title = job_title_element.text
                        if job_id not in job_ids_dict[company_url]:
                            job_ids_dict[company_url].append(job_id)
                            jobstosend.append((job_title, job_href, job_location_text))
                        else:
                            print(f"Job ID {job_id} already in job_ids_dict.")
                    else:
                        today = False
                try:
                    next_button = driver.find_element(
                        By.XPATH, '//button[@data-uxi-element-id="next"]'
                    )
                    if "disabled" in next_button.get_attribute("class"):
                        break  # exit loop if the "next" button is disabled
                    next_button.click()
                except:
                    break

        except Exception as e:
            print(f"An error occurred while processing {company_url}: {str(e)}")
            continue

        print(f"Found {len(jobstosend)} jobs for {company}.")

        # for job_info in jobstosend:
        #     job_info = scrape_job_posting(job_info, company, seturl)
        #     jobs.append(job_info)

        with multiprocessing.Pool() as pool, tqdm.tqdm(total=len(jobstosend)) as pbar:
            params = [(jobtosend, company, seturl) for jobtosend in jobstosend]
            for job_info in pool.starmap(scrape_job_posting, params):
                if job_info is not None:
                    jobs.append(job_info)
                pbar.update()

    print("Done scraping.")

    # Write job postings to a JSON file
    if not no_json:
        jsondata = json.dumps(jobs, indent=4)
        with open("job_postings.json", "w") as jsonfile:
            jsonfile.write(jsondata)

    # Write job postings to an RSS file
    if not no_rss:
        with open("rss.xml", "w") as rssfile:
            rssfile.write(generate_rss(jobs))

    # Save job_ids_dict to file
    with open("job_ids_dict.pkl", "wb") as f:
        pickle.dump(job_ids_dict, f)

    print("Files written.")

    # Send an email if option given
    sender = args["email"]
    if sender and len(jobs) > 0:
        subject = "Workday Scraper: Today's Jobs"
        body = compose_email(jobs)
        recipients = args["recipients"].split(",")
        password = args["password"]
        send_email(subject, body, sender, recipients, password)
        print("Email sent.")


if __name__ == "__main__":
    main()
