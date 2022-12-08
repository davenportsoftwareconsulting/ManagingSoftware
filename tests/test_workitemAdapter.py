import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
from datetime import datetime
sys.path.append('..')
from src.workitemAdapter import ExternalWorkitemInterface, WorkitemAdapter

class TestWorkitemAdapter(unittest.TestCase):

    def setUp(self) -> None:
        self.listOfWorkitemAdapters = []

        try:
            jiraWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.JIRA, username=os.getenv('jira_username'),
                password=os.getenv('jira_PAT'), organization=os.getenv('jira_org')
            )
            with open('ado_workitem_data.json', 'r') as jsonFile:
                mockData = json.loads(jsonFile.read())
            self.listOfWorkitemAdapters.append((jiraWorkitemAdapter, mockData))
        except Exception as e:
            print(f"Jira workitem adapter not configured\n{e}")

        try:
            adoWorkitemAdapter = WorkitemAdapter(
                connectionType=ExternalWorkitemInterface.ADO, username=os.getenv('ado_username'),
                password=os.getenv('ado_PAT'), organization=os.getenv('ado_org'), project=os.getenv('ado_project')
            )
            with open('jira_workitem_data.json', 'r') as jsonFile:
                mockData = json.loads(jsonFile.read())
            self.listOfWorkitemAdapters.append((adoWorkitemAdapter, mockData))
        except Exception as e:
            print(f"ADO workitem adapter not configured\n{e}")

        if len(self.listOfWorkitemAdapters) == 0:
            raise ValueError("ADO or Jira variables must fully be present in OS environment variables. Please refer to README for more details")
        
    def test_connection_test(self):
        for workitemAdapter, mockData in self.listOfWorkitemAdapters:
            result = workitemAdapter.connection_test()
            self.assertEqual(result, True)

    def test_Str_To_Datetime(self):
        for workitemAdapter, mockData in self.listOfWorkitemAdapters:
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
            for workitemAdapter, mockData in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Response('1')
                self.assertTrue('fields' in response)

    def test_Get_Workitem_Fields(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Fields('1')
                self.assertTrue('issuetype' in response or 'System.State' in response)
                
    def test_Get_Workitem_Fields(self):
        with patch('src.workitemAdapter.requests.get') as mock_get:
            for workitemAdapter, mockData in self.listOfWorkitemAdapters:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mockData
                response = workitemAdapter.Get_Workitem_Fields('1')
                self.assertTrue('issuetype' in response or 'System.State' in response)
            
if __name__ == "__main__":
    unittest.main()