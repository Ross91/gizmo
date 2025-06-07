# encoding utf-8
# Author: Ross Harrop
# Date: 10/01/2023
# Version: 0.1
"""
Store information locally on a users PC's, for easy retreval.
"""

import os
import json
import logging
from collections import UserDict
from .. import constants as c

log = logging.getLogger("Record")
log.setLevel(logging.INFO)


class Record(UserDict):
    """This should be instantiated where ever it's needed"""
    _folder = 'Record'
    _path = ''

    def __init__(self, name):
        super().__init__()

        self._path = os.path.join(c.APP_DATA, self._folder, name)
        self.load()

    def load(self):
        """Load & read file then store data as dictionary."""

        if not os.path.exists(self._path):
            log.info(f"New file: {self._path}")
            return 
        
        with open(self._path, "r") as f:
            data = json.loads(f.read()) or {}
            log.info(f"Loaded file: {self._path}")
         
        self.update(data)

    def save(self):
        """Save dictionary to file in AppData/local"""

        with open(self._path, 'w') as f:
            f.write(json.dumps(self, indent=4, ordered_keys=True))
            log.info(f"Saved file: {self._path}")

    def delete(self):
        """Delete the file assocaited with the current instance."""

        if os.path.exists(self._path):
            os.remove(self._path)
            log.info(f"Deleted file: {self._path}")

    def __repr__(self):
        log.info(json.dumps(self, indent=4, ordered_keys=True))


class UserDictEndoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Record):
            return obj.items()
        return json.JSONEncoder.default(self, obj)


class UserDictDecoder(json.JSONDecoder):
    def default(self, obj):
        if isinstance(obj, Record):
            return "Something"
        return json.JSONDecoder.decode(obj)
