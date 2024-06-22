""" This module contains all the enums used in the application. """

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class WorkItemType(Enum):
    """
    Represents the type of work item.
    """

    BUG = "Bug"
    EPIC = "Epic"
    FEATURE = "Feature"
    TASK = "Task"
    USER_STORY = "User Story"
    PRODUCT_BACKLOG_ITEM = "Product Backlog Item"
    OTHER = "Other"


class LogLevel(Enum):
    """
    Enumeration representing different log levels.

    Attributes:
        INFO (str): Represents the INFO log level.
        WARNING (str): Represents the WARNING log level.
        ERROR (str): Represents the ERROR log level.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


class Field(Enum):
    """
    Enum representing the different fields of a work item.
    """

    TITLE = "System.Title"
    DESCRIPTION = "System.Description"
    REPRO_STEPS = "Microsoft.VSTS.TCM.ReproSteps"
    COMMENTS = "System.Comments"
    PARENT = "System.Parent"
    WORK_ITEM_TYPE = "System.WorkItemType"
    AREA_PATH = "System.AreaPath"
    TEAM_PROJECT = "System.TeamProject"
    STATE = "System.State"
    REASON = "System.Reason"
    ASSIGNED_TO = "System.AssignedTo"
    CREATED_DATE = "System.CreatedDate"
    CREATED_BY = "System.CreatedBy"
    CHANGED_DATE = "System.ChangedDate"
    CHANGED_BY = "System.ChangedBy"
    PRIORITY = "Microsoft.VSTS.Common.Priority"
    SEVERITY = "Microsoft.VSTS.Common.Severity"
    VALUE_AREA = "Microsoft.VSTS.Common.ValueArea"
    ITERATION_PATH = "System.IterationPath"
    TAGS = "System.Tags"


class ResponseStatus(Enum):
    """
    Enum class representing the response status codes.

    Attributes:
        SUCCESS (int): Represents a successful response (status code 200).
        RATE_LIMIT (int): Represents a rate limit response (status code 429).
        ERROR (int): Represents an error response (status code 500).
        NOT_FOUND (int): Represents a not found response (status code 404).
        NOT_AUTHORIZED (int): Represents a not authorized response (status code 401).
        FORBIDDEN (int): Represents a forbidden response (status code 403).
    """

    SUCCESS = 200
    RATE_LIMIT = 429
    ERROR = 500
    NOT_FOUND = 404
    NOT_AUTHORIZED = 401
    FORBIDDEN = 403


class OutputFormat(Enum):
    """
    Represents the available output formats for generating release notes.
    """

    MARKDOWN = "md"
    HTML = "html"
    PDF = "pdf"


class WorkItemState(Enum):
    """
    Enum representing the different states of a work item.
    """

    NEW = "New"
    ACTIVE = "Active"
    APPROVED = "Approved"
    COMMITTED = "Committed"
    DONE = "Done"
    REMOVED = "Removed"


@dataclass
class Icon:
    """Represents an icon for a work item."""

    url: str


@dataclass
class Link:
    """Represents a link for a work item."""

    href: str


# pylint: disable=invalid-name
@dataclass
class Links:
    """Represents the links for a work item."""

    html: Link
    workItemIcon: Icon
    workItemComments: Link


@dataclass
class WorkItem:
    """Represents a work item."""

    name: str
    icon: Icon
    id: int
    fields: Dict[Field, Any]
    _links: Links
    url: str
