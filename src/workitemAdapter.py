from enum import Enum
import requests
import time
from datetime import datetime, timedelta
from flask import Flask
import os

app = Flask(__name__)

class ExternalWorkitemInterface(Enum):
    JIRA = 0
    ADO = 1
    WORKDAY = 2

class TimeGranularity(Enum):
    SECOND = 5
    MINUTE = 4
    HOUR = 3
    DAY = 2
    MONTH = 1
    YEAR = 0

class WorkitemAdapter:
    fieldList = []
    fieldDataList = []
    
    def __init__(self, connectionType: ExternalWorkitemInterface, username: str, password: str, organization: str, project: str = None) -> None:
        self.connectionType = connectionType
        self.username = username
        self.password = password
        self.organization = organization
        self.project = project

        if self.connectionType == ExternalWorkitemInterface.ADO:
            self.baseURL = f"https://dev.azure.com/{organization}/{project}/_apis"
            self.baseWorkitemURL = f"{self.baseURL}/wit/workitems"
            self.testURL = f"{self.baseURL}/wit/fields"
            self.credentials = ('',self.password)
            self.requestContentType = "application/json-patch+json"
            self.postContentType = "application/json"
            for fieldEntry in self.__genericRequest(f"{self.baseURL}/wit/fields")['value']:
                self.fieldList.append(fieldEntry['referenceName'])
                self.fieldDataList.append(fieldEntry)

        if self.connectionType == ExternalWorkitemInterface.JIRA:
            self.baseURL = f"https://{organization}.atlassian.net/rest/api"
            self.baseWorkitemURL = f"{self.baseURL}/2/issue"
            self.testURL = f"{self.baseURL}/2/permissions"
            self.credentials = (self.username, self.password)
            self.requestContentType = "application/json"
            self.postContentType = "application/json"
            for fieldEntry in self.__genericRequest(f"{self.baseURL}/latest/field"):
                self.fieldList.append(fieldEntry['key'])
                self.fieldDataList.append(fieldEntry)

    def connection_test(self):
        testResponse = self.__genericRequest(self.testURL)
        if testResponse:
            return True
        else:
            return False

    def __str__(self) -> str:
        return f"Connection Type: {self.connectionType.name}\nConnection URL: {self.baseURL}"

    def __genericRequest(self, url: str):
        goodValue = False
        for i in range(0, 3):
            r = requests.get(url,
                headers={'Content-Type': self.requestContentType},
                auth=self.credentials)

            if r.status_code == 200:
                goodValue = True
                break

            print(f"Unable to process: {url} trying again")
            if i != 2:
                time.sleep(5 + (5 * i))

        if not goodValue:
            return None

        return r.json()
        
    def __jql_search_request(self, searchString: str):
        url = f"{self.baseURL}/2/search?jql={searchString}"
        return self.__genericRequest(url)

    def __genericPostRequest(self, url: str, jsonData):
        goodValue = False
        for i in range(0, 3):
            r = requests.post(url,
                json=jsonData,
                headers={'Content-Type': self.postContentType},
                auth=self.credentials)

            if r.status_code == 200:
                goodValue = True
                break

            print(f"Unable to process: {url} trying again")
            if i != 2:
                time.sleep(5 + (5 * i))

        if not goodValue:
            return None

        return r.json()
        
    def Str_To_Datetime(self, dateString: str) -> datetime:
        inputFormat = "%Y-%m-%d %H:%M:%S"
        dateString = dateString.replace('T', ' ')
        dateString = dateString.replace('Z', '')
        if '+' in dateString:
            dateString = dateString[:dateString.find('+')]
        if '.' in dateString:
            dateString = dateString[:dateString.find('.')]

        if '-' in dateString[:6]:
            try:
                returnDatetime = datetime.strptime(dateString, inputFormat)
            except:
                inputFormat = "%Y-%m-%d"
                returnDatetime = datetime.strptime(dateString, inputFormat)
        else:
            try:
                inputFormat = "%m/%d/%Y %H:%M:%S"
                returnDatetime = datetime.strptime(dateString, inputFormat)
            except:
                inputFormat = "%m/%d/%Y"
                returnDatetime = datetime.strptime(dateString, inputFormat)

        return returnDatetime

    def __number_compare(self, num1: int, num2: int):
        if num1 > num2:
            return 1
        elif num2 > num1:
            return -1
        else:
            return 0

    def Compare_Dates(self, day1: datetime, day2: datetime, granularity: TimeGranularity = TimeGranularity.DAY):
        yearCompare = self.__number_compare(day1.year, day2.year)
        monthCompare = self.__number_compare(day1.month, day2.month)
        dayCompare = self.__number_compare(day1.day, day2.day)
        hourCompare = self.__number_compare(day1.hour, day2.hour)
        minuteCompare = self.__number_compare(day1.minute, day2.minute)
        secondCompare = self.__number_compare(day1.second, day2.second)
        compareList = [yearCompare, monthCompare, dayCompare, hourCompare, minuteCompare, secondCompare]

        for i in range(0, granularity.value + 1):
            if compareList[i] != 0:
                return compareList[i]
        return 0

    def Get_Workitem_Response(self, workitemID: str):
        return self.__genericRequest(f"{self.baseWorkitemURL}/{workitemID}")

    def Get_Workitem_Fields(self, workitemID: str):
        workitemResponse = self.Get_Workitem_Response(workitemID)
        if self.connectionType in [ExternalWorkitemInterface.ADO, ExternalWorkitemInterface.JIRA]:
            return workitemResponse['fields']

    def Get_Workitem_Associations(self, workitemID: str):
        returnAssociations = {
            "Parent": None,
            "Children": [],
            "Related": []
        }
        if self.connectionType == ExternalWorkitemInterface.ADO:
            associationResponse = self.__genericRequest(f"{self.baseWorkitemURL}/{workitemID}?$expand=relations")
            if 'relations' not in associationResponse:
                return None

            for association in associationResponse['relations']:
                associationType = association['attributes']['name']
                associationID = association['url'].split('/')[-1]

                if associationType == "Parent":
                    returnAssociations['Parent'] = associationID
                elif associationType == "Child":
                    returnAssociations['Children'].append(associationID)
                elif associationType == "Related":
                    returnAssociations['Related'].append(associationID)

        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            workitemResponse = self.Get_Workitem_Response(workitemID)
            if 'parent' in workitemResponse['fields']:
                returnAssociations['Parent'] = workitemResponse['fields']['parent']['key']

            jqlChildrenSearchResponse = self.__jql_search_request(f"%22Parent%22=%22{workitemID}%22")
            for child in jqlChildrenSearchResponse['issues']:
                returnAssociations['Children'].append(child['key'])

            if 'issuelinks' in workitemResponse['fields']:
                for linkedIssue in workitemResponse['fields']['issuelinks']:
                    linkType = linkedIssue['type']['name']
                    if linkType == 'Relates':
                        if 'inwardIssue' in linkedIssue:
                            linkKey = linkedIssue['inwardIssue']['key']
                        else:
                            linkKey = linkedIssue['outwardIssue']['key']
                        returnAssociations['Related'].append(linkKey)

        return returnAssociations

    def Get_Workitem_Title(self, workitemID: str):
        workitemFields = self.Get_Workitem_Response(workitemID)['fields']

        if 'System.Title' not in workitemFields and 'summary' not in workitemFields:
            return None

        if self.connectionType == ExternalWorkitemInterface.ADO:
            return workitemFields['System.Title']
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            return workitemFields['summary']

    def Get_Workitem_State(self, workitemID: str):
        workitemFields = self.Get_Workitem_Response(workitemID)['fields']

        if 'System.State' not in workitemFields and 'status' not in workitemFields:
            return None

        if self.connectionType == ExternalWorkitemInterface.ADO:
            return workitemFields['System.State']
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            return workitemFields['status']['name']

    def Get_Workitem_Description(self, workitemID: str):
        workitemFields = self.Get_Workitem_Response(workitemID)['fields']

        if 'System.Description' not in workitemFields and 'description' not in workitemFields:
            return None

        if self.connectionType == ExternalWorkitemInterface.ADO:
            return workitemFields['System.Description']  # TODO: decode HTML to raw text 
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            return workitemFields['description']

    def Get_Workitem_Assignee(self, workitemID: str):
        workitemFields = self.Get_Workitem_Response(workitemID)['fields']

        if 'System.AssignedTo' not in workitemFields and 'assignee' not in workitemFields:
            return None

        if self.connectionType == ExternalWorkitemInterface.ADO:
            return workitemFields['System.AssignedTo']['displayName']
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            return workitemFields['assignee']['displayName']

    def Get_Workitem_Created_Date(self, workitemID: str):
        workitemFields = self.Get_Workitem_Response(workitemID)['fields']

        if 'System.CreatedDate' not in workitemFields and 'created' not in workitemFields:
            return None

        if self.connectionType == ExternalWorkitemInterface.ADO:
            return self.Str_To_Datetime(workitemFields['System.CreatedDate'])
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            return self.Str_To_Datetime(workitemFields['created'])

    def Get_Workitem_History(self, workitemID: str):
        if self.connectionType == ExternalWorkitemInterface.JIRA:
            historyURL = f"{self.baseWorkitemURL}/{workitemID}?expand=changelog"
            historyList = self.__genericRequest(historyURL)['changelog']['histories']
        elif self.connectionType == ExternalWorkitemInterface.ADO:
            historyURL = f"{self.baseWorkitemURL}/{workitemID}/updates"
            historyList = self.__genericRequest(historyURL)['value']

        return historyList

    def Get_Workitem_Field_History(self, workitemID: str, field: str, fromDate: datetime = None, toDate: datetime = None, embeddedReturn: list = None):
        if field not in self.fieldList:
            raise ValueError(f"Unable to find field: {field}")

        workitemFields = self.Get_Workitem_Fields(workitemID)
        workitemCreatedDate = self.Get_Workitem_Created_Date(workitemID)
        timeNow = datetime.now()
        
        if not fromDate:
            fromDate = workitemCreatedDate
        if not toDate:
            toDate = timeNow

        fieldChanges = []
        returnArray = []
        historyList = self.Get_Workitem_History(workitemID)
        if self.connectionType == ExternalWorkitemInterface.JIRA:
            for historyItem in historyList:
                if 'items' not in historyItem:
                    pass

                for historyChange in historyItem['items']:
                    historyChangeField = historyChange['field']

                    if historyChangeField == field:
                        historyChangeFromString = historyChange['fromString']
                        historyChangeToString = historyChange['toString']
                        historyDate = self.Str_To_Datetime(historyItem['created'])

                        fieldChanges.append({
                            'From': historyChangeFromString,
                            'To': historyChangeToString,
                            'Date': historyDate})

            fieldChanges = fieldChanges[::-1]

        elif self.connectionType == ExternalWorkitemInterface.ADO:
            for historyItem in historyList:
                if 'fields' not in historyItem:
                    continue

                for historyChange in historyItem['fields']:
                    historyChangeField = historyChange

                    if historyChangeField == field:
                        if 'oldValue' not in historyItem['fields'][historyChange]:
                            historyChangeFromString = None
                        else:
                            if embeddedReturn:
                                historyChangeFromString = historyItem['fields'][historyChange]['oldValue']
                                for fieldReturn in embeddedReturn:
                                    historyChangeFromString = historyChangeFromString[fieldReturn]
                                
                            else:
                                historyChangeFromString = historyItem['fields'][historyChange]['oldValue']

                        if 'newValue' not in historyItem['fields'][historyChange]:
                            historyChangeToString = None
                        else:
                            if embeddedReturn:
                                historyChangeToString = historyItem['fields'][historyChange]['newValue']
                                for fieldReturn in embeddedReturn:
                                    historyChangeToString = historyChangeToString[fieldReturn]

                            else:
                                historyChangeToString = historyItem['fields'][historyChange]['newValue']

                        if 'System.ChangedDate' in historyItem['fields']:
                            historyDate = self.Str_To_Datetime(historyItem['fields']['System.ChangedDate']['newValue'])
                        else:
                            historyDate = self.Str_To_Datetime(historyItem['revisedDate'])

                        fieldChanges.append({
                            'From': historyChangeFromString,
                            'To': historyChangeToString,
                            'Date': historyDate})
        
        dateTimeDelta = (toDate - fromDate)
        numberOfDays = dateTimeDelta.days + 1
        if dateTimeDelta.seconds > 0:
            numberOfDays += 1

        previousVal = None
        fieldChangIndex = 0
        if len(fieldChanges) == 0:
            if field in workitemFields:
                previousVal = workitemFields[field]
                if embeddedReturn:
                    for returnField in embeddedReturn:
                        previousVal = previousVal[returnField]
        else:
            for index, fieldChange in enumerate(fieldChanges):
                if self.Compare_Dates(fromDate, fieldChange['Date']) in [0, -1]:
                    fieldChangIndex = index
                    previousVal = fieldChanges[index]['From']
                    break
            if not previousVal: # There is a field change, but it happened before the scope of the report
                previousVal = fieldChanges[0]['To']

        for i in range(0, numberOfDays):
            currentDay = fromDate + timedelta(days=i)

            if len(fieldChanges) == 0:
                returnArray.append((currentDay, previousVal))
                continue

            if self.Compare_Dates(fieldChanges[fieldChangIndex]['Date'], currentDay) == 0:
                while fieldChangIndex + 1 < len(fieldChanges) and self.Compare_Dates(fieldChanges[fieldChangIndex + 1]['Date'], currentDay) == 0:
                    fieldChangIndex += 1
                returnArray.append((currentDay, fieldChanges[fieldChangIndex]['To']))
                previousVal = fieldChanges[fieldChangIndex]['To']
                if fieldChangIndex + 1 < len(fieldChanges):
                    fieldChangIndex += 1
            else:
                returnArray.append((currentDay, previousVal))

        return returnArray

    def Get_Projects(self):
        if self.connectionType == ExternalWorkitemInterface.ADO:
            return [self.project]
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            projectList = []
            projectResponse = self.__genericRequest(f"{self.baseURL}/latest/project")
            for project in projectResponse:
                projectList.append(project['name'])
            return projectList

    def Get_Features(self):
        featureList = []
        if self.connectionType == ExternalWorkitemInterface.ADO:
            queryData = {
                            "query": "Select [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] = 'Feature'"
                        }
            featureResponse = self.__genericPostRequest(f"{self.baseURL}/wit/wiql?api-version=7.1-preview.2", queryData)
            if 'workItems' not in featureResponse:
                return []

            for feature in featureResponse['workItems']:
                featureList.append(str(feature['id']))

        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            featureResponse = self.__genericRequest(f"{self.baseURL}/latest/search?jql=issuetype=Feature")
            for feature in featureResponse['issues']:
                featureList.append(feature['key'])

        return featureList

    def Get_Workitem_Sprint(self, workitemID: str):
        workitemFields = self.Get_Workitem_Fields(workitemID)
        if self.connectionType == ExternalWorkitemInterface.ADO:
            return workitemFields['System.IterationPath'].split('\\')[-1]
        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            for field in self.fieldDataList:
                if field['name'] == 'Sprint':
                    sprintField = field['id']
                    break
            return workitemFields[sprintField][0]['name']

    def Get_Sprints(self, inputScope: str):
        sprintDict = {}
        if self.connectionType == ExternalWorkitemInterface.ADO:
            iterationsURL = f"https://dev.azure.com/{self.organization}/{self.project}/{inputScope}/_apis/work/teamsettings/iterations"
            try:
                iterationsValue = self.__genericRequest(iterationsURL)['value']
            except Exception as _:
                raise ValueError(f"{inputScope} not a valid team")

            for sprint in iterationsValue:
                sprintDict[sprint['name']] = {'Start': self.Str_To_Datetime(sprint['attributes']['startDate']), 'End': self.Str_To_Datetime(sprint['attributes']['finishDate'])}

        if self.connectionType == ExternalWorkitemInterface.JIRA:
            iterationsURL = f"https://{self.organization}.atlassian.net/rest/agile/1.0/board/{inputScope}/sprint"
            try:
                iterationsValue = self.__genericRequest(iterationsURL)['values'][::-1]
            except Exception as _:
                raise ValueError(f"{inputScope} not a valid board")

            for sprint in iterationsValue:
                sprintDict[sprint['name']] = {'Start': self.Str_To_Datetime(sprint['startDate']), 'End': self.Str_To_Datetime(sprint['endDate'])}

        return sprintDict

    def Get_Board_or_Teams(self):
        returnList = []
        if self.connectionType == ExternalWorkitemInterface.JIRA:
            boardsURL = f"https://{self.organization}.atlassian.net/rest/agile/1.0/board"
            for board in self.__genericRequest(boardsURL)['values']:
                returnList.append((board['name'], board['id']))

        elif self.connectionType == ExternalWorkitemInterface.ADO:
            teamsURL = f"https://dev.azure.com/{self.organization}/_apis/projects/{self.project}/teams"
            for team in self.__genericRequest(teamsURL)['value']:
                returnList.append((team['name'], team['id']))
                
        return returnList

    def Get_Employees(self):
        returnList = []
        if self.connectionType == ExternalWorkitemInterface.JIRA:
            url = f"{self.baseURL}/2/users/search"
            for user in self.__genericRequest(url):
                if 'displayName' in user and 'emailAddress' in user and user['active']:
                    returnList.append((user['displayName'], user['emailAddress']))

        elif self.connectionType == ExternalWorkitemInterface.ADO:
            url = f"https://vssps.dev.azure.com/{self.organization}/_apis/graph/users?api-version=7.0-preview.1" #TODO Currently works in Chrome and not in requests
            for user in self.__genericRequest(url)['value']:
                if 'displayName' in user and 'mailAddress' in user and user['domain'] not in ['Build']:
                    returnList.append((user['displayName'], user['mailAddress']))
                
        return returnList

    def Is_Workitem_ChangedBy(self, workitemID: str, employee: str, fromDate: datetime = None, toDate: datetime = None) -> bool:
        employee = employee.strip()
        returnList = []
        if ' ' in employee:
            employeeIdentifierType = "Name"
        elif '@' in employee:
            employeeIdentifierType = "Email"
        else:
            raise ValueError(f"{employee} must either be a name (contain a ' ') or be an email (contain an @)")

        fromDate = datetime(year=1999, month=1, day=1) if not fromDate else fromDate
        toDate = datetime.now() if not toDate else toDate

        workitemHistory = self.Get_Workitem_History(workitemID)

        if self.connectionType == ExternalWorkitemInterface.ADO:
            for historyPoint in workitemHistory:
                historyPointName = historyPoint['revisedBy']['displayName'].lower()
                historyPointEmail = historyPoint['revisedBy']['uniqueName'].lower()
                historyPointDate = historyPoint['fields']['System.ChangedDate']['newValue'] if 'fields' in historyPoint and 'System.ChangedDate' in historyPoint['fields'] else historyPoint['revisedDate']
                historyPointDate = self.Str_To_Datetime(historyPointDate)

                if historyPointDate > fromDate and historyPointDate < toDate and\
                        ((employeeIdentifierType == "Name" and employee.lower() == historyPointName) or\
                        (employeeIdentifierType == "Email" and employee.lower() == historyPointEmail)):
                    returnList.append(historyPointDate)

        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            for historyPoint in workitemHistory:
                historyPointName = historyPoint['author']['displayName'].lower()
                historyPointEmail = historyPoint['author']['emailAddress'].lower()
                historyPointDate = historyPoint['created']
                historyPointDate = self.Str_To_Datetime(historyPointDate)
                
                if historyPointDate > fromDate and historyPointDate < toDate and\
                        ((employeeIdentifierType == "Name" and employee.lower() == historyPointName) or\
                        (employeeIdentifierType == "Email" and employee.lower() == historyPointEmail)):
                    returnList.append(historyPointDate)

        return returnList

    def Get_Employee_Contributions(self, employee: str, fromDate: datetime = None, toDate: datetime = None) -> list:
        totalChangeList = []
        if self.connectionType == ExternalWorkitemInterface.ADO:
            queryData = {
                            "query": "Select [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType] IN ('User Story','Bug','Issue')"
                        }
            workitemResponse = self.__genericPostRequest(f"{self.baseURL}/wit/wiql?api-version=7.1-preview.2", queryData) # TODO Test ADO part of this function
            if 'workItems' not in workitemResponse:
                return []

            for workitem in workitemResponse['workItems']:
                changeList = self.Is_Workitem_ChangedBy(workitemID=workitem['id'], employee=employee, fromDate=fromDate, toDate=toDate)
                for changeDate in changeList:
                    totalChangeList.append((workitem['id'], changeDate))

        elif self.connectionType == ExternalWorkitemInterface.JIRA:
            workitemResponse = self.__genericRequest(f"{self.baseURL}/latest/search?jql=issuetype in (Story,Subtask)")
            for workitem in workitemResponse['issues']:
                changeList = self.Is_Workitem_ChangedBy(workitemID=workitem['id'], employee=employee, fromDate=fromDate, toDate=toDate)
                for changeDate in changeList:
                    totalChangeList.append((workitem['id'], changeDate))

        return totalChangeList

