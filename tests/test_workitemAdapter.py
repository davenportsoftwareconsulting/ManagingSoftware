import unittest
from unittest.mock import Mock, patch, PropertyMock
import sys
import os
import json
from datetime import datetime
sys.path.append('..')
from src.workitemAdapter import ExternalWorkitemInterface, WorkitemAdapter

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

class TestWorkitemAdapter(unittest.TestCase):

    def setUp(self) -> None:
        self.listOfWorkitemAdapters = []
        self.currentMockData = None

        try:
            jiraWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.JIRA, username=os.getenv('jira_username'),
                password=os.getenv('jira_PAT'), organization=os.getenv('jira_org')
            )
            with open('jira_workitem_data.json', 'r') as jsonFile:
                jiraMockData = json.loads(jsonFile.read())
            with open('jira_relation_workitem_data.json', 'r') as jsonFile:
                jiraRelationMockData = json.loads(jsonFile.read())
            with open('jira_history_workitem_data.json', 'r') as jsonFile:
                jiraHistoryMockData = json.loads(jsonFile.read())
            with open('jira_project_data.json', 'r') as jsonFile:
                jiraProjectMockData = json.loads(jsonFile.read())
            with open('jira_feature_data.json', 'r') as jsonFile:
                jiraFeatureMockData = json.loads(jsonFile.read())
            self.listOfWorkitemAdapters.append((jiraWorkitemAdapter, jiraMockData, jiraRelationMockData, jiraHistoryMockData, jiraProjectMockData, jiraFeatureMockData))
        except Exception as e:
            print(f"Jira workitem adapter not configured\n{e}")

        try:
            adoWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.ADO, username=os.getenv('ado_username'),
                password=os.getenv('ado_PAT'), organization=os.getenv('ado_org'), project=os.getenv('ado_project')
            )
            with open('ado_workitem_data.json', 'r') as jsonFile:
                adoMockData = json.loads(jsonFile.read())
            with open('ado_relation_workitem_data.json', 'r') as jsonFile:
                adoRelationMockData = json.loads(jsonFile.read())
            with open('ado_history_workitem_data.json', 'r') as jsonFile:
                adoHistoryMockData = json.loads(jsonFile.read())
            with open('ado_feature_data.json', 'r') as jsonFile:
                adoFeatureMockData = json.loads(jsonFile.read())
            self.listOfWorkitemAdapters.append((adoWorkitemAdapter, adoMockData, adoRelationMockData, adoHistoryMockData, [adoWorkitemAdapter.project], adoFeatureMockData))
        except Exception as e:
            print(f"ADO workitem adapter not configured\n{e}")

        if len(self.listOfWorkitemAdapters) == 0:
            raise ValueError("ADO or Jira variables must fully be present in OS environment variables. Please refer to README for more details")
        
    def test_connection_test(self):
        for workitemAdapter, *_ in self.listOfWorkitemAdapters:
            result = workitemAdapter.connection_test()
            self.assertEqual(result, True)

    def test_Str_To_Datetime(self):
        for workitemAdapter, *_ in self.listOfWorkitemAdapters:
            result = workitemAdapter.Str_To_Datetime("01/01/2022")
            self.assertEqual(result, datetime(year=2022, month=1, day=1))

            result = workitemAdapter.Str_To_Datetime("01/01/2022")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=1))

            result = workitemAdapter.Str_To_Datetime("01/01/2022 12:45:20")
            self.assertEqual(result, datetime(year=2022, month=1, day=1, hour=12, minute=45, second=20))

            result = workitemAdapter.Str_To_Datetime("01/01/2022 12:45:20")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=1, hour=13))
            
            result = workitemAdapter.Str_To_Datetime("01/01/2022T01:30:54")
            self.assertEqual(result, datetime(year=2022, month=1, day=1, hour=1, minute=30, second=54))

            result = workitemAdapter.Str_To_Datetime("2022-01-02")
            self.assertEqual(result, datetime(year=2022, month=1, day=2))

            result = workitemAdapter.Str_To_Datetime("2022-01-02")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=2))

            result = workitemAdapter.Str_To_Datetime("2022-01-02 12:45:20")
            self.assertEqual(result, datetime(year=2022, month=1, day=2, hour=12, minute=45, second=20))

            result = workitemAdapter.Str_To_Datetime("2022-01-02 12:45:20")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=2, hour=13))
            
            result = workitemAdapter.Str_To_Datetime("2022-01-02T01:30:54")
            self.assertEqual(result, datetime(year=2022, month=1, day=2, hour=1, minute=30, second=54))

            with self.assertRaises(ValueError):
                result = workitemAdapter.Str_To_Datetime("01-01-2022")

            with self.assertRaises(ValueError):
                result = workitemAdapter.Str_To_Datetime("2022-13-01")

            with self.assertRaises(ValueError):
                result = workitemAdapter.Str_To_Datetime("*1-mm-2022")

    def test_Get_Workitem_Response(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Response('1')
                self.assertTrue('fields' in response)

    def test_Get_Workitem_Fields(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Fields('1')
                self.assertTrue('issuetype' in response or 'System.State' in response)

    def test_Get_Workitem_Associations(self):
        for workitemAdapter, mockData, relationMockData, *_ in self.listOfWorkitemAdapters:
            self.currentMockData = mockData
            self.currentRelationMockData = relationMockData
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                response = workitemAdapter.Get_Workitem_Associations('1')
                self.assertTrue('Parent' in response) # TODO: Allow this to test for other relationships as well, but would need to pass more data for relationMockData specifically for Jira to do this
            
    def request_side_effect(self, *args, **kwargs):
        if 'expand=relations' in args[0]:
            return MockResponse(
                self.currentRelationMockData, 200
            )
        elif '/updates' in args[0] or '?expand=changelog' in args[0]:
            return MockResponse(
                self.currentHistoryMockData, 200
            )
        elif '/project' in args[0]:
            return MockResponse(
                self.currentProjectMockData, 200
            )
        elif "jql=issuetype=Feature" in args[0]:
            return MockResponse(
                self.currentFeatureMockData, 200
            )
        elif 'jql=' in args[0]:
            return MockResponse(
                {
                    "issues": [
                        {
                            "key": "SAN-5"
                        },
                        {
                            "key": "SAN-6"
                        }
                    ]
                }, 200)
        else:
            return MockResponse(
                self.currentMockData, 200
            )

    def test_Get_Workitem_Title(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Title('1')
                self.assertTrue(
                    response == "MVP: Static Config and External Adapters" or
                    response == "ADO Integration"
                )

    def test_Get_Workitem_State(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_State('1')
                self.assertTrue(
                    response == "New" or
                    response == "Done"
                )

    def test_Get_Workitem_Description(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Description('1')
                self.assertTrue(
                    "<div>For MVP, we want the ability" in response or
                    "Integrate ADO with tool" in response
                )

    def test_Get_Workitem_Assignee(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Assignee('1')
                self.assertTrue(response == "Connor Davenport")
                
    def test_Get_Workitem_Created_Date(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData, *_ in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Created_Date('1')
                self.assertTrue(
                    (response - datetime(year=2022, month=11, day=26, hour=14, minute=16, second=22)).seconds < 2 or 
                    (response - datetime(year=2022, month=11, day=26, hour=19, minute=2, second=44)).seconds < 2
                )

    def test_Get_Workitem_Field_History(self):
        for workitemAdapter, mockData, referenceMockData, historyMockData, *_ in self.listOfWorkitemAdapters:
            self.currentMockData = mockData
            self.currentRelationMockData = referenceMockData
            self.currentHistoryMockData = historyMockData
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                with patch.object(WorkitemAdapter, "fieldList", new_callable=PropertyMock) as objectPatch:
                    objectPatch.return_value = ["System.State"]
                    response = workitemAdapter.Get_Workitem_Field_History('1', "System.State")
                    self.assertTrue(
                        isinstance(response, list) and
                        len(response) > 0 and
                        isinstance(response[0], tuple) and
                        isinstance(response[0][0], datetime)
                    )

    def test_Get_Projects(self):
        for workitemAdapter, *_, projectMockData, _ in self.listOfWorkitemAdapters:
            self.currentProjectMockData = projectMockData
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                response = workitemAdapter.Get_Projects()
                self.assertTrue(
                    isinstance(response, list) and
                    len(response) > 0 and
                    isinstance(response[0], str)
                )

    def test_Get_Features(self):
        for workitemAdapter, *_, featureMockData in self.listOfWorkitemAdapters:
            self.currentFeatureMockData = featureMockData
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                with patch('src.workitemAdapter.requests.post') as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = featureMockData
                    response = workitemAdapter.Get_Features()
                    self.assertTrue(
                        isinstance(response, list) and
                        isinstance(response[0], str)
                    )

if __name__ == "__main__":
    unittest.main()