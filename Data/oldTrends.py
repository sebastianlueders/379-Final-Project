import os
from datetime import datetime, timedelta
import pandas as pd
from pytrends.request import TrendReq
import time
import random
import requests

# Proxy configuration
username = 'user-spyhpi3or0-sessionduration-60'
password = 'K50vszVG8kyy=tExo3'
base_proxy_url = f"https://{username}:{password}@gate.smartproxy.com"
proxy_list = [f"{base_proxy_url}:{port}" for port in range(10001, 10021)]  # Ports from 10001 to 10020

# Function to test proxy (optional)
def test_proxy(proxy):
    try:
        test_url = "https://ip.smartproxy.com/json"
        result = requests.get(test_url, proxies={'https': proxy})
        print(f"Proxy test successful: {proxy}, Response: {result.json()}")
    except Exception as e:
        print(f"Proxy test failed: {proxy}, Error: {e}")

# List to store missing timeframes
missingData = []

def fetch_hourly_data_in_batches(keyword, geo='', output_folder='pytrends_output'):
    pytrends = TrendReq(hl='en-US', tz=360, proxies=proxy_list)
    start_date = datetime(2020, 12, 18)
    end_date = datetime.now()
    delta = timedelta(days=7)
    all_data = []

    while start_date < end_date:
        batch_start = start_date
        batch_end = min(start_date + delta, end_date)
        timeframe = f"{batch_start.strftime('%Y-%m-%d')} {batch_end.strftime('%Y-%m-%d')}"
        print(f"Fetching data for timeframe: {timeframe}")
        
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo, gprop='')
            batch_data = pytrends.interest_over_time()
            
            if not batch_data.empty:
                all_data.append(batch_data)
        except Exception as e:
            missingData.append(timeframe)
            print(f"Error fetching data for timeframe {timeframe}: {e}")
        
        start_date = batch_end + timedelta(days=1)  # Prevent overlap

    retry_count = 0
    max_retries = 5

    while missingData and retry_count < max_retries:
        current_round = missingData.copy()
        missingData.clear()

        for retry_timeframe in current_round:
            print(f"Retrying for missing timeframe: {retry_timeframe}")
            
            try:
                pytrends.build_payload([keyword], cat=0, timeframe=retry_timeframe, geo=geo, gprop='')
                retry_data = pytrends.interest_over_time()
                
                if not retry_data.empty:
                    all_data.append(retry_data)
                else:
                    print(f"No data available for timeframe {retry_timeframe}")
            except Exception as e:
                print(f"Failed again for timeframe {retry_timeframe}: {e}")
                missingData.append(retry_timeframe)
        
        if missingData:
            delay_minutes = random.randint(0, 10)
            print(f"Delaying next retry round by {delay_minutes} minutes...")
            time.sleep(delay_minutes * 60)
        
        retry_count += 1

    if retry_count >= max_retries:
        print("Max retries reached. Exiting...")

    if all_data:
        combined_data = pd.concat(all_data).reset_index()
        combined_data = combined_data.rename(columns={keyword: 'search_count', 'date': 'time_interval'})
        combined_data = combined_data[['time_interval', 'search_count']]
        combined_data['time_interval'] = pd.to_datetime(combined_data['time_interval'])
        combined_data = combined_data.sort_values(by='time_interval')

        os.makedirs(output_folder, exist_ok=True)
        output_file = os.path.join(output_folder, f"{keyword}_pytrends.csv")
        combined_data.to_csv(output_file, index=False)

        print(f"Hourly data saved to {output_file}")
    else:
        print("No data retrieved for the given keyword.")

if __name__ == "__main__":
    # Test all proxies before starting the main script
    for proxy in proxy_list:
        test_proxy(proxy)
    
    keyword_to_search = "Bitcoin"
    fetch_hourly_data_in_batches(keyword=keyword_to_search, geo="", output_folder="pytrends_output")