@app.route("/init")
def route_init():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Base URL": thisWorkitemAdapter.baseURL,
        "Credentials": thisWorkitemAdapter.credentials,
        "Request Content Type": thisWorkitemAdapter.requestContentType
    })

@app.route("/test")
def route_test():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Result": thisWorkitemAdapter.connection_test()
    })

@app.route("/workitem/<string:workitemId>")
def route_workitemResponse(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return(
        thisWorkitemAdapter.Get_Workitem_Response(workitemID=workitemId)
    )

@app.route("/workitem/fields/<string:workitemId>")
def route_workitemFields(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "fields": thisWorkitemAdapter.Get_Workitem_Fields(workitemID=workitemId)
    })

@app.route("/workitem/associations/<string:workitemId>")
def route_workitemAssociations(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "fields": thisWorkitemAdapter.Get_Workitem_Associations(workitemID=workitemId)
    })

@app.route("/workitem/title/<string:workitemId>")
def route_workitemTitle(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_Title(workitemID=workitemId)
    })

@app.route("/workitem/state/<string:workitemId>")
def route_workitemState(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_State(workitemID=workitemId)
    })

@app.route("/workitem/description/<string:workitemId>")
def route_workitemDescription(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_Description(workitemID=workitemId)
    })
    
@app.route("/workitem/assignee/<string:workitemId>")
def route_workitemAssignee(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_Assignee(workitemID=workitemId)
    })

