import requests
import aiohttp
import asyncio
from tqdm.asyncio import tqdm
from pathlib import Path
from datetime import datetime


def post_getter(service: str, creator_id: str, api_server: str, offset: int) -> dict:
    """
    Get the list of posts from a specified user

    Parameters:
    - service: str, the service type to be requested
    - creator_id: str, creator's id
    - api_server: str, the base URL of the API server.
    - offset: int, the offset of the post to be requested
    """
    response = requests.get(url=f"{api_server}/{service}/user/{creator_id}",
                            params={"o": offset},
                            headers={"accept": "application/json"})

    # user API would not return 4xx even if the search result is null, return a None explicitly if no data in response
    return response.json() if len(response.json()) != 0 else None


def attachments_handler(attachments: list[dict], title: str, publish_date: str) -> list[dict]:
    """
    Rename files and return the list with ordered file name

    Parameters:
    - attachments: list[dict], list of attachments names and relative paths
    - title: str, title of the post
    """
    # Index counter, record the index of the files in attachments
    file_counter = 0

    for attachment in attachments:
        file_prefix = attachment["name"].split(".")[-1]
        # Rename the raw file name to make the files sorted easier for system
        attachment["name"] = publish_date + "_" + title.replace('\\', '').replace('/', '') + "_" + str(file_counter) + "." + file_prefix
        file_counter += 1

    return attachments


def creator_mkdir(service: str, creator_id: str, api_server: str) -> str:
    """
    Create folder with the name of creator

    Parameters:
    - service: str, the service type to be requested
    - creator_id: str, creator's id
    - api_server: str, the base URL of the API server.
    """
    query_creator = requests.get(url=f"{api_server}/{service}/user/{creator_id}/profile",
                                 headers={"accept": "application/json"})

    # Check if creator exists
    if query_creator.status_code == 404:
        print("Creator not found, exiting...")
        exit(1)

    creator_folder = query_creator.json()["name"]
    # Create the download folder with the name of the creator
    if not Path(creator_folder).exists():
        Path(creator_folder).mkdir(parents=True)
    # Return folder path
    return creator_folder


def date_handler(date: str, date_formatter: str) -> datetime.date:
    """
    Convert a date string into a datetime object in a safe way

    Parameters:
    - date: str, the input date string
    - date_formatter: str, target format of the date, following ISO 8601
    """
    try:
        return datetime.strptime(date, date_formatter)
    except (TypeError, ValueError):
        print(f"Warning: invalid date format of {date}, will be ignored in the coming process")
        return None


def title_checker(title: str, exclude_words: str) -> bool:
    """
    Check if the title is valid
    - title: str, title of the post
    - exclude_words: str, contains a series of exclude words split by ","
    """
    for word in exclude_words.split(','):
        # Return False (invalid) if the banned word appears in the title
        if word in title:
            return False
    return True


# Asynchronous downloader
async def __download_file(session: aiohttp.ClientSession, url: str, file_path: str, cookies: str) -> None:
    """
    Helper function to download a single file asynchronously.
    """
    async with session.get(url, cookies={"session": cookies}) as response:
        response.raise_for_status()  # Raise an error for bad responses
        with open(file_path, "wb") as f:
            f.write(await response.read())


async def download_resources(max_async_download: int,
                             posts_link: list[dict[str, str]],
                             download_folder: str,
                             cookies: str) -> None:
    """
    Asynchronously download resources from a given API server with a maximum concurrency limit.

    Parameters:
    - max_async_download: int, max allowed asynchronous download threads at a time.
    - posts_link: list[dict], list of dictionaries containing 'name' and 'path' for each file.
    - download_folder: str, the local folder path to save downloaded files.
    """
    # Create a semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(max_async_download)

    # Define a task to download a single file, respecting the semaphore limit
    async def download_task(tmp_session, file_info):
        file_path = Path(download_folder) / file_info["name"]
        # Check if file already exists
        if file_path.exists():
            print(f"File '{file_info['name']}' already exists. Skipping download.")
            return

        async with semaphore:
            url = f"https://kemono.su/{file_info['path'].lstrip('/')}"  # Ensure relative paths are correctly joined
            await __download_file(tmp_session, url, file_path, cookies)

    # Create an aiohttp session and download all files
    async with aiohttp.ClientSession() as session:
        # Create an asynchronous tqdm progress bar
        with tqdm(total=len(posts_link), desc="Downloading Files", ncols=100, unit="file") as pbar:
            tasks = []

            # Create tasks for downloading each file and update progress bar
            for file_messages in posts_link:
                task = download_task(session, file_messages)
                # Wrap the download task to update the progress bar when completed
                tasks.append(task)

            # Wait for all download tasks to finish and update the progress bar
            for task in asyncio.as_completed(tasks):
                await task
                pbar.update(1)  # Update progress bar by 1 for each completed task

