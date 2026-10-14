"""Print every link the explorer shows for the reference objects, one per line.

Input for the source-link checker (.github/workflows/links.yml):

    python docs/list_source_urls.py [csv_path] > source_urls.txt
"""

import sys

from timeSpace.explorer.links import source_urls

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/datasets/time_space_reference_objects.csv"
    print("\n".join(source_urls(csv_path)))
