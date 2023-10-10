#!/srv/shared/bin/python3.9

import argparse
import logging
import os
from pathlib import Path
import sys
import atexit
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, Future
import tempfile
import smtplib
from email.message import EmailMessage
import time

QUEUE_DIR = Path(sys.path[0], "queue")
LOCKFILE = QUEUE_DIR / "lock"
GITURL = "https://github.com/AudiovisualMetadataPlatform/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true", help="Turn on debugging")
    parser.add_argument("--threads", type=int, default=1, help="Number of Threads for building")
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s [%(levelname)-8s] (%(filename)s:%(lineno)d:%(process)d)  %(message)s",
                        filename=f"{sys.path[0]}/build.log", 
                        level=logging.DEBUG if args.debug else logging.INFO)
    
    # make sure we're the only one running
    if not get_queue_lock():
        logging.debug("Lockfile exists.  Exiting")
        exit(0)

    # make sure we've got a clean queue to work with
    reset_queue()

    # create a process pool 
    ppe = ProcessPoolExecutor(max_workers=args.threads)
    futures: dict[str, Future] = {}
    while True:
        # check any pending future results
        for i in list(futures.keys()):
            f = futures[i]
            if f.done():
                try:
                    r = f.result()
                    logging.info(f"Queue id {i} finished ({r})")
                except Exception as e:
                    logging.exception(f"Queue id {i} failed with an exception: {e}")
                # clear out this future.
                futures.pop(i, None)
                (QUEUE_DIR / i).unlink(missing_ok=True)

        for q in sorted(QUEUE_DIR.iterdir()):
            if q.name.startswith("build-") and not q.name.endswith(".lock"):
                # this queue file is one we want to process.
                locked = lock_entry(q)
                try:
                    with open(locked) as f:
                        data = json.load(f)
                    # now that I have the data, let's start a background job.
                    logging.info(f"Submitting {locked!s} for {data}")
                    futures[locked.name] = ppe.submit(build, data)
                except Exception as e:
                    logging.exception(f"Cannot read {locked!s} or start the job.  Will remove it: {e}")
                    locked.unlink()
                    
        # if there are no futures in flight, we can exit.
        if not futures:
            break
        time.sleep(10)

def lock_entry(filename: Path) -> Path:
    "Lock a queue file by renaming it to *.lock"
    dest = filename.with_name(filename.name + ".lock")
    filename.rename(dest)
    return dest


def reset_queue():
    """Reset any in-flight build jobs because they're stale"""
    for entry in QUEUE_DIR.iterdir():
        if entry.name.endswith(".lock"):
            # this one was in-flight, rename it.
            logging.debug(f"Clearing lock on {entry.name}")
            entry.rename(entry.with_name(entry.name.replace('.lock', '')))


def get_queue_lock() -> bool:
    """Return true if we acquired the queue lock, false otherwise"""
    try: 
        fd = os.open(LOCKFILE, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o664)
        os.write(fd, f"{os.getpid()}\n".encode())
        os.close(fd)
        # make sure we remove the lockfile when we're done.
        atexit.register(lambda: LOCKFILE.unlink())
        return True
    except:
        # check if we have a stale lock.  This is a simple check -- I'm only
        # checking for the pid...not that the pid is actually one of us.
        with open(LOCKFILE) as f:
            pid = int(f.readline().strip())
            if Path(f"/proc/{pid}").exists():
                return False
            else:
                LOCKFILE.unlink()
                return get_queue_lock()
            

def build(data: dict):
    """Do an AMP build based on the parameters in data"""
    # Create the tempdir and move there.
    if Path("/srv/scratch").exists():
        tmpdir = "/srv/scratch"
    else:
        tmpdir = "/tmp"
    with tempfile.TemporaryDirectory(prefix="amp_ci-", dir=tmpdir) as tmpdir:
        os.chdir(tmpdir)

        # create the build script.  It consists of:
        # * checkout_repos
        # * build_packages
        # * distribute_{ref-name} (if it exists)
        # The ref name for master is converted to main.
        potential_chunks = ["checkout_repos", "build_packages", "distribute"]
        ref_name = data['ref'].split('/')[-1]
        if ref_name == 'master':
            ref_name = 'main'
        chunks = []
        for p in potential_chunks:
            d_script = f"{p}_{ref_name}"
            if Path(sys.path[0], "scripts", d_script).exists():
                chunks.append(d_script)

        if not chunks:
            # we found nothing, don't do anything
            return data
        
        # create the build script
        with open("build.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("set -ex\n")
            f.write("echo Starting at $(date)\n")
            for chunk in chunks:
                f.write(f"### Start of {chunk} ###\n")
                cdata = Path(sys.path[0], "scripts", chunk).read_text()
                f.write(str.format(cdata, **data))
                f.write(f"### End of {chunk} ###\n")
            f.write("echo Successful at $(date)\n")
        os.chmod("build.sh", 0o775)

        logging.debug(f"Build script for {data}:\n{Path('build.sh').read_text()}")

        logging.info(f"Starting build for {data}")
        p = subprocess.run(['./build.sh'],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8")
        logging.debug(f"Build rc {p.returncode}, output: {p.stdout}")
        if p.returncode != 0:
            logging.error(f"Build failed for {data}")
            logging.error(f"Build output:\n{p.stdout}")
            # send an email to the person who committed this.
            msg = EmailMessage()
            msg['Subject'] = f"AMP build failed for {data['repository']}/{data['commit_id']}"
            msg['From'] = 'amppd@iu.edu'
            msg['To'] = data['committer_email']
            message = f"""Greetings and salutations {data['committer_name']}!

Hopefully this email finds you well.

The build for {data['repository']} commit {data['commit_id']} in the branch {data['ref']} has failed.

The script returned an rc of {p.returncode} and produced the following output:
----------------------------------
{p.stdout}
----------------------------------

Sorry about that.

With warmest regards,
AMP CI
"""
            msg.set_content(message)

            # and send it.
            s = smtplib.SMTP("localhost")
            s.send_message(msg)
            s.quit()

        # we'll send back our calling data to build a friendly log message.
        return data



if __name__ == "__main__":
    main()