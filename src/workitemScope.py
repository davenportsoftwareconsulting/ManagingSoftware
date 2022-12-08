from workitemAdapter import ExternalWorkitemInterface
from datetime import datetime

class workitemScope:
    def __init__(
            self, externalInterface: ExternalWorkitemInterface = None, project: str = None,
            assigneeList: list = None, workitemTypeList: list = None, lastUpdated: datetime = None,
            stateList: list = None, titleContains: str = None, iterationPathUnder: str = None, areaPathUnder: str = None) -> None:
        
        self.project = project
        self.assigneeList = assigneeList
        self.workitemTypeList = workitemTypeList
        self.lastUpdated = lastUpdated
        self.stateList = stateList
        self.titleContains = titleContains
        self.iterationPathUnder = iterationPathUnder
        self.areaPathUnder = areaPathUnder
        self.externalInterface = externalInterface

    def Get_Query_String(self):
        if self.externalInterface == ExternalWorkitemInterface.ADO:
            returnString = "SELECT [System.Id] FROM workitems WHERE "
            whereConditions = []
            if self.project:
                whereConditions.append(f"[System.TeamProject] = {self.project}")
            if self.assigneeList:
                assigneeCondition = ""
                for assignee in self.assigneeList:
                    assigneeCondition += f"'{assignee}',"
                assigneeCondition = assigneeCondition[:-1]
                whereConditions.append(f"[System.AssignedTo] IN ({assigneeCondition})") # TODO: need to test and see that the in operator works here
            if self.workitemTypeList:
                typeCondition = ""
                for workitemType in self.workitemTypeList:
                    typeCondition += f"'{workitemType}',"
                typeCondition = typeCondition[:-1]
                whereConditions.append(f"[System.WorkItemType] IN ({typeCondition})")
            if self.lastUpdated:
                whereConditions.append(f"[System.ChangedDate] > {self.lastUpdated}")
            if self.stateList:
                stateCondition = ""
                for state in self.stateList:
                    stateCondition += f"'{state}',"
                stateCondition = stateCondition[:-1]
                whereConditions.append(f"[System.State] IN ({self.project})")
            if self.titleContains:
                whereConditions.append(f"[System.Title] CONTAINS '{self.titleContains}'")
            if self.iterationPathUnder:
                whereConditions.append(f"[System.IterationPath] UNDER '{self.iterationPathUnder}'")
            if self.areaPathUnder:
                whereConditions.append(f"[System.AreaPath] UNDER {self.areaPathUnder}")

            for condition in whereConditions:
                returnString += f"{condition} AND"
            returnString = returnString[:-4]


        elif self.externalInterface == ExternalWorkitemInterface.JIRA:
            returnString = ""

        return returnString