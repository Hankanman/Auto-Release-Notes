""" Config module for DevOps and OpenAI configuration."""

import os
import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import aiohttp
from dotenv import load_dotenv
from .model import Model

DEFAULT_ENV = """
# DevOps and OpenAI Configuration
ORG_NAME=
PROJECT_NAME=
SOLUTION_NAME=
RELEASE_VERSION=
RELEASE_QUERY=
PAT=
GPT_API_KEY=
SOFTWARE_SUMMARY=
OUTPUT_FOLDER=Releases
MODEL=gpt-4o
GPT_BASE_URL=https://api.openai.com/v1
DEVOPS_BASE_URL=https://dev.azure.com
DEVOPS_API_VERSION=6.0
"""


@dataclass
class Output:
    """
    Output class for writing release notes to a file.

    Parameters:
        folder (str): The folder to store the release notes.
        name (str): The name of the software.
        version (str): The version of the software.

    Attributes:
        md (bool): Whether to output in markdown format.
        html (bool): Whether to output in HTML format.
        pdf (bool): Whether to output in PDF format.
        path (Path): The path to the output file.

    Functions:
        write: Write content to the output file.
        read: Read content from the output file.
        setup: Set up the initial content of the release notes file.
        set_summary: Set the summary of the release notes.
        set_toc: Set the table of contents of the release notes.
        finalize: Finalize the release notes by generating HTML and PDF outputs.
    """

    md: bool = True
    html: bool = False
    pdf: bool = False

    def __init__(self, folder: str, name: str, version: str):
        try:
            folder_path = Path(".") / folder
            self.path = (folder_path / f"{name}-v{version}.md").resolve()
            if self.path.exists():
                self.path.unlink()
            self.path.touch()
            folder_path.mkdir(parents=True, exist_ok=True)
            self.setup(name, version)
        except FileNotFoundError as e:
            print(f"Error occurred while initializing Output: {e}")
        except PermissionError as e:
            print(f"Error occurred while initializing Output: {e}")

    def write(self, content: str):
        """Write content to the output file."""
        with open(self.path, "a", encoding="utf-8") as file_output:
            file_output.write(content)

    def read(self) -> str:
        """Read content from the output file."""
        with open(self.path, "r", encoding="utf-8") as file:
            contents = file.read()
        return contents

    def setup(self, name: str, version: str):
        """Set up the initial content of the release notes file."""
        try:

            self.write(
                f"# Release Notes for {name} version v{version}\n\n"
                f"## Summary\n\n"
                f"<NOTESSUMMARY>\n\n"
                f"## Quick Links\n\n"
                f"<TABLEOFCONTENTS>\n\n"
            )
        except FileNotFoundError as e:
            print(f"Error occurred while setting up initial content: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting up initial content: {e}")

    def set_summary(self, summary: str):
        """Set the summary of the release notes."""
        try:
            self.write(self.read().replace("<NOTESSUMMARY>", summary))
        except FileNotFoundError as e:
            print(f"Error occurred while setting summary: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting summary: {e}")

    def set_toc(self, toc: str):
        """Set the table of contents of the release notes."""
        try:
            self.write(self.read().replace("<TABLEOFCONTENTS>", toc))
        except FileNotFoundError as e:
            print(f"Error occurred while setting table of contents: {e}")
        except PermissionError as e:
            print(f"Error occurred while setting table of contents: {e}")

    async def finalize(self, session: aiohttp.ClientSession):
        """
        Finalize the release notes by generating HTML and PDF outputs.

        Parameters:
            session (aiohttp.ClientSession): The aiohttp session object.
        """

        contents = self.read()
        if self.html:
            try:
                async with session.post(
                    "https://api.github.com/markdown",
                    json={"text": contents},
                    headers={"Content-Type": "application/json"},
                ) as html_response:
                    html_response.raise_for_status()
                    html_text = await html_response.text()
                    file_html = self.path.with_suffix(".html")
                    with open(file_html, "w", encoding="utf-8") as file:
                        file.write(html_text)
            except aiohttp.ClientError as e:
                print(f"Error occurred while making HTTP request: {e}")


