# writes errors
from datetime import datetime

LOG_PATH = "crashes/"

def catchError(error, errorPath = None, errorStr = None):
     file_name = datetime.now().strftime("%d_%m_%Y_%H_%M_%S.log")
     try:
          crashFile = open(f"{LOG_PATH}{file_name}", "w+")
          crashFile.write(
               f"Error catched in: {errorPath}\nError on line: {errorStr}\n\n{str(error)}"
          )
          crashFile.close()
     except Exception as e:
          print(e) # holy shit, can it even crash? This def meant to write crashes, not this please