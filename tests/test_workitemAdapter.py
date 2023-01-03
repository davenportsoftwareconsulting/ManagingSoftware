import unittest
from unittest.mock import patch, PropertyMock
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
        self.workitemAdapters = {}
        self.currentMockData = None
        basePath = os.getcwd() if 'tests' in os.getcwd() else f"{os.getcwd()}\\tests"

        try:
            jiraWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.JIRA, username=os.getenv('jira_username'),
                password=os.getenv('jira_PAT'), organization=os.getenv('jira_org')
            )
            with open(f'{basePath}\\jira_workitem_data.json', 'r') as jsonFile:
                jiraMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_relation_workitem_data.json', 'r') as jsonFile:
                jiraRelationMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_history_workitem_data.json', 'r') as jsonFile:
                jiraHistoryMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_project_data.json', 'r') as jsonFile:
                jiraProjectMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_feature_data.json', 'r') as jsonFile:
                jiraFeatureMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_sprints_data.json', 'r') as jsonFile:
                jiraSprintsMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\jira_boards_data.json', 'r') as jsonFile:
                jiraBoardMockData = json.loads(jsonFile.read())
            self.workitemAdapters['JIRA'] = {
                "Adapter": jiraWorkitemAdapter,
                "Workitem Mock": jiraMockData, "Workitem Relation Mock": jiraRelationMockData,
                "Workitem History Mock": jiraHistoryMockData, "Project Mock": jiraProjectMockData,
                "Feature Mock": jiraFeatureMockData, "Sprints Mock": jiraSprintsMockData,
                "Group Mock": jiraBoardMockData
            }
        except Exception as e:
            print(f"Jira workitem adapter not configured\n{e}")

        try:
            adoWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.ADO, username=os.getenv('ado_username'),
                password=os.getenv('ado_PAT'), organization=os.getenv('ado_org'), project=os.getenv('ado_project')
            )
            with open(f'{basePath}\\ado_workitem_data.json', 'r') as jsonFile:
                adoMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\ado_relation_workitem_data.json', 'r') as jsonFile:
                adoRelationMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\ado_history_workitem_data.json', 'r') as jsonFile:
                adoHistoryMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\ado_feature_data.json', 'r') as jsonFile:
                adoFeatureMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\ado_sprints_data.json', 'r') as jsonFile:
                adoSprintsMockData = json.loads(jsonFile.read())
            with open(f'{basePath}\\ado_teams_data.json', 'r') as jsonFile:
                adoTeamsMockData = json.loads(jsonFile.read())
            self.workitemAdapters["ADO"] = {
                "Adapter": adoWorkitemAdapter,
                "Workitem Mock": adoMockData, "Workitem Relation Mock": adoRelationMockData,
                "Workitem History Mock": adoHistoryMockData, "Project Mock": [adoWorkitemAdapter.project],
                "Feature Mock": adoFeatureMockData, "Sprints Mock": adoSprintsMockData,
                "Group Mock": adoTeamsMockData
            }
        except Exception as e:
            print(f"ADO workitem adapter not configured\n{e}")

        if len(self.workitemAdapters) == 0:
            raise ValueError("ADO or Jira variables must fully be present in OS environment variables. Please refer to README for more details")
        
    def test_connection_test(self):
        for workitemAdapter in self.workitemAdapters:
            result = self.workitemAdapters[workitemAdapter]['Adapter'].connection_test()
            self.assertEqual(result, True)

    def test_Str_To_Datetime(self):
        for workitemAdapter in self.workitemAdapters:
            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01/01/2022")
            self.assertEqual(result, datetime(year=2022, month=1, day=1))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01/01/2022")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=1))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01/01/2022 12:45:20")
            self.assertEqual(result, datetime(year=2022, month=1, day=1, hour=12, minute=45, second=20))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01/01/2022 12:45:20")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=1, hour=13))
            
            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01/01/2022T01:30:54")
            self.assertEqual(result, datetime(year=2022, month=1, day=1, hour=1, minute=30, second=54))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-01-02")
            self.assertEqual(result, datetime(year=2022, month=1, day=2))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-01-02")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=2))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-01-02 12:45:20")
            self.assertEqual(result, datetime(year=2022, month=1, day=2, hour=12, minute=45, second=20))

            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-01-02 12:45:20")
            self.assertNotEqual(result, datetime(year=2022, month=2, day=2, hour=13))
            
            result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-01-02T01:30:54")
            self.assertEqual(result, datetime(year=2022, month=1, day=2, hour=1, minute=30, second=54))

            with self.assertRaises(ValueError):
                result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("01-01-2022")

            with self.assertRaises(ValueError):
                result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("2022-13-01")

            with self.assertRaises(ValueError):
                result = self.workitemAdapters[workitemAdapter]['Adapter'].Str_To_Datetime("*1-mm-2022")

    def test_Get_Workitem_Response(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Response('1')
                self.assertTrue('fields' in response)

    def test_Get_Workitem_Fields(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Fields('1')
                self.assertTrue('issuetype' in response or 'System.State' in response)

    def test_Get_Workitem_Associations(self):
        for workitemAdapter in self.workitemAdapters:
            self.currentMockData = self.workitemAdapters[workitemAdapter]['Workitem Mock']
            self.currentRelationMockData = self.workitemAdapters[workitemAdapter]['Workitem Relation Mock']
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Associations('1')
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
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Title('1')
                self.assertTrue(
                    response == "MVP: Static Config and External Adapters" or
                    response == "ADO Integration"
                )

    def test_Get_Workitem_State(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_State('1')
                self.assertTrue(
                    response == "New" or
                    response == "Done"
                )

    def test_Get_Workitem_Description(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Description('1')
                self.assertTrue(
                    "<div>For MVP, we want the ability" in response or
                    "Integrate ADO with tool" in response
                )

    def test_Get_Workitem_Assignee(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Assignee('1')
                self.assertTrue(response == "Connor Davenport")
                
    def test_Get_Workitem_Created_Date(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Created_Date('1')
                self.assertTrue(
                    (response - datetime(year=2022, month=11, day=26, hour=14, minute=16, second=22)).seconds < 2 or 
                    (response - datetime(year=2022, month=11, day=26, hour=19, minute=2, second=44)).seconds < 2
                )

    def test_Get_Workitem_Field_History(self):
        for workitemAdapter in self.workitemAdapters:
            self.currentMockData = self.workitemAdapters[workitemAdapter]['Workitem Mock']
            self.currentRelationMockData = self.workitemAdapters[workitemAdapter]['Workitem Relation Mock']
            self.currentHistoryMockData = self.workitemAdapters[workitemAdapter]['Workitem History Mock']
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                with patch.object(WorkitemAdapter, "fieldList", new_callable=PropertyMock) as objectPatch:
                    objectPatch.return_value = ["System.State"]
                    response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Field_History('1', "System.State")
                    self.assertTrue(
                        isinstance(response, list) and
                        len(response) > 0 and
                        isinstance(response[0], tuple) and
                        isinstance(response[0][0], datetime)
                    )

    def test_Get_Projects(self):
        for workitemAdapter in self.workitemAdapters:
            self.currentProjectMockData = self.workitemAdapters[workitemAdapter]['Project Mock']
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Projects()
                self.assertTrue(
                    isinstance(response, list) and
                    len(response) > 0 and
                    isinstance(response[0], str)
                )

    def test_Get_Features(self):
        for workitemAdapter in self.workitemAdapters:
            self.currentFeatureMockData = self.workitemAdapters[workitemAdapter]['Feature Mock']
            with patch('src.workitemAdapter.requests.get', side_effect=self.request_side_effect) as mock_get:
                with patch('src.workitemAdapter.requests.post') as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Feature Mock']
                    response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Features()
                    self.assertTrue(
                        isinstance(response, list) and
                        isinstance(response[0], str)
                    )

    def test_Get_Workitem_Sprint(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Workitem Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Workitem_Sprint('1')
                self.assertTrue(
                    isinstance(response, str) and 
                    (response == "Sprint 1" or response == "SAN Sprint 1")
                )

    def test_Get_Sprints(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Sprints Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Sprints('1')
                self.assertTrue(
                    isinstance(response, dict) and 
                    isinstance(response[list(response.keys())[0]]['Start'], datetime)
                )

    def test_Get_Board_or_Teams(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter in self.workitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = self.workitemAdapters[workitemAdapter]['Group Mock']
                response = self.workitemAdapters[workitemAdapter]['Adapter'].Get_Board_or_Teams()
                self.assertTrue(
                    isinstance(response, list) and 
                    isinstance(response[0], tuple) and
                    (response[0][0] == "SAN board" or response[0][0] == "Davenport software consulting Team")
                )

if __name__ == "__main__":
    unittest.main()