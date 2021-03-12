# Copyright (c) 2020 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

import json
import os, csv
from cloudvision.Connector.codec import Path, FrozenDict


def pretty_print(dataDict):
    def default(obj):
        if isinstance(obj, Path):
            return obj._keys
        if isinstance(obj, (FrozenDict, dict)):
            return obj._dict
    print(json.dumps(
        dataDict, default=default, indent=4,
        sort_keys=True, separators=(",", ":")
    ))

def fileWrite(filePath,data,fileType,option="c"):
    """ filePath - full directory and filename for file
        Function returns True is file is successfully written to media
        data - content to write to file
        fileType
          json - JSON object
          txt - text string
          csvList - list of row lists
          csvDict - list of row dictionaries,
                    first element of the list is a list of headers
        option
          a - append
          w - overwrite
          c - choose option based on file existence
        """
    if option.lower() == "c":
        if os.path.exists(filePath) and os.path.getsize(filePath) > 0:
            print(f"Appending data to file: {filePath}")
            fileOp = "a"
        else:
            print(f"Creating file {filePath} to write data to")
            fileOp = "w"
    else:
        fileOp = option.lower()
    directory, filename = os.path.split(filePath)
    try:
        os.makedirs(directory)
    except OSError:
        # directory already exists
        pass
    else:
        print(f"Directory did not exist: Created - {directory}")
    try:
        with open(filePath, fileOp) as FH:
            if fileOp == "a":
                FH.seek(0, 2)
            if fileType.lower() == "json":
                #json.dump(json.loads(data), FH, sort_keys = True, indent = 4, ensure_ascii = True)
                json.dump(data, FH, sort_keys = True, indent = 4, ensure_ascii = True)
                result = True
            elif fileType.lower() == "txt":
                FH.writelines(data)
                result = True
            elif fileType == "csvList":
                write_csv = csv.writer(FH, dialect="excel")
                write_csv.writerows(data)
                result = True
            elif fileType == "csvDict":
                headers = data[0]
                write_csv = csv.DictWriter(FH, fieldnames=headers, dialect="excel")
                write_csv.writeheader()
                for row in data[1:]:
                    write_csv.writerow(row)
                result = True
            else:
                print(f"Invalid fileType: {fileType}")
                result = False
    except IOError as file_error:
        print(f"{filename} File Write Error: {file_error}")
        result = False
    return result
