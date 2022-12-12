from enum import Enum
import requests
import time
from datetime import datetime

class ExternalRepoInterface(Enum):
    BITBUCKET = 0
    ADO = 1
    GITHUB = 2


class repoAdapter:

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

    def Get_Repos(self):
        repoList = []
        if self.connectionType == ExternalRepoInterface.BITBUCKET:
            url = f"{self.baseURL}/repositories/{self.organization}"
            repoListResponse = self.__genericRequest(url)['values']
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
            commitsResponse = self.__genericRequest(url)
            for commit in commitsResponse['values']:
                commitCommitterName = commit['author']['user']['display_name'].lower()
                commitCommitterRaw = commit['author']['raw']
                commitCommitterEmail = commitCommitterRaw[commitCommitterRaw.find('<') + 1:commitCommitterRaw.find('>')]
                commitDate = self.Str_To_Datetime(commit['date'])
                if (not fromDate or commitDate > fromDate) and (not toDate or commitDate < toDate) and\
                (not committerName or committerName == commitCommitterName) and (not committerEmail or commitCommitterEmail == committerEmail):
                    commitList.append((commit['hash'], commitCommitterName, commitDate))

        return commitList