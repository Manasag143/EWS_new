from pydantic import BaseModel

class Params(BaseModel):
    """
    Params - pydantic model to validate the structure of input JSON for post request call
    """
    docName: str
    docPath: dict
    processId: str
    callBackURL: str
    companyCode : str
    requestedBy : str
