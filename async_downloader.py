import aiohttp
import asyncio
import os

from tqdm.asyncio import tqdm
from pathlib import Path


class async_downloader:
    __slots__ = 'semaphore', 'client_timeout', 'cookies'

    def __init__(self,
                 max_async_download: int,
                 timeout: int,
                 cookies: str):
        """
        Initialize the async_downloader class.

        - max_async_download: int, max allowed asynchronous download threads at a time.
        - timeout: int, download will throw an asyncio.exceptions.TimeoutError after given timeout limit.
        - cookies: str, cookie to be sent in the request.
        """
        # Create a semaphore to limit concurrent downloads
        self.semaphore = asyncio.Semaphore(max_async_download)
        # Define timeout settings for aiohttp requests
        self.client_timeout = aiohttp.ClientTimeout(total=timeout)
        # Cookie used in download
        self.cookies = cookies

    # Asynchronous downloader
    async def __download_file(self,
                              session: aiohttp.ClientSession,
                              url: str,
                              file_path: str) -> None:
        """
        Helper function to download a single file asynchronously.
        """
        try:
            async with session.get(url, cookies={"session": self.cookies}, timeout=self.client_timeout) as response:
                response.raise_for_status()  # Raise an error for bad responses
                with open(file_path, "wb") as f:
                    f.write(await response.read())
        except (asyncio.TimeoutError, asyncio.exceptions.TimeoutError):
            print("Downloading file took too long, exiting...")
            exit(1)

    async def download_resources(self,
                                 posts_link: list[dict[str, str]],
                                 download_folder: str) -> None:
        """
        Asynchronously download resources from a given API server with a maximum concurrency limit.

        Parameters:
        - posts_link: list[dict], list of dictionaries containing 'name' and 'path' for each file.
        - download_folder: str, the local folder path to save downloaded files.
        """

        # Define a task to download a single file, respecting the semaphore limit
        async def download_task(tmp_session, file_info):
            file_path = Path(download_folder) / file_info["name"]
            # Check if file already exists
            if file_path.exists() and os.path.getsize(file_path) != 0:
                print(f"File '{file_info['name']}' already exists. Skipping download.")
                return

            async with self.semaphore:
                url = f"https://kemono.su/{file_info['path'].lstrip('/')}"  # Ensure relative paths are correctly joined
                await self.__download_file(tmp_session, url, file_path)

        # Create an aiohttp session and download all files
        async with aiohttp.ClientSession(timeout=self.client_timeout) as session:
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
