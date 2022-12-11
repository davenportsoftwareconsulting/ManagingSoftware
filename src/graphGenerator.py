from workitemAdapter import WorkitemAdapter, ExternalWorkitemInterface
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import datetime
import seaborn as sns
import numpy as np

class GraphGenerator:

    def __init__(self, workitemAdapter: WorkitemAdapter) -> None:
        self.workitemAdapter = workitemAdapter

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
        x = []
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
        plt.show()