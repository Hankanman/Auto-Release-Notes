# generated by datamodel-codegen:
#   filename:  <stdin>
#   timestamp: 2024-06-09T07:10:30+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Column(BaseModel):
    referenceName: str
    name: str
    url: str


class WorkItem(BaseModel):
    id: int
    url: str


class Model(BaseModel):
    queryType: str
    queryResultType: str
    asOf: str
    columns: List[Column]
    workItems: List[WorkItem]