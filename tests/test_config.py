""" Test for config module"""

import aiohttp
from src.config import Config, Output, DevOps, Prompt, Software
from src.model import Model


def test_config_initialization():
    """Test config_init"""
    config = Config()
    assert isinstance(config.software, Software)
    assert isinstance(config.devops, DevOps)
    assert isinstance(config.model, Model)
    assert isinstance(config.prompts, Prompt)
    assert isinstance(config.output, Output)
    assert isinstance(config.session, aiohttp.ClientSession)


def test_output_initialization():
    """Test output_init"""
    output = Output("test_folder", "test_name", "1.0")
    assert output.path.name == "test_name-v1.0.md"
    assert output.path.parent.name == "test_folder"


def test_devops_initialization():
    """Test devops_init"""
    devops = DevOps("url", "api_version", "org", "project", "query", "pat")
    assert devops.url == "url"
    assert devops.api_version == "api_version"
    assert devops.org == "org"
    assert devops.project == "project"
    assert devops.query == "query"
    assert devops.pat is not None
    assert len(devops.fields) > 0
