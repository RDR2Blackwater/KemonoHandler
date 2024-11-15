import requests
from pathlib import Path
from datetime import datetime

# Invalid pattern list
invalid_pattern = {'\\', '/', ':', '*', '?', '"', '<', '>', '|'}


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
    - publish_date: str, publish date of the post
    """
    # Index counter, record the index of the files in attachments
    file_counter = 0

    for attachment in attachments:
        file_prefix = attachment["name"].split(".")[-1]
        # Rename the raw file name to make the files sorted easier for system
        title = ''.join([char for char in title if char not in invalid_pattern])
        attachment["name"] = publish_date.split("T")[0] + "_" + title + "_" + str(file_counter) + "." + file_prefix
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
