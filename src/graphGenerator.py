from workitemAdapter import WorkitemAdapter, ExternalWorkitemInterface
from repoAdapter import RepoAdapter, ExternalRepoInterface
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import datetime, timedelta
import seaborn as sns
import numpy as np

class GraphGenerator:

    def __init__(self, workitemAdapter: WorkitemAdapter, repoAdapter: RepoAdapter) -> None:
        self.workitemAdapter = workitemAdapter
        self.repoAdapter = repoAdapter

    def Set_Workitem_Adapter(self, workitemAdapter: WorkitemAdapter) -> None:
        self.workitemAdapter = workitemAdapter

    def Set_Repo_Adapter(self, repoAdapter: RepoAdapter) -> None:
        self.repoAdapter = repoAdapter

    def Generate_State_Stacked_Area_Chart(self, featureID: str, fromDate: datetime = None, toDate: datetime = None, outputFileName: str = None) -> str:
        if not outputFileName:
            outputFileName = "current_feature_progress.jpg"
        
        adapterExteriorType = self.workitemAdapter.connectionType
        parentChildrenList = self.workitemAdapter.Get_Workitem_Associations(featureID)['Children']
        totalStateHistory = []
        if adapterExteriorType == ExternalWorkitemInterface.ADO:
            for child in parentChildrenList:
                totalStateHistory.append(self.workitemAdapter.Get_Workitem_Field_History(workitemID=child, field="System.State", fromDate=fromDate, toDate=toDate))
        elif adapterExteriorType == ExternalWorkitemInterface.JIRA:
            for child in parentChildrenList:
                totalStateHistory.append(self.workitemAdapter.Get_Workitem_Field_History(workitemID=child, field="status", fromDate=fromDate, toDate=toDate, embeddedReturn=["statusCategory", "name"]))
            # TODO: dynamically query state field and see which states this workitem can be assigned
            # TODO: check when a workitem is parented to the parent, instead of assuming all that are currently parented always were
        featureTitle = self.workitemAdapter.Get_Workitem_Title(featureID)

        uniqueStates = []
        flatState = {}
        displayX = []
        firstPass = True
        for childHistoryList in totalStateHistory:
            for date, state in childHistoryList:
                if state not in uniqueStates:
                    uniqueStates.append(state)
                    
                if totalStateHistory.index(childHistoryList) == 0 and firstPass:
                    displayX.append(date.strftime("%m/%d"))
            firstPass = False
                    
        for state in uniqueStates:
            flatState[state] = [0] * len(displayX)
        
        for childHistoryList in totalStateHistory:
            for index, (date, state) in enumerate(childHistoryList):
                flatState[state][index] += 1

        tuplePassthrough = ()
        maxCount = 0
        for state in flatState:
            tuplePassthrough += (flatState[state],)
            maxCount += max(flatState[state])

        labels = uniqueStates
        colors = sns.color_palette("RdBu", len(labels))

        plt.stackplot(displayX, *tuplePassthrough, labels=labels, colors=colors)
        plt.legend(loc="lower left")
        plt.title(f"{featureID}: {featureTitle}\nChildren Progress")
        plt.ylabel("Work Items")
        plt.yticks(np.arange(1, maxCount, 1.0))
        plt.savefig(outputFileName)
        plt.close()

    def Generate_Gantt_Chart(self, workitemID: str, sprintScope:str, outputFileName: str = None):
        if not outputFileName:
            outputFileName = "feature_gantt.jpg"

        sprints = self.workitemAdapter.Get_Sprints(sprintScope)
        sprintList = list(sprints.keys())
        x_pos = np.arange(len(sprints))

        workitemTitle = self.workitemAdapter.Get_Workitem_Title(workitemID)

        childList = []
        childWidths = []
        childLeft = []
        parentChildrenList = self.workitemAdapter.Get_Workitem_Associations(workitemID)['Children']
        for child in parentChildrenList:
            childList.append(child)
            childWidths.append(1)
            childLeft.append(sprintList.index(self.workitemAdapter.Get_Workitem_Sprint(child)))

        fig, ax = plt.subplots(1, figsize=(16,6))

        ax.barh(y=childList, width=childWidths, height=0.8, left=childLeft)
        
        ax.set_xticks(x_pos, tuple(sprintList))

        plt.title(f"{workitemID}: {workitemTitle}\nGantt Chart")
        plt.ylabel("Children")
        plt.savefig(outputFileName)
        plt.close()

    def Generate_Commit_Bar_Graph(self, repo: str, fromDate: datetime, toDate: datetime, outputFileName: str = None):
        outputFileName = "repo_commits.jpg" if not outputFileName else outputFileName

        if not toDate:
            toDate = datetime.now()
        
        commits = self.repoAdapter.Get_Repo_Commits(repo, fromDate, toDate)
        if not fromDate:
            fromDate = commits[0][2]
        numOfDays = (toDate - fromDate).days + 1
        x = []
        numberOfCommitsList = []
        for i in range(0,numOfDays):
            indexDate = fromDate + timedelta(days=i)
            x.append(indexDate.strftime("%m/%d"))
            numberOfCommits = 0

            for commit, author, date in commits:
                compareResult = self.repoAdapter.Compare_Dates(date, indexDate)
                if compareResult == 0:
                    numberOfCommits += 1
                elif compareResult == 1:
                    break

            numberOfCommitsList.append(numberOfCommits)

        plt.bar(x, numberOfCommitsList, width=.8, bottom = 0)
        plt.title(f"{repo}: Commit History")
        plt.ylabel("Commits")
        plt.savefig(outputFileName)
        plt.close()