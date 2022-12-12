import unittest
import sys
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch, PropertyMock
sys.path.append('..')
from src.repoAdapter import ExternalRepoInterface, RepoAdapter

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

class TestRepoAdapter(unittest.TestCase):
    repoAdapters = {}
    def setUp(self) -> None:
        bitbucketAdapter = RepoAdapter(
            connectionType=ExternalRepoInterface.BITBUCKET,
            username=None, password=os.getenv('bitbucket_PAT') if os.getenv('bitbucket_PAT') else os.getenv('jira_PAT'),
            organization=os.getenv('bitbucket_org') if os.getenv('bitbucket_org') else os.getenv('jira_org'), 
            project=os.getenv('bitbucket_project') if os.getenv('bitbucket_project') else os.getenv('jira_project') 
        )
        self.repoAdapters['BITBUCKET'] = {
            'Adapter': bitbucketAdapter
        }
        with open("bitbucket_repos_data.json", 'r') as jsonFile:
            self.repoAdapters['BITBUCKET']['Repo List Mock'] = json.loads(jsonFile.read())
        with open("bitbucket_repo_commits_data.json", 'r') as jsonFile:
            self.repoAdapters['BITBUCKET']['Repo Commits Mock'] = json.loads(jsonFile.read())
        
        githubAdapter = RepoAdapter(
            connectionType=ExternalRepoInterface.GITHUB,
            username=None, password=os.getenv('github_PAT'),
            organization=os.getenv('github_org'), project=None
        )
        self.repoAdapters['GITHUB'] = {
            'Adapter': githubAdapter
        }
        with open("github_repos_data.json", 'r') as jsonFile:
            self.repoAdapters['GITHUB']['Repo List Mock'] = json.loads(jsonFile.read())
        with open("github_repo_commits_data.json", 'r') as jsonFile:
            self.repoAdapters['GITHUB']['Repo Commits Mock'] = json.loads(jsonFile.read())
        
        adoAdapter = RepoAdapter(
            connectionType=ExternalRepoInterface.ADO,
            username=os.getenv('ado_username'), password=os.getenv('ado_PAT'),
            organization=os.getenv('ado_org'), project=os.getenv('ado_project')
        )
        self.repoAdapters['ADO'] = {
            'Adapter': adoAdapter
        }
        with open("ado_repos_data.json", 'r') as jsonFile:
            self.repoAdapters['ADO']['Repo List Mock'] = json.loads(jsonFile.read())
        with open("ado_repo_commits_data.json", 'r') as jsonFile:
            self.repoAdapters['ADO']['Repo Commits Mock'] = json.loads(jsonFile.read())

    def test_Get_Repos(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for repoAdapter in self.repoAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.repoAdapters[repoAdapter]['Repo List Mock']
                response = self.repoAdapters[repoAdapter]['Adapter'].Get_Repos()
                self.assertTrue(
                    isinstance(response, list) and isinstance(response[0], str) and
                    'ManagingSoftware' in response
                )

    def test_Get_Repo_Commits(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for repoAdapter in self.repoAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.repoAdapters[repoAdapter]['Repo Commits Mock']
                fullResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits('test')
                fromOnlyDateResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits(
                    'test',
                    fromDate=datetime(year=2022, month=12, day=8))
                dateConstrainedResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits(
                    'test',
                    fromDate=datetime(year=2022, month=12, day=8),
                    toDate=datetime(year=2022, month=12, day=11)
                )
                goodNameLimitResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits('test', committerName="Connor Davenport")
                badNameLimitResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits('test', committerName="John Smith")
                goodEmailLimitResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits('test', committerEmail="connor.davenport92@gmail.com")
                badEmailLimitResponse = self.repoAdapters[repoAdapter]['Adapter'].Get_Repo_Commits('test', committerEmail="johnsmith@hotmail.com")
                self.assertTrue(
                    isinstance(fullResponse, list) and isinstance(fullResponse[0], tuple) and
                    isinstance(fullResponse[0][0], str) and isinstance(fullResponse[0][1], str) and isinstance(fullResponse[0][2], datetime)
                )
                self.assertTrue(len(fullResponse) > len(fromOnlyDateResponse))
                self.assertTrue(len(fromOnlyDateResponse) > len(dateConstrainedResponse))
                self.assertTrue(len(fullResponse) == len(goodNameLimitResponse))
                self.assertTrue(len(fullResponse) == len(goodEmailLimitResponse))
                self.assertTrue(len(fullResponse) != len(badNameLimitResponse))
                self.assertTrue(len(fullResponse) != len(badEmailLimitResponse))


if __name__ == "__main__":
    unittest.main()