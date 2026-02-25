
#read data from profile file

import threading
import queue
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# queue to hold the two scripts that need to run, in order
job_queue = queue.Queue()

# lock so only one script writes to the data folder at a time
# (avoids race conditions on linkedin_jobs.json)
file_lock = threading.Lock()

def run_script(path):
    print(f"[{threading.current_thread().name}] Starting: {os.path.basename(path)}")
    result = subprocess.run([sys.executable, path])
    if result.returncode != 0:
        print(f"[{threading.current_thread().name}] ERROR: {os.path.basename(path)} exited with code {result.returncode}")
        return False
    print(f"[{threading.current_thread().name}] Done: {os.path.basename(path)}")
    return True

def worker():
    while True:
        try:
            script_path = job_queue.get(block=False)
        except queue.Empty:
            break

        with file_lock:
            success = run_script(script_path)

        job_queue.task_done()

        if not success:
            # clear the remaining jobs if something failed
            while not job_queue.empty():
                try:
                    job_queue.get_nowait()
                    job_queue.task_done()
                except queue.Empty:
                    break
            break


if __name__ == "__main__":
    # add jobs to the queue in the order they should run
    job_queue.put(os.path.join(BASE_DIR, "scrapers/linkedin_scraper.py"))
    job_queue.put(os.path.join(BASE_DIR, "processors/ai_processor.py"))

    # single worker thread processes the queue sequentially
    # (scraper must finish before processor reads its output)
    t = threading.Thread(target=worker, name="JobRunner")
    t.start()
    t.join()

    print("\nAll jobs finished. Check outputs/job_leads.md for results.")

