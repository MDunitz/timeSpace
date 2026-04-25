import logging
import re
import time
from urllib.error import URLError

import pandas as pd
from timeSpace import PROJECT_ROOT

logger = logging.getLogger(__name__)


def get_latest_filename(sheet_id, data_name):
    """Find the most recent cached CSV for a given Google Sheet.

    Cache files are named: ``{data_name}___{unix_timestamp}___{sheet_id}.csv``

    Parameters
    ----------
    sheet_id : str
        Google Sheets spreadsheet ID.
    data_name : str
        Human-readable dataset name (e.g. "processes").

    Returns
    -------
    str
        Filename of the most recent cache file.
    """
    data_dir = PROJECT_ROOT / "data" / "datasets"
    files = list(data_dir.glob("*.csv"))
    all_filenames = [f.stem for f in files]
    data_files = [x.split("___") for x in all_filenames if len(x.split("___")) > 2]
    times = [x[1] for x in data_files if x[2] == sheet_id]
    max_time = max(times, key=int)
    return f"{data_name}___{max_time}___{sheet_id}.csv"


def extract_google_sheet(spreadsheet_id, data_name, from_cache=True, cache=False, sheet_id=0, **kwargs):
    """Fetch a Google Sheets spreadsheet as a pandas DataFrame.

    Tries the local CSV cache first (``data/datasets/``). Falls back to
    downloading from Google Sheets export URL. Optionally caches the
    downloaded data for future use.

    Parameters
    ----------
    spreadsheet_id : str
        Google Sheets spreadsheet ID (the part between /d/ and /edit in the URL).
    data_name : str
        Human-readable name for the dataset (used in cache filenames).
    from_cache : bool
        If True (default), try to load from local cache before downloading.
    cache : bool
        If True, save downloaded data to the cache directory.
    sheet_id : int
        Sheet GID for multi-sheet workbooks. Default 0 (first sheet).
    **kwargs
        Passed to ``pd.read_csv()``.

    Returns
    -------
    DataFrame
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", str(spreadsheet_id)):
        raise ValueError(f"Invalid spreadsheet_id: {spreadsheet_id!r}")
    data_dir = PROJECT_ROOT / "data" / "datasets"
    if from_cache:
        try:
            filename = get_latest_filename(spreadsheet_id, data_name)
            file_path = data_dir / filename
            df = pd.read_csv(file_path, **kwargs)
            logger.info("Pulling data from cache: %s", file_path)
        except (FileNotFoundError, ValueError, KeyError) as e:
            logger.info("%s\nNo cache available for: %s\n%s, trying to pull from source", e, data_name, spreadsheet_id)
            df = extract_google_sheet(
                spreadsheet_id, data_name, from_cache=False, sheet_id=sheet_id, cache=cache, **kwargs
            )
    else:
        try:
            if sheet_id == 0:
                url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
            else:
                url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?gid={sheet_id}&format=csv"
            df = pd.read_csv(url, **kwargs)
        except URLError:
            import certifi
            import ssl

            ctx = ssl.create_default_context(cafile=certifi.where())
            import urllib.request as _urlreq

            with _urlreq.urlopen(url, context=ctx) as response:
                import io

                df = pd.read_csv(io.BytesIO(response.read()), **kwargs)
        logger.info("Data for %s pulled from: %s", data_name, url)
        if cache:
            filename = f"{data_name}___{int(time.time())}___{spreadsheet_id}.csv"
            file_path = data_dir / filename
            logger.info("Caching raw data to: %s", file_path)
            df.to_csv(file_path)
    return df
