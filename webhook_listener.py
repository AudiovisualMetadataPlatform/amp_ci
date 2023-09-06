#!/bin/env python3.9
# Shamelessly stolen from https://majornetwork.net/2020/10/webhook-listener-with-fastapi/

import logging
import logging.config
from fastapi import FastAPI
import argparse
import sys
import uvicorn
from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor
from datatypes import WebhookPush, ConfigFile
from web_handler import router as hook_router
import yaml
import tempfile
import os
import subprocess
from pathlib import Path
import setproctitle
import time

APP_NAME = "webhook_listener"
WEBHOOK_SECRET = "My precious"

event_queue = Queue()
logger = logging.getLogger()
config: ConfigFile = None

def main():
    global logger, config
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true", help="Turn on debugging")
    parser.add_argument("config", help="Configuration file")
    args = parser.parse_args()

    # Configure the logger
    log_handlers = ['console', 'default'] if sys.stderr.isatty() else ['default']
    log_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {'standard': {'format': "%(asctime)s [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s"}},
        'handlers': {
            'console': {'class': 'logging.StreamHandler',
                        'formatter': 'standard',
                        'stream': 'ext://sys.stderr',
                        'level': 'DEBUG'},
            'default': {'class': 'logging.FileHandler',
                        'formatter': 'standard',
                        'filename': f"{sys.path[0]}/logs/{APP_NAME}.log",
                        'level': 'DEBUG'}},
        'loggers': {
            'uvicorn': {'propagate': False, 'level': 'DEBUG', 'handlers': log_handlers},
            'watchfiles': {'propagate': False, 'level': 'DEBUG', 'handlers': log_handlers},
        },
        'root': {'level': 'DEBUG', 'handlers': log_handlers}
    }
    logging.config.dictConfig(log_config)
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    with open(args.config) as f:
        config = ConfigFile(**yaml.safe_load(f))

    # Set up the web application
    app = FastAPI(
        title="AMP Webhook Listener",
        description="Nothing to see here",
        version="1.0",
    )
    app.state.queue = event_queue
    app.state.secret = WEBHOOK_SECRET
    app.state.app_name = APP_NAME
    app.include_router(hook_router)

    # Start the uvicorn daemon    
    logger.info("Starting uvicorn daemon")
    def uvicorn_wrapper(**kwargs):
        setproctitle.setproctitle("AMP Webhooks Webserver")
        uvicorn.run(**kwargs)

    uvicorn_daemon = Process(target=uvicorn_wrapper, #uvicorn.run,
                             name="Webhook Uvicorn",
                             args=[], 
                             kwargs={'app': app,                                     
                                     'host': config.host,
                                     'port': config.port,
                                     'log_config': log_config},
                             daemon=True)
    uvicorn_daemon.start()

    logger.info("Watching the queue for events...")
    setproctitle.setproctitle("AMP Webhooks Queue Handler")
    ppe = ProcessPoolExecutor(config.workers,
                              initializer=lambda: setproctitle.setproctitle("AMP Webhooks build idle"))
    while True:
        try:            
            event: WebhookPush = event_queue.get(True)            
            logger.debug(f"Got event: {event!s}")
            this_repo = event.repository.name            
            if this_repo == "amp_bootstrap":
                to_build = config.repos
            else:
                if this_repo not in config.repos:
                    continue
                to_build = [this_repo]
            for repo in to_build:
                logger.info(f"Queuing build for {repo} since {event.pusher.name} pushed some code to {event.repository.name}")
                ppe.submit(push_handler, repo, event, logging.DEBUG if args.debug else logging.INFO)
        except Exception as e:
            logger.exception(e)


def push_handler(reponame, event: WebhookPush, level):
    # Set up a separate logger for this reponame
    repohandler = logging.FileHandler(sys.path[0] + "/logs/" + reponame + ".log")
    repohandler.setLevel(level)
    repohandler.setFormatter(logging.Formatter("%(asctime)s [%(name)s:%(filename)s:%(lineno)d] [%(levelname)s] %(message)s"))
    logger.addHandler(repohandler)

    # do the build
    start = time.time()
    try:
        pid = os.getpid()
        logger.info(f"[{pid}] Building {reponame}, {event.ref}")
        setproctitle.setproctitle(f"AMP Webhooks building {reponame}, {event.ref}")
        # find the build scripts:
        scripts = [f"{sys.path[0]}/{x}" for x in config.scripts.get(reponame, config.scripts.get('*'))]
        
        # make sure our temporary directory is correct
        for n in ('TMP', 'TMPDIR', 'TEMP'):
            os.environ[n] = config.temproot

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # check out the bootstrap and the repo in question...
            subprocess.run(["git", "clone", config.baseurl + f"/amp_bootstrap"], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            os.mkdir("src_repos")
            os.chdir("src_repos")
            subprocess.run(["git", "clone", config.baseurl + f"/{reponame}", "--recurse-submodules"], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)            
            os.chdir(tmpdir)

            # Start the build process.
            for script in scripts:
                p = subprocess.run([script], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, encoding="utf-8")
                if p.returncode != 0:
                    logger.error(f"[{pid}] {reponame} Build script {script} failed with rc {p.returncode}")
                    logger.error(f"[{pid}] Script output:\n{p.stdout}")
                    break
                else:
                    logger.debug(f"[{pid}] {reponame} Build script {script} output:\n{p.stdout}")
            else:
                logger.info(f"[{pid}] Done building {reponame}, {event.ref} in {time.time() - start} seconds")
    except Exception as e:
        logger.exception(f"[{pid}] Building {reponame}, {event.ref}: {e}")
    setproctitle.setproctitle("AMP Webhooks build idle")
    logger.removeHandler(repohandler)

if __name__ == "__main__":
    main()
