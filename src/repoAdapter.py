from enum import Enum
import requests
import time
from datetime import datetime
from flask import Flask, request
import json
import argparse

app = Flask(__name__)

badRequestReturn = {
    "Status": 400,
    "Message": "Parameters passed cannot authenticate to work item tracking application"
}

class ExternalRepoInterface(Enum):
    BITBUCKET = 0
    ADO = 1
    GITHUB = 2

class TimeGranularity(Enum):
    SECOND = 5
    MINUTE = 4
    HOUR = 3
    DAY = 2
    MONTH = 1
    YEAR = 0

class RepoAdapter:

    def __init__(self, connectionType: ExternalRepoInterface, username: str, password: str, organization: str, project: str) -> None:
        self.connectionType = connectionType
        self.organization = organization
        self.project = project

        if connectionType == ExternalRepoInterface.BITBUCKET:
            self.baseURL = "https://api.bitbucket.org/2.0"
            self.credentials = (username, password)
            self.requestContentType = "application/json-patch+json"
        elif connectionType == ExternalRepoInterface.ADO:
            self.baseURL = f"https://dev.azure.com/{organization}/{project}/_apis"
            self.credentials = ('',password)
            self.requestContentType = "application/json-patch+json"
        elif connectionType == ExternalRepoInterface.GITHUB:
            self.baseURL = f"https://api.github.com"
            self.credentials = ('',password)
            self.requestContentType = "application/json-patch+json"

    def __genericRequest(self, url: str, noCredentials = False):
        goodValue = False
        for i in range(0, 3):

            r = requests.get(url,
                headers={'Content-Type': self.requestContentType},
                auth=None if noCredentials else self.credentials)

            if r.status_code == 200:
                goodValue = True
                break

            print(f"Unable to process: {url} trying again")
            if i != 2:
                time.sleep(5 + (5 * i))

        if not goodValue:
            return None

        return r.json()

    def __number_compare(self, num1: int, num2: int):
        if num1 > num2:
            return 1
        elif num2 > num1:
            return -1
        else:
            return 0

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

    def Connection_Test(self):
        return True # TODO: Actually build out the test

    def Get_Repos(self):
        repoList = []
        if self.connectionType == ExternalRepoInterface.BITBUCKET:
            url = f"{self.baseURL}/repositories/{self.organization}"
            repoListResponse = self.__genericRequest(url, noCredentials=True)['values']
            for repo in repoListResponse:
                repoList.append(repo['name'])
        elif self.connectionType == ExternalRepoInterface.ADO:
            url = f"{self.baseURL}/git/repositories"
            repoListResponse = self.__genericRequest(url)['value']
            for repo in repoListResponse:
                repoList.append(repo['name'])
        elif self.connectionType == ExternalRepoInterface.GITHUB:
            url = f"{self.baseURL}/user/repos"
            repoListResponse = self.__genericRequest(url)
            for repo in repoListResponse:
                repoList.append(repo['name'])

        return repoList

    def Get_Repo_Commits(self, repo: str, fromDate: datetime = None, toDate: datetime = None, committerName: str = None, committerEmail: str = None) -> list:
        commitList = []
        committerName = committerName.lower() if committerName else None
        committerEmail = committerEmail.lower() if committerEmail else None
        if self.connectionType == ExternalRepoInterface.GITHUB:
            url = f"{self.baseURL}/repos/{self.organization}/{repo}/commits"
            commitsResponse = self.__genericRequest(url)
            for commit in commitsResponse:
                commitCommitterName = commit['commit']['committer']['name'].lower()
                commitCommitterEmail = commit['commit']['committer']['email'].lower()
                commitDate = self.Str_To_Datetime(commit['commit']['committer']['date'])
                if (not fromDate or commitDate > fromDate) and (not toDate or commitDate < toDate) and\
                (not committerName or committerName == commitCommitterName) and (not committerEmail or commitCommitterEmail == committerEmail):
                    commitList.append((commit['sha'], commitCommitterName, commitDate))
        elif self.connectionType == ExternalRepoInterface.ADO:
            url = f"{self.baseURL}/git/repositories/{repo}/commits"
            commitsResponse = self.__genericRequest(url)
            for commit in commitsResponse['value']:
                commitCommitterName = commit['committer']['name'].lower()
                commitCommitterEmail = commit['committer']['email'].lower()
                commitDate = self.Str_To_Datetime(commit['committer']['date'])
                if (not fromDate or commitDate > fromDate) and (not toDate or commitDate < toDate) and\
                (not committerName or committerName == commitCommitterName) and (not committerEmail or commitCommitterEmail == committerEmail):
                    commitList.append((commit['commitId'], commitCommitterName, commitDate))
        elif self.connectionType == ExternalRepoInterface.BITBUCKET:
            url = f"{self.baseURL}/repositories/{self.organization}/{repo}/commits"
            commitsResponse = self.__genericRequest(url, noCredentials=True)
            for commit in commitsResponse['values']:
                commitCommitterName = commit['author']['user']['display_name'].lower()
                commitCommitterRaw = commit['author']['raw']
                commitCommitterEmail = commitCommitterRaw[commitCommitterRaw.find('<') + 1:commitCommitterRaw.find('>')]
                commitDate = self.Str_To_Datetime(commit['date'])
                if (not fromDate or commitDate > fromDate) and (not toDate or commitDate < toDate) and\
                (not committerName or committerName == commitCommitterName) and (not committerEmail or commitCommitterEmail == committerEmail):
                    commitList.append((commit['hash'], commitCommitterName, commitDate))

        commitList = commitList[::-1]

        return commitList

def initialize(request) -> RepoAdapter:
    requestData = request.data
    if not len(requestData) == 0:
        requestData = json.loads(request.data.decode())
    else:
        requestData = request.form
    return RepoAdapter(
        ExternalRepoInterface.ADO,
        requestData['username'],
        requestData['pat'],
        requestData['org'],
        requestData['project']
    )

@app.route("/init", methods=['GET'])
def route_init():
    thisRepoAdapter = initialize(request)
    if not thisRepoAdapter:
        return(badRequestReturn)

    return({
        "Base URL": thisRepoAdapter.baseURL,
        "Credentials": thisRepoAdapter.credentials,
        "Request Content Type": thisRepoAdapter.requestContentType,
        "Status": 200
    })

@app.route("/test", methods=['GET'])
def route_test():
    thisRepoAdapter = initialize(request)
    if not thisRepoAdapter:
        return(badRequestReturn)

    return({
        "Result": thisRepoAdapter.Connection_Test(),
        "Status": 200
    })

@app.route("/repos", methods=['GET'])
def route_getRepos():
    thisRepoAdapter = initialize(request)
    if not thisRepoAdapter:
        return(badRequestReturn)

    return({
        "Values": thisRepoAdapter.Get_Repos(),
        "Status": 200
    })

@app.route("/repo/commits/<string:repoName>", methods=['GET'])
def route_getRepoCommits(repoName):
    print(repoName)
    thisRepoAdapter = initialize(request)
    if not thisRepoAdapter:
        return(badRequestReturn)

    return({
        "Values": thisRepoAdapter.Get_Repo_Commits(repo=repoName, fromDate=None, toDate=None, committerName=None, committerEmail=None),
        "Status": 200
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="userOpt_port", action="store", default="5001")
    args = parser.parse_args()
    print(args.userOpt_port)
    app.run(host='0.0.0.0', port=int(args.userOpt_port))
