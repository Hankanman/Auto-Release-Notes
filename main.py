""" Main script to write release notes based on Azure DevOps work items. """

import base64
import sys
import logging as log
from pathlib import Path
from urllib.parse import quote
from collections import defaultdict
import asyncio
import aiohttp
from modules.config import (
    ORG_NAME,
    PROJECT_NAME,
    SOLUTION_NAME,
    RELEASE_VERSION,
    RELEASE_QUERY,
    PAT,
    GPT_API_KEY,
    MODEL,
    MODEL_BASE_URL,
    DEVOPS_BASE_URL,
    DESIRED_WORK_ITEM_TYPES,
    OUTPUT_FOLDER,
    SOFTWARE_SUMMARY,
    DEVOPS_API_VERSION,
)
from modules.enums import WorkItemField, APIEndpoint
from modules.utils import (
    setupLogs,
    cleanString,
    getWorkItemIcons,
    getWorkItems,
    updateItemGroup,
    finaliseNotes,
)


class ProcessConfig:
    """
    Represents a configuration for processing data.

    Args:
        session (str): The session information.
        file_md (str): The file metadata.
        summarize_items (bool): Flag indicating whether to summarize items.
        work_item_type_to_icon (dict): A dictionary mapping work item types to icons.
    """

    def __init__(self, session, file_md, summarize_items, work_item_type_to_icon):
        self.session = session
        self.file_md = file_md
        self.summarize_items = summarize_items
        self.work_item_type_to_icon = work_item_type_to_icon


def setupFiles():
    """Sets up the necessary file paths and initial markdown content."""
    folder_path = Path(".") / OUTPUT_FOLDER
    file_md = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.md").resolve()
    file_html = (folder_path / f"{SOLUTION_NAME}-v{RELEASE_VERSION}.html").resolve()
    folder_path.mkdir(parents=True, exist_ok=True)

    with open(file_md, "w", encoding="utf-8") as md_file:
        md_file.write(
            f"# Release Notes for {SOLUTION_NAME} version v{RELEASE_VERSION}\n\n"
            f"## Summary\n\n"
            f"<NOTESSUMMARY>\n\n"
            f"## Quick Links\n\n"
            f"<TABLEOFCONTENTS>\n"
        )

    return file_md, file_html


def encodePat():
    """Encodes the PAT for authorization."""
    return base64.b64encode(f":{PAT}".encode()).decode()


async def fetchParentItems(session, org_name_escaped, project_name_escaped, parent_ids):
    """Fetches parent work items from Azure DevOps."""
    parent_work_items = {}
    for parent_id in parent_ids:
        parent_uri = DEVOPS_BASE_URL + APIEndpoint.WORK_ITEM.value.format(
            org_name=org_name_escaped,
            project_name=project_name_escaped,
            parent_id=parent_id,
        )
        if parent_id != "0":
            async with session.get(parent_uri) as parent_response:
                parent_work_items[parent_id] = await parent_response.json()
    return parent_work_items


def groupItems(work_items):
    """Groups work items by their parent."""
    parent_child_groups = defaultdict(list)
    for item in work_items:
        parent_link = next(
            (
                rel
                for rel in item.get("relations", [])
                if rel["rel"] == "System.LinkTypes.Hierarchy-Reverse"
            ),
            None,
        )
        if parent_link:
            parent_id = parent_link["url"].split("/")[-1]
            parent_child_groups[parent_id].append(item)
        else:
            log.info("Work item %s has no parent", item["id"])
            item["fields"][WorkItemField.PARENT.value] = 0
            parent_child_groups["0"].append(item)
    return parent_child_groups


def addOtherParent(parent_work_items):
    """Adds a placeholder for items with no parent."""
    parent_work_items["0"] = {
        "id": 0,
        "fields": {
            WorkItemField.TITLE.value: "Other",
            WorkItemField.WORK_ITEM_TYPE.value: "Other",
            WorkItemField.PARENT.value: 0,
        },
        "_links": {
            "html": {"href": "#"},
            "workItemIcon": {
                "url": "https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_clipboard_issue?color=577275&v=2"
            },
        },
        "url": "#",
    }


async def processItems(config, work_items, parent_work_items):
    """Processes work items and writes them to the markdown file."""
    summary_notes = ""
    for work_item_type in DESIRED_WORK_ITEM_TYPES:
        log.info("Processing %ss", work_item_type)
        parent_ids_of_type = getParentIdsByType(parent_work_items, work_item_type)

        for parent_id in parent_ids_of_type:
            parent_work_item = parent_work_items[parent_id]
            parent_title = cleanString(
                parent_work_item["fields"][WorkItemField.TITLE.value]
            )
            log.info("%s | %s | %s", work_item_type, parent_id, parent_title)

            parent_link, parent_icon_url = getParentLinkAndIcon(
                parent_work_item, config.work_item_type_to_icon, work_item_type
            )
            child_items = getChildItems(work_items, parent_id)

            if not child_items:
                log.info("No child items found for parent %s", parent_id)

            summary_notes += f"- {parent_title}\n"
            parent_header = generateParentHeader(
                parent_id, parent_link, parent_icon_url, parent_title
            )

            grouped_child_items = groupChildItemsByType(child_items)
            if grouped_child_items:
                writeParentHeaderToFile(config.file_md, parent_header)
                await updateItemGroup(
                    summary_notes,
                    grouped_child_items,
                    config.work_item_type_to_icon,
                    config.file_md,
                    config.session,
                    config.summarize_items,
                )

    return summary_notes


