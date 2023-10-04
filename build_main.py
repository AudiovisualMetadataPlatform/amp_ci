#!/bin/env python3

import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="Repository Name")
    parser.add_argument("commit_id", help="Commit ID")
    parser.add_argument("committer_name", help="Committer Name")
    parser.add_argument("committer_email", help="Committer Email")
    args = parser.parse_args()
    print(args)
    print(os.environ)

if __name__ == "__main__":
    main()