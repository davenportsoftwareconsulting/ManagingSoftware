from enum import Enum
import os
import requests
import time
from datetime import datetime, timedelta

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

    def __init__(self, connectionType: ExternalWorkitemInterface, username: str, password: str, organization: str, project: str = None) -> None:
        self.connectionType = connectionType
        self.username = username
        self.password = password
        self.organization = organization
        self.project = project
        self.fieldList = []

        if self.connectionType == ExternalWorkitemInterface.ADO:
            self.baseURL = f"https://dev.azure.com/{organization}/{project}/_apis"
            self.baseWorkitemURL = f"{self.baseURL}/wit/workitems"
            self.testURL = f"{self.baseURL}/wit/fields"
            self.credentials = ('',self.password)
            self.requestContentType = "application/json-patch+json"
            self.postContentType = "application/json"
            for fieldEntry in self.__genericRequest(f"{self.baseURL}/wit/fields")['value']:
                self.fieldList.append(fieldEntry['referenceName'])

        if self.connectionType == ExternalWorkitemInterface.JIRA:
            self.baseURL = f"https://{organization}.atlassian.net/rest/api"
            self.baseWorkitemURL = f"{self.baseURL}/2/issue"
            self.testURL = f"{self.baseURL}/2/permissions"
            self.credentials = (self.username, self.password)
            self.requestContentType = "application/json"
            self.postContentType = "application/json"
            for fieldEntry in self.__genericRequest(f"{self.baseURL}/latest/field"):
                self.fieldList.append(fieldEntry['key'])

    def test(self):
        testResponse = self.__genericRequest(self.testURL)
        if testResponse:
            print("pass")
            return True
        else:
            print("fail")
            return

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

        if goodValue:
            return r.json()
        else:
            return None

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

        if goodValue:
            return r.json()
        else:
            return None

    def Str_To_Datetime(self, dateString: str) -> datetime:
        inputFormat = "%Y-%m-%d %H:%M:%S"
        dateString = dateString.replace('T', ' ')
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

    def __compare_dates(self, day1: datetime, day2: datetime, granularity: TimeGranularity = TimeGranularity.DAY):
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

            jqlChildrenSearchResponse = self.__genericRequest(f"{self.baseURL}/2/search?jql=%22Parent%22=%22{workitemID}%22")
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
        if self.connectionType == ExternalWorkitemInterface.JIRA:
            historyURL = f"{self.baseWorkitemURL}/{workitemID}?expand=changelog"
            historyList = self.__genericRequest(historyURL)['changelog']['histories']
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
            historyURL = f"{self.baseWorkitemURL}/{workitemID}/updates"
            historyList = self.__genericRequest(historyURL)['value']
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
                if self.__compare_dates(fromDate, fieldChange['Date']) in [0, -1]:
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

            if self.__compare_dates(fieldChanges[fieldChangIndex]['Date'], currentDay) == 0:
                while fieldChangIndex + 1 < len(fieldChanges) and self.__compare_dates(fieldChanges[fieldChangIndex + 1]['Date'], currentDay) == 0:
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