def getParentIdsByType(parent_work_items, work_item_type):
    """
    Returns a list of parent work item IDs that match the specified work item type.

    Args:
        parent_work_items (dict): A dictionary containing parent work items, where the keys are the work item IDs and the values are the work item details.
        work_item_type (str): The work item type to filter by.

    Returns:
        list: A list of parent work item IDs that match the specified work item type.
    """
    return [
        pid
        for pid, item in parent_work_items.items()
        if item["fields"]["System.WorkItemType"] == work_item_type
    ]


def getParentLinkAndIcon(parent_work_item, work_item_type_to_icon, work_item_type):
    """
    Get the parent link and icon URL for a given work item.

    Args:
        parent_work_item (dict): The parent work item.
        work_item_type_to_icon (dict): A dictionary mapping work item types to their corresponding icon URLs.
        work_item_type (str): The type of the work item.

    Returns:
        tuple: A tuple containing the parent link and icon URL.
    """
    parent_link = parent_work_item["_links"]["html"]["href"]
    parent_icon_url = work_item_type_to_icon.get(work_item_type)["iconUrl"]
    return parent_link, parent_icon_url


def getChildItems(work_items, parent_id):
    """
    Returns a list of child work items based on the given parent ID.

    Parameters:
    work_items (list): A list of work items.
    parent_id (int): The ID of the parent work item.

    Returns:
    list: A list of child work items.
    """
    return [
        wi
        for wi in work_items
        if wi["fields"].get(WorkItemField.PARENT.value) == int(parent_id)
    ]


def generateParentHeader(parent_id, parent_link, parent_icon_url, parent_title):
    """
    Generate a parent header for a given parent ID, link, icon URL, and title.

    Args:
        parent_id (str): The ID of the parent.
        parent_link (str): The link associated with the parent.
        parent_icon_url (str): The URL of the icon for the parent.
        parent_title (str): The title of the parent.

    Returns:
        str: The generated parent header.

    """
    parent_head_link = f"[#{parent_id}]({parent_link}) " if parent_id != "0" else ""
    return (
        f"\n### <img src='{parent_icon_url}' alt='icon' width='20' height='20'> "
        f"{parent_head_link}{parent_title}\n"
    )


def groupChildItemsByType(child_items):
    """
    Groups child items by their work item type.

    Parameters:
    - child_items (list): A list of child items.

    Returns:
    - grouped_child_items (defaultdict): A defaultdict containing the child items grouped by their work item type.
    """
    grouped_child_items = defaultdict(list)
    for item in child_items:
        grouped_child_items[item["fields"][WorkItemField.WORK_ITEM_TYPE.value]].append(
            item
        )
    return grouped_child_items


def writeParentHeaderToFile(file_md, parent_header):
    """
    Appends the parent header to the specified Markdown file.

    Args:
        file_md (str): The path to the Markdown file.
        parent_header (str): The parent header to be written.

    Returns:
        None
    """
    with open(file_md, "a", encoding="utf-8") as file_output:
        file_output.write(parent_header)


async def writeReleaseNotes(
    query_id: str, section_header: str, summarize_items: bool, output_html: bool
):
    """
    Writes release notes based on the provided parameters.

    Args:
        query_id (str): The ID of the query to fetch work items from.
        section_header (str): The header for the release notes section.
        summarize_items (bool): Flag indicating whether to summarize the work items.
        output_html (bool): Flag indicating whether to output the release notes in HTML format.
    """
    org_name_escaped = quote(ORG_NAME)
    project_name_escaped = quote(PROJECT_NAME)
    devops_headers = {"Authorization": f"Basic {encodePat()}"}

    file_md, file_html = setupFiles()

    async with aiohttp.ClientSession(headers=devops_headers) as session:
        work_item_type_to_icon = await getWorkItemIcons(session, ORG_NAME, PROJECT_NAME)
        work_items = await getWorkItems(session, ORG_NAME, PROJECT_NAME, query_id)

        parent_child_groups = groupItems(work_items)
        parent_work_items = await fetchParentItems(
            session, org_name_escaped, project_name_escaped, parent_child_groups.keys()
        )
        addOtherParent(parent_work_items)

        config = ProcessConfig(
            session, file_md, summarize_items, work_item_type_to_icon
        )
        summary_notes = await processItems(config, work_items, parent_work_items)

        await finaliseNotes(
            output_html, summary_notes, file_md, file_html, [section_header]
        )


if __name__ == "__main__":
    setupLogs()
    required_env_vars = [
        ORG_NAME,
        PROJECT_NAME,
        SOLUTION_NAME,
        RELEASE_VERSION,
        RELEASE_QUERY,
        GPT_API_KEY,
        PAT,
        MODEL,
        MODEL_BASE_URL,
        DEVOPS_BASE_URL,
        SOFTWARE_SUMMARY,
        DESIRED_WORK_ITEM_TYPES,
        OUTPUT_FOLDER,
        DEVOPS_API_VERSION,
    ]
    if any(not var for var in required_env_vars):
        log.error(
            "Please set the environment variables in the .env file before running the script."
        )
        sys.exit(1)
    else:
        with open(".env", "r", encoding="utf-8") as file:
            # Read the content of the file
            file_content = file.read()
            # Print the content
            print(file_content)
        asyncio.run(writeReleaseNotes(RELEASE_QUERY, "Resolved Issues", True, True))
