import http.client
import json
from dotenv import load_dotenv
from typing import Optional, Union
from urllib.parse import urlparse, parse_qs, quote
import os
from models.user_profile import ScrapedJobData, JobSearchParams
load_dotenv()

ACTOR_TASK_ID = 'gab-domingo~indeed-scraper-task'

def get_country_code(url: str) -> str:
    """
    Extract and validate country code from Indeed URL.
    Returns the correct country code format for the API.
    """
    parsed_url = urlparse(url)
    # Extract subdomain (e.g., 'ph' from 'ph.indeed.com')
    subdomain = parsed_url.netloc.split('.')[0]
    
    # Map of Indeed subdomains to API country codes
    country_map = {
        'ph': 'PH',  # Philippines
        'us': 'US',  # United States
        'www': 'US', # US uses www
        'uk': 'GB',  # United Kingdom
        'ca': 'CA',  # Canada
        # Add more mappings as needed
    }
    
    return country_map.get(subdomain, 'US')  # Default to US if unknown

def construct_indeed_url(job_title: str, location: str, country_code: str = 'ph') -> str:
    """
    Construct Indeed URL from job title and location parameters.
    
    Args:
        job_title (str): The job title to search for
        location (str): The location to search in
        country_code (str): Country code for Indeed domain (default: 'ph')
    
    Returns:
        str: Properly formatted Indeed URL
    """
    job_query = quote(job_title)
    location_query = quote(location)

    return f"https://{country_code}.indeed.com/jobs?q={job_query}&l={location_query}"

async def scrape_indeed_jobs(
    url: Optional[str] = None,
    search_params: Optional[JobSearchParams] = None,
    max_rows: int = 1
) -> Union[ScrapedJobData, dict]:
    """
    Scrape Indeed jobs using either a direct URL or job search parameters.
    
    Args:
        search_params (Optional[JobSearchParams]): Search parameters containing URL or job title and location
        max_rows (int): Maximum number of results to return (default: 1)
    
    Returns:
        Union[ScrapedJobData, dict]: ScrapedJobData object if successful, error dict if failed
    """
    try:
        # Validate search parameters
        if search_params is None:
            return {"error": "Search parameters must be provided"}
            
        search_params.validate_search_params()
        
        # Get the URL to scrape
        url = search_params.url if search_params.url else construct_indeed_url(
            search_params.job_title,
            search_params.location,
            'ph'  # You might want to make this configurable
        )
        
        apify_token = os.getenv("APIFY_TOKEN")
        if not apify_token:
            return {
                "error": "APIFY_TOKEN environment variable is not set"
            }
        
        conn = http.client.HTTPSConnection("api.apify.com")
        payload = json.dumps({
            "startUrls": [{"url": url}],
            "maxItems": max_rows,
            "proxyConfiguration": {
                "useApifyProxy": True
            }
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {apify_token}'
        }
        
        # Start the actor task
        conn.request("POST", f"/v2/actor-tasks/{ACTOR_TASK_ID}/runs", payload, headers)
        res = conn.getresponse()
        run_data = json.loads(res.read())
        
        if res.status != 201:  # Actor task creation should return 201
            return {
                "url": url,
                "error": f"Failed to start actor task. Status: {res.status}",
                "response": run_data
            }
            
        # Get the run ID from the response
        run_id = run_data.get('data', {}).get('id')  # Note: Changed to get id from data object
        if not run_id:
            return {
                "url": url,
                "error": "No run ID received from Apify",
                "response": run_data
            }
            
        print(f"Started actor task run: {run_id}")
        
        # Poll the run status until it's completed
        while True:
            conn.request("GET", f"/v2/actor-runs/{run_id}", headers=headers)
            status_res = conn.getresponse()
            status_data = json.loads(status_res.read())
            
            status = status_data.get('data', {}).get('status')  # Note: Changed to get status from data object
            print(f"Current status: {status}")
            
            if status == 'SUCCEEDED':
                # Get the dataset ID from the run
                dataset_id = status_data.get('data', {}).get('defaultDatasetId')
                if not dataset_id:
                    return {
                        "url": url,
                        "error": "No dataset ID found in the run"
                    }
                
                # Get the dataset items
                dataset_url = f"/v2/datasets/{dataset_id}/items"
                conn.request("GET", dataset_url, headers=headers)
                data_res = conn.getresponse()
                results = json.loads(data_res.read())
                
                if isinstance(results, list) and len(results) > 0:
                    job_data = results[0]
                    
                    # Try to find the correct keys
                    title = (
                        job_data.get("title") or 
                        job_data.get("jobTitle") or 
                        job_data.get("position") or 
                        search_params.job_title
                    )
                    
                    description = (
                        job_data.get("description") or 
                        job_data.get("jobDescription") or 
                        job_data.get("fullDescription") or
                        f"Position for {search_params.job_title} in {search_params.location}"
                    )
                    
                    if title and description:
                        return ScrapedJobData(
                            job_title=title,
                            job_description=description
                        )
                    else:
                        return {
                            "error": "Could not find title or description in scraped data",
                            "available_data": job_data,
                            "search_params": search_params.model_dump()
                        }
                else:
                    return {
                        "error": "No results found",
                        "search_params": search_params.model_dump() if search_params else None
                    }
                    
            elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                return {
                    "url": url,
                    "error": f"Actor run failed with status: {status}",
                    "details": status_data.get('data', {}).get('meta', {}).get('error', {}).get('message')
                }
                
            import time
            time.sleep(5)  # Wait 5 seconds before checking again
            
    except Exception as e:
        print(f"Error in scrape_indeed_jobs: {str(e)}")
        print(f"Last known results: {results if 'results' in locals() else 'No results available'}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "search_params": search_params.model_dump() if search_params else None
        }
    finally:
        if 'conn' in locals():
            conn.close()

# Update example usage
if __name__ == "__main__":
  
    
    
    #async def test_scraper():
     # Test with URL
    #    url_params = JobSearchParams(
    #        url="https://ph.indeed.com/jobs?q=engineer&l=Makati"
    #    )
        
        # Test with job title and location
        #search_params = JobSearchParams(
            #job_title="Python Developer",
            #location="Manila"
        #)
        
    #    if not os.getenv("APIFY_TOKEN"):
    #        print("Please set your APIFY_TOKEN environment variable first!")
    #        return
            
    #    # Test URL-based search
    #    print(f"Starting scrape for URL: {url_params.url}")
    #    result1 = await scrape_indeed_jobs(search_params=url_params)
    #    print("URL-based Result:", 
    #          result1.dict() if isinstance(result1, ScrapedJobData) else result1)
        
        # Test parameter-based search
        #print(f"\nStarting scrape for Job: {search_params.job_title} in {search_params.location}")
        #result2 = await scrape_indeed_jobs(search_params=search_params)
        #print("Parameter-based Result:", 
        #      result2.dict() if isinstance(result2, ScrapedJobData) else result2)

    #asyncio.run(test_scraper())

    scrape_indeed_jobs(url="https://ph.indeed.com/jobs?q=engineer&l=Makati")