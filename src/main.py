"""Iterate and Print Work Items by Type"""

from __future__ import annotations
import asyncio
import logging as log
from typing import List
import aiohttp
from src.config import Config
from src.work_items import WorkItems, WorkItemChildren, WorkItem


def iterate_and_print(
    items_by_type: List[WorkItemChildren],
    config: Config,
    session: aiohttp.ClientSession,
    level: int = 1,
    icon_size: int = 20,
):
    """Recursively iterate through work items by type and print each level."""
    indent = "#" * level
    icon_size = icon_size - level if len(indent) > 1 else icon_size
    for item_group in items_by_type:
        print(f"{indent} Type: {item_group.type}")
        write_type_header(item_group, config, level, icon_size)
        for item in item_group.items:
            print(f" - WorkItem ID: {item.id}, Title: {item.title}")
            if len(item.children) > 0:
                write_parent_header(item, config, level, icon_size)
            else:
                write_child_item(item, config)
            if item.children_by_type:
                iterate_and_print(item.children_by_type, config, session, level + 1)


def write_type_header(
    item: WorkItemChildren, config: Config, level: int, icon_size: int
):
    """Generate and write the header for the parent item."""
    indent = "#" * level
    header = f"{indent} <img src='{item.icon}' alt='{item.type}' width='{icon_size}' height='{icon_size}'> {item.type}s\n\n"
    config.output.write(header)


def write_parent_header(item: WorkItem, config: Config, level: int, icon_size: int):
    """Generate and write the header for the parent item."""
    parent_head_link = f"[#{item.id}]({item.url}) " if item.id != 0 else ""
    indent = "#" * level
    header = (
        f"{indent} <img src='{item.icon}' alt='{item.type}' width='{icon_size}' height='{icon_size}' parent='{item.parent}'> "
        f"{parent_head_link}{item.title}\n\n"
    )
    config.output.write(header)


def write_child_item(item: WorkItem, config: Config):
    """Write the child item to the markdown file."""
    config.output.write(
        f"- [#{item.id}]({item.url}) **{item.title}** {item.description} {item.parent}\n"
    )


async def main():
    """Main function to fetch and iterate through work items by type."""
    log.basicConfig(level=log.INFO)
    config = Config()
    session = config.session
    wi = WorkItems()
    await wi.get_items(config, session)
    items_by_type = wi.by_type

    iterate_and_print(items_by_type, config, session)
    await session.close()


if __name__ == "__main__":
    asyncio.run(main())
