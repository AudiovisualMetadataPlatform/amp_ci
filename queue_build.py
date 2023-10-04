#!/bin/env python3
#
# queue a build
#
import argparse
import json
import time
import sys

def main():
    parser = argparse.ArgumentParser()    
    parser.add_argument("repository", help="Repository Name")
    parser.add_argument("ref", help="Commit ref")
    parser.add_argument("commit_id", help="Commit ID")
    parser.add_argument("committer_name", help="Committer Name")
    parser.add_argument("committer_email", help="Committer Email")
    args = vars(parser.parse_args())
 
    with open(f"{sys.path[0]}/queue/build-{time.time()}", "w") as f:
        json.dump(args, f)


if __name__ == "__main__":
    main()