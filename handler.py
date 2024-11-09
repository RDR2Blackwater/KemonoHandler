import argparse
import asyncio

import utils


def post_main_handler(args: argparse.Namespace) -> None:
    """ Handler of the main loop of the application """
    # Initialize download folder and the first fifty (or less) posts response
    res = utils.post_getter(args.service, args.creator_id, args.api_server, 0)
    offset_counter = 0
    folder = utils.creator_mkdir(args.service, args.creator_id, args.api_server)
    print("Destination download folder: " + folder)

    # Construct the date from args.publish_date_before and args.publish_date_after
    publish_date_before = utils.date_handler(args.publish_date_before, "%Y-%m-%d")
    publish_date_after = utils.date_handler(args.publish_date_after, "%Y-%m-%d")

    # Loop the download process until the response is None
    while res is not None:
        print("Detected posts: " + str(len(res)))
        for posts in res:
            # Check the published date of the post
            publish_date = utils.date_handler(posts["published"], "%Y-%m-%dT%H:%M:%S")
            if publish_date_before and publish_date_before < publish_date:
                print("The published date of " + posts["title"] + f" is later than {publish_date_before}, skipping post...")
                continue
            if publish_date_after and publish_date_after > publish_date:
                print(f"All posts after {publish_date} have been downloaded")
                break

            # Check if the title contains excluded words
            if args.exclude_words is not None and not utils.title_checker(posts["title"], args.exclude_words):
                print(posts["title"] + "Contains excluded words, skipping post...")
                continue

            # Pre-process the names in attachments
            posts_link = posts["attachments"]
            print(posts["title"] + " has " + str(len(posts_link)) + " attachments")
            posts_link = utils.attachments_handler(posts_link, posts["title"])

            # Run the asynchronous download function
            asyncio.run(utils.download_resources(args.max_async_download, posts_link, folder, args.cookies))

        # Get the next 50 posts, if available
        offset_counter += 1
        res = utils.post_getter(args.service, args.creator_id, args.api_server, offset_counter * 50)

    # Exit the script
    print("None of posts detected, exiting...")
    exit(0)
