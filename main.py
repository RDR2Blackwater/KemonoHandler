import argparse
import handler

parser = argparse.ArgumentParser(description="Kemono download configurations")
parser.add_argument("--cookies", type=str, default=None,
                    help="Cookie value recorded in \"session\", download might be blocked by DDoS defender without cookies")
parser.add_argument("--service", type=str, default=None,
                    help="Target service name")
parser.add_argument("--creator-id", type=str, default=None,
                    help="Target creator id")
parser.add_argument("--max-async-download", type=int, default=3,
                    help="Max allowed asynchronous download threads (default: 3)")
parser.add_argument("--api-server", type=str, default="kemono",
                    choices=["kemono", "coomer"], help="Target api server to request (default: kemono)")
parser.add_argument("--publish-date-before", type=str, default=None,
                    help="(Optional) Filter the posts before the specified date, format of the date should be YYYY-MM-DD")
parser.add_argument("--publish-date-after", type=str, default=None,
                    help="(Optional) Filter the posts after the specified date, format of the date should be YYYY-MM-DD")
parser.add_argument("--exclude-words", type=str, default=None,
                    help="(Optional) Exclude posts that contains given words in title, split words by \",\"")

if __name__ == '__main__':
    args = parser.parse_known_args()[0]
    args.api_server = f"https://{args.api_server}.su/api/v1/"
    print("Kemono handler arguments: " + str(args))

    handler.post_main_handler(args)
