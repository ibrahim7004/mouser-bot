import threading
import os
import sys
from MouserBot import MouserBot
from files import tsv_files_dir, threads


def process_file(file_path):
    with open(file_path, 'r') as file:
        MouserBot(file)


tsv_files = [os.path.join(tsv_files_dir, o)
             for o in os.listdir(tsv_files_dir) if o.endswith('.tsv')]

num_threads = min(threads, len(tsv_files))

threads = []

for i in range(num_threads):
    thread = threading.Thread(target=process_file, args=(tsv_files[i],))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

sys.exit()
