""" This module contains utility functions for the script. """

import re
import datetime
import logging as log
import json
from typing import List
import aiohttp
from .enums import LogLevel
from .config import Config as c


def setup_logs(level: LogLevel = LogLevel.INFO):
    """
    Sets up logging configuration with the specified logging level.

    Parameters:
        level (LogLevel): The logging level to set. Defaults to LogLevel.INFO.

    Returns:
        None
    """
    log.basicConfig(
        level=level.value, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def create_contents(input_array: List[str]) -> str:
    """
    Converts a Array of section headers into a markdown table of contents.

    Args:
        input_array (Array[str]): The Array of section headers.

    Returns:
        str: The markdown table of contents.

    """
    markdown_links = []
    for item in input_array:
        anchor = re.sub(r"[^\w-]", "", item.replace(" ", "-")).lower()
        markdown_links.append(f"- [{item}](#{anchor})\n")
    return "".join(markdown_links)


def format_date(date_str: str) -> str:
    """Format the modified date string.

    Args:
        date_str (str): Input date string in the format "%Y-%m-%dT%H:%M:%S.%fZ"

    Returns:
        str: Human-readable date string in the format "%d-%m-%Y %H:%M"
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return date_obj.strftime("%d-%m-%Y %H:%M")
    except ValueError:
        log.warning("Invalid modified date format: %s", date_str)
        return date_str


def clean_string(string: str, min_length: int = 30) -> str:
    """Strip a string of HTML tags, URLs, JSON, and user references."""
    string = re.sub(r"<[^>]*?>", "", string)  # Remove HTML tags
    string = re.sub(r"http[s]?://\S+", "", string)  # Remove URLs
    string = re.sub(r"@\w+(\.\w+)?", "", string)  # Remove user references

    try:
        json.loads(string)
        string = ""
    except json.JSONDecodeError:
        pass

    string = string.strip()
    string = re.sub(r"&nbsp;", " ", string)
    string = re.sub(r"\s+", " ", string)
    return string if len(string) >= min_length else ""


async def finalise_notes(session: aiohttp.ClientSession) -> None:
    """
    Finalizes the release notes by adding the summary and table of contents.

    Args:
        html (bool): A boolean flag indicating whether to generate HTML output.
        summary_notes (str): The summary of the work items completed in this release.
        file_md (Path): The path to the output Markdown file.
        file_html (Path): The path to the output HTML file.
        section_headers (Array[str]): A Array of section headers for the table of contents.

    Returns:
        None
    """
    log.info("Writing final summary and table of contents...")
    final_summary = await c.model.summarise(
        f"{c.prompts.summary}{c.software.brief}\n"
        f"The following is a summary of the work items completed in this release:\n"
        f"{c.software.notes}\nYour response should be as concise as possible",
        session,
    )

    c.output.set_summary(final_summary)
    c.output.set_toc(create_contents(c.software.headers))
    await c.output.finalize(session)