@dataclass
class DevOps:
    """
    DevOps class for Azure DevOps configuration.

    Parameters:
        url (str): The base URL of the Azure DevOps organization.
        api_version (str): The API version of the Azure DevOps REST API.
        org (str): The name of the Azure DevOps organization.
        project (str): The name of the Azure DevOps project.
        query (str): The query to retrieve work items from Azure DevOps.
        pat (str): The personal access token for authenticating with Azure DevOps.

    Attributes:
        url (str): The base URL of the Azure DevOps organization.
        api_version (str): The API version of the Azure DevOps REST API.
        org (str): The name of the Azure DevOps organization.
        project (str): The name of the Azure DevOps project.
        query (str): The query to retrieve work items from Azure DevOps.
        pat (str): The personal access token for authenticating with Azure DevOps.
        fields (List[str]): The fields to retrieve from the work items.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, url: str, api_version: str, org: str, project: str, query: str, pat: str
    ):
        self.url = url
        self.api_version = api_version
        self.org = org
        self.project = project
        self.query = query
        self.pat = base64.b64encode(f":{pat}".encode()).decode()
        self.fields = [
            "System.Title",
            "System.Id",
            "System.State",
            "System.Tags",
            "System.Description",
            "System.Parent",
            "System.CommentCount",
            "System.WorkItemType",
            "Microsoft.VSTS.Common.Priority",
            "Microsoft.VSTS.TCM.ReproSteps",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.Scheduling.StoryPoints",
        ]


class Prompt:
    """
    Prompt class for generating prompts for the GPT model.

    Parameters:
        name (str): The name of the software.
        brief (str): The brief description of the software.
        release_notes (str): The release notes for the software.

    Attributes:
        summary (str): The summary prompt.
        item (str): The work item prompt.
    """

    def __init__(self, name: str, brief: str, release_notes: str):
        self._summary = (
            f"You are a developer working on a software project called {name}. You have been asked to review the following and write a summary "
            f"of the work completed for this release. Please keep your summary to one paragraph, do not write any bullet points or list, do not group your response in any way, "
            f"just a natural language explanation of what was accomplished. The following is a high-level summary of the purpose of the software for your context: {brief}\n"
            f"The following is a high-level summary of the release notes for your context: {release_notes}\n"
        )
        self._item = (
            "You are a developer writing a summary of the work completed for the given devops work item. Ignore timestamps and links. Return only the description text with no titles, "
            "headers, or formatting, if there is nothing to describe, return 'Addressed', always assume that the work item was completed. Do not list filenames or links. "
            "Please provide a single sentence of the work completed for the following devops work item details:\n"
        )

    @property
    def summary(self):
        """Get the summary prompt."""
        return self._summary

    @summary.setter
    def summary(self, value: str):
        self._summary = value

    @property
    def item(self):
        """Get the item prompt."""
        return self._item

    @item.setter
    def item(self, value: str):
        self._item = value


@dataclass
class Software:
    """
    Software class for software configuration.

    Attributes:
        name (str): The name of the software.
        version (str): The version of the software.
        brief (str): The brief description of the software.
        headers (List[str]): The headers for the software release notes.
        notes (str): The software release notes.

    Functions:
        add_header: Add a header to the software release notes.
    """

    name: str
    version: str
    brief: str
    headers: List[str] = field(default_factory=list)

    def add_header(self, value: str):
        """
        Add a header to the software release notes.

        Parameters:
            value (str): The header to add to the software release notes.

        Returns:
            List[str]: The updated list of headers for the software release notes.
        """
        self.headers.append(value)
        return self.headers

    @property
    def notes(self):
        """Get the software release notes."""
        return self.notes

    @notes.setter
    def notes(self, value: str):
        self.notes = self.notes + value
        return self.notes


@dataclass
class Config:
    """
    Configuration class for DevOps and OpenAI configuration.

    Attributes:
        software (Software): The software configuration.
        devops (DevOps): The DevOps configuration.
        model (Model): The GPT model configuration.
        prompts (Prompt): The prompt configuration.
        output (Output): The output configuration.
        session (aiohttp.ClientSession): The aiohttp session object.
    """

    software: Software
    devops: DevOps
    model: Model
    prompts: Prompt
    output: Output
    session: aiohttp.ClientSession

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        env_path: Path = Path(".") / ".env",
        output_folder: str = "Releases",
        software: Optional[Software] = None,
        devops: Optional[DevOps] = None,
        model: Optional[Model] = None,
        prompts: Optional[Prompt] = None,
        output: Optional[Output] = None,
    ):
        # Check if .env file exists, if not, create it with default values
        if not env_path.exists():
            try:
                with open(env_path, "w", encoding="utf-8") as env_file:
                    env_file.write(DEFAULT_ENV)
            except FileNotFoundError as e:
                print(f"Error occurred while creating .env file: {e}")
            except PermissionError as e:
                print(f"Error occurred while creating .env file: {e}")

        # Load environment variables from the .env file
        load_dotenv(env_path)

        # Set default output folder if not provided
        if output_folder is None:
            output_folder = str(os.getenv("OUTPUT_FOLDER", "Releases"))

        self.software = software or Software(
            name=str(os.getenv("SOLUTION_NAME")),
            version=str(os.getenv("RELEASE_VERSION")),
            brief=str(os.getenv("SOFTWARE_SUMMARY")),
        )

        self.devops = devops or DevOps(
            url=str(os.getenv("DEVOPS_BASE_URL")),
            api_version=str(os.getenv("DEVOPS_API_VERSION")),
            org=str(os.getenv("ORG_NAME")),
            project=str(os.getenv("PROJECT_NAME")),
            pat=str(os.getenv("PAT")),
            query=str(os.getenv("RELEASE_QUERY")),
        )

        self.model = model or Model(
            key=str(os.getenv("GPT_API_KEY")),
            url=str(os.getenv("MODEL_BASE_URL")),
            model_name=str(os.getenv("MODEL")),
        )

        self.prompts = prompts or Prompt(
            self.software.name,
            self.software.brief,
            self.software.brief,
        )

        self.output = output or Output(
            folder=output_folder,
            name=self.software.name,
            version=self.software.version,
        )

        self.session = aiohttp.ClientSession()
