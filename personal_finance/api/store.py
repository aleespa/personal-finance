import uuid
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from personal_finance.account import AccountList


@dataclass
class LoadedWorkbook:
    id: str
    accounts: AccountList
    holdings: Optional[pd.DataFrame]
    year_data: dict[int, pd.DataFrame]


class WorkbookStore:
    """Holds the most recently uploaded workbook.

    The app is single user, so a new upload replaces the previous one and any
    older id stops working.
    """

    def __init__(self):
        self._current: Optional[LoadedWorkbook] = None

    def put(self, accounts: AccountList, holdings, year_data) -> LoadedWorkbook:
        workbook = LoadedWorkbook(uuid.uuid4().hex, accounts, holdings, year_data)
        self._current = workbook
        return workbook

    def get(self, workbook_id: str) -> LoadedWorkbook:
        workbook = self._current
        if workbook is None or workbook.id != workbook_id:
            raise HTTPException(404, "Workbook not found. Upload it again.")
        return workbook
