import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


def wait_for_file(file_path, timeout = 1000):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 1000:
                return True
        time.sleep(2)
    return False

restart_threshold = 50

# ==========> Customize script params STARTs here <==========
input_folder = "../../files/offset/"
output_folder = "../../files/offset/output/"
log_file = "process_pdf_logs.log"
# ==========> Customize script params ENDs here <==========

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("=== Script started ===")
os.makedirs(output_folder, exist_ok=True)

geckodriver_path = "/usr/local/bin/geckodriver"
firefox_profile_path = "/home/node0/snap/firefox/common/.mozilla/firefox/rznn2zjo.default"

def start_firefox():
    firefox_options = Options()
    firefox_options.binary_location = "/usr/bin/firefox"
    firefox_options.add_argument("-profile")
    firefox_options.add_argument(firefox_profile_path)
    firefox_options.add_argument("--headless")

    firefox_options.set_preference("print.always_print_silent", True)
    firefox_options.set_preference("print.show_print_progress", True)
    firefox_options.set_preference("print.save_as_pdf", True)
    firefox_options.set_preference("print_printer", "Mozilla Save to PDF")
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    firefox_options.set_preference("print.print_to_file", True)
    firefox_options.set_preference("print.printer_Mozilla_Save_to_PDF.print_to_filename",
                                   "/home/node0/Downloads/output.pdf")

    print("Starting Firefox WebDriver...")
    logging.info("Starting Firefox WebDriver...")
    service = Service(geckodriver_path)
    return webdriver.Firefox(service=service, options=firefox_options)

pdf_files = sorted(f for f in os.listdir(input_folder) if f.endswith(".pdf"))
logging.info(f"Found {len(pdf_files)} PDF files for processing.")
processed_cnt = 0
skipped_cnt = 0
driver = start_firefox()
for filename in pdf_files:
    input_path = f"file://{os.path.abspath(os.path.join(input_folder, filename))}"
    output_path = os.path.join(output_folder, filename)
    if os.path.exists(output_path):
        logging.info(f"Skipping {filename} (already processed)")
        skipped_cnt += 1
        continue
    temp_output_path = "/home/node0/Downloads/output.pdf"
    print(f"Processing: {filename}")
    logging.info(f"Processing: {filename}")
    print(f"File size: {os.path.getsize(os.path.join(input_folder, filename)) / 1024} KB")
    logging.info(f"File size: {os.path.getsize(os.path.join(input_folder, filename)) / 1024} KB")

    try:
        driver.get(input_path)
        time.sleep(5)

        print("Triggering print command...")
        logging.info("Triggering print command...")
        driver.execute_script("window.print();")
        time.sleep(3)
        processed_cnt += 1

        if wait_for_file(temp_output_path):
            os.rename(temp_output_path, output_path)
            print(f"Saved printed PDF: {output_path}")
            logging.info(f"Saved printed PDF: {output_path}")
            print(f"{processed_cnt} files have been processed, {skipped_cnt} files have been skipped, {len(pdf_files) - processed_cnt - skipped_cnt} files remained.")
            logging.info(f"{processed_cnt} files have been processed, {skipped_cnt} files have been skipped, {len(pdf_files) - processed_cnt - skipped_cnt} files remained.")
        else:
            print(f"Failed to save: {filename}")
            logging.warning(f"Failed to save: {filename}")
    except Exception as e:
        processed_cnt += 1
        logging.error(f"Error processing {filename}: {str(e)}")
        logging.info("Firefox crashed. Restarting WebDriver...")
        driver.quit()
        time.sleep(5)
        driver = start_firefox()
        continue

    if processed_cnt % restart_threshold == 0:
        logging.info("Restarting Firefox to prevent crashes...")
        driver.quit()
        time.sleep(5)
        driver = start_firefox()

print("Batch processing complete!")
logging.info(f"Total files processed: {processed_cnt}")
logging.info(f"Total files skipped: {skipped_cnt}")
logging.info(f"Total files found: {len(pdf_files)}")
logging.info("=== Script finished ===")
driver.quit()

os.system("shutdown -h +1")