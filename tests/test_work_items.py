""" Test cases for work_items.py """

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import aiohttp
from tests.test_main import WORK_ITEM
from src.work_items import WorkItems


def mock_config():
    """Mock the config object."""
    config = MagicMock()
    config.session = AsyncMock(spec=aiohttp.ClientSession)
    config.devops.url = "http://example.com"
    config.devops.org = "org"
    config.devops.project = "project"
    config.devops.query = "query"
    config.devops.pat = "pat"
    return config


@pytest.mark.asyncio
async def test_work_items_get_items():
    """Test the get_items function."""
    config = mock_config()
    wi = WorkItems()

    mock_response = {
        "value": [{"name": "Bug", "icon": {"url": "icon_url"}, "color": "FFFFFF"}]
    }

    with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        await wi.get_items(config, config.session)
        assert not wi.all


@pytest.mark.asyncio
async def test_work_items_fetch_item():
    """Test the fetch_item function."""
    config = mock_config()
    wi = WorkItems()

    wi.add_work_item(WORK_ITEM)
    item = await wi.fetch_item(config, 1, config.session)
    assert item.id == 1


def test_work_items_add_work_item():
    """Test the add_work_item function."""
    wi = WorkItems()
    wi.add_work_item(WORK_ITEM)
    assert WORK_ITEM in wi.all


def test_work_items_group_by_type():
    """Test the group_by_type function."""
    wi = WorkItems()
    wi.add_work_item(WORK_ITEM)
    grouped = wi.group_by_type([WORK_ITEM])
    assert len(grouped) == 1
    assert grouped[0].type == "Bug"