@app.route("/workitem/created/<string:workitemId>")
def route_workitemCreatedDate(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_Created_Date(workitemID=workitemId)
    })

@app.route("/workitem/history/<string:workitemId>")
def route_workitemHistory(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_History(workitemID=workitemId)
    })

@app.route("/workitem/sprint/<string:workitemId>")
def route_workitemSprint(workitemId):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Value": thisWorkitemAdapter.Get_Workitem_Sprint(workitemID=workitemId)
    })

@app.route("/workitem/history/<string:workitemId>/field/<string:field>")
def route_workitemFeieldHistory(workitemId, field):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    zipped = thisWorkitemAdapter.Get_Workitem_Field_History(workitemID=workitemId, field=field, fromDate=None, toDate=None, embeddedReturn=None)
    dateList, fieldList = zip(*zipped)
    return({
        "Dates": dateList,
        "Values": fieldList,
        "Combined": zipped
    })

@app.route("/workitem/<string:workitemId>/changedBy/<string:employee>")
def route_workitemFeildHistory(workitemId, employee):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Is_Workitem_ChangedBy(workitemID=workitemId, employee=employee, fromDate=None, toDate=None)
    })

@app.route("/projects")
def route_projects():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Projects()
    })

@app.route("/features")
def route_features():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Features()
    })

@app.route("/sprints/<string:scope>")
def route_sprints(scope):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Sprints(inputScope=scope)
    })

@app.route("/boards")
def route_boards():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Board_or_Teams()
    })

@app.route("/employees")
def route_employees():
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Employees()
    })

@app.route("/employee/<string:employee>")
def route_employeeContributions(employee):
    thisWorkitemAdapter = WorkitemAdapter(
        ExternalWorkitemInterface.ADO,
        os.getenv("ado_username"),
        os.getenv("ado_pat"),
        os.getenv("ado_org"),
        os.getenv("ado_project")
    )
    return({
        "Values": thisWorkitemAdapter.Get_Employee_Contributions(employee, fromDate=None, toDate=None)
    })

if __name__ == "__main__":
    app.run()