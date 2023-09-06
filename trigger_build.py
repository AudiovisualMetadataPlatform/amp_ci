#!/bin/env python3
import argparse
import requests
import datatypes
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Configuration file")
    parser.add_argument("repo", help="Repository to build")
    parser.add_argument("--ref", type=str, default="/refs/heads/main", help="Repo reference")
    args = parser.parse_args()

    with open(args.config) as f:
        config = datatypes.ConfigFile(**yaml.safe_load(f))

    payload = {
        'ref': args.ref,
        'repository': {
            'name': args.repo
        },
        'pusher': {
            'name': 'Manual Trigger',
            'email': 'amppd@iu.edu'
        }
    }

    host = "127.0.0.1" if config.host == "0.0.0.0" else config.host
    r = requests.post(f"http://{host}:{config.port}/webhook/", 
                      json=payload,
                      headers={'x-github-event': 'push'})
    if r.status_code != 200:
        print(f"Push failed: ({r.status_code}) {r.content}")
    else:
        print(f"Push successful")

if __name__ == "__main__":
    main()