import customtkinter
from workitemAdapter import ExternalWorkitemInterface, WorkitemAdapter
from repoAdapter import ExternalRepoInterface, RepoAdapter
import os
import operator
from PIL import Image, ImageTk
from graphGenerator import GraphGenerator


class desktopApplication:
    def __init__(self) -> None:
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")
        self.app = customtkinter.CTk()
        self.app.geometry('1200x800')
        self.app.title('Metrics Manager')

        self.workitemAdapter = None
        self.repoAdapter = None
        self.graphGenerator = GraphGenerator(None, None)

        self.usernameEntry = None
        self.passwordEntry = None
        self.organizationEntry = None
        self.projectEntry = None
        self.workitemConfigured = False
        self.repoConfigured = False

        self.frame = None
        self.workitemConfigFrame = None
        self.repoConfigFrame = None
        self.externalWorkitemInterface = ExternalWorkitemInterface.JIRA
        self.externalRepoInterface = ExternalRepoInterface.BITBUCKET
        self.externalworkitemListBox = None
        self.externalRepoListBox = None
        self.featureTestStatusLabel = None
        self.repoTestStatusLabel = None
        self.featureSelectButton = None
        self.repoSelectButton = None
        self.employeeSelectButton = None
        self.featureImageList = []
    
    def Get_External_Workitem_Interface(self) -> ExternalWorkitemInterface:
        return self.externalWorkitemInterface

    def __Set_External_Workitem_Interface(self, externalInterface: str):
        if externalInterface.lower() == "jira":
            self.externalWorkitemInterface = ExternalWorkitemInterface.JIRA
        elif externalInterface.lower() == "ado":
            self.externalWorkitemInterface = ExternalWorkitemInterface.ADO
        elif externalInterface.lower() == "workday":
            self.externalWorkitemInterface = ExternalWorkitemInterface.WORKDAY

        self.Show_Workitem_Config_Frame()

    def __Set_External_Repo_Interface(self, externalInterface: str):
        if externalInterface.lower() == "bitbucket":
            self.externalRepoInterface = ExternalRepoInterface.BITBUCKET
        elif externalInterface.lower() == "ado":
            self.externalRepoInterface = ExternalRepoInterface.ADO
        elif externalInterface.lower() == "github":
            self.externalRepoInterface = ExternalRepoInterface.GITHUB

        self.Show_Repo_Config_Frame()

    def __Gather_And_Remove_Config(self, workitemFrame = None, repoFrame = None):
        if workitemFrame:
            try:
                self.workitemAdapter = WorkitemAdapter(self.externalWorkitemInterface, self.usernameEntry.get(), self.passwordEntry.get(), self.organizationEntry.get(), self.projectEntry.get() if self.projectEntry else None)
                testPass = self.workitemAdapter.connection_test()
                self.graphGenerator.Set_Workitem_Adapter(self.workitemAdapter)
            except Exception as e:
                testPass = False
        elif repoFrame:
            try:
                self.repoAdapter = RepoAdapter(self.externalRepoInterface, self.usernameEntry.get(), self.passwordEntry.get(), self.organizationEntry.get(), self.projectEntry.get() if self.projectEntry else None)
                testPass = self.repoAdapter.Connection_Test()
                self.graphGenerator.Set_Repo_Adapter(self.repoAdapter)
            except Exception as e:
                testPass = False

        if testPass and workitemFrame and not self.workitemConfigured:
            self.workitemConfigured = True
        if testPass and repoFrame and not self.repoConfigured:
            self.repoConfigured = True

        if testPass:
            if self.workitemConfigured:
                self.featureTestStatusLabel.configure(text_color="green")
                self.featureTestStatusLabel.configure(text="Connected")
                self.featureSelectButton.configure(state="normal", fg_color=("#608BD5","#395E96"))
            if self.repoConfigured:
                self.repoTestStatusLabel.configure(text_color="green")
                self.repoTestStatusLabel.configure(text="Connected")
                self.repoSelectButton.configure(state="normal", fg_color=("#608BD5","#395E96"))
            if self.workitemConfigured and self.repoConfigured:
                self.employeeSelectButton.configure(state="normal", fg_color=("#608BD5","#395E96"))

        else:
            if workitemFrame:
                self.featureTestStatusLabel.configure(text_color="red")
                self.featureTestStatusLabel.configure(text="Failed Connection")
            elif repoFrame:
                self.repoTestStatusLabel.configure(text_color="red")
                self.repoTestStatusLabel.configure(text="Failed Connection")


        workitemFrame.grid_remove() if workitemFrame else repoFrame.grid_remove()

    def Show_Repo_Config_Frame(self):
        self.repoConfigFrame = customtkinter.CTkFrame(master=self.app)
        self.repoConfigFrame.grid()
        defaultUsername = None
        defaultPassword = None
        defaultOrg = None
        defaultProject = None

        if self.externalRepoInterface == ExternalRepoInterface.ADO:
            defaultUsername = os.getenv("ado_username")
            defaultPassword = os.getenv("ado_PAT")
            defaultOrg = os.getenv("ado_org")
            defaultProject = os.getenv("ado_project")
        elif self.externalRepoInterface == ExternalRepoInterface.BITBUCKET:
            defaultUsername = os.getenv("bitbucket_username") if os.getenv("bitbucket_username") else os.getenv("jira_username")
            defaultPassword = os.getenv("bitbucket_PAT") if os.getenv("bitbucket_PAT") else os.getenv("jira_PAT")
            defaultOrg = os.getenv("bitbucket_org") if os.getenv("bitbucket_org") else os.getenv("jira_org")
            defaultProject = os.getenv("bitbucket_project") if os.getenv("bitbucket_project") else os.getenv("jira_project")
        elif self.externalRepoInterface == ExternalRepoInterface.GITHUB:
            defaultUsername = os.getenv("github_username")
            defaultPassword = os.getenv("github_PAT")
            defaultOrg = os.getenv("github_org")
            defaultProject = os.getenv("github_project")

        usernameLabel = customtkinter.CTkLabel(master=self.repoConfigFrame, text='Username', padx=15, pady=20)
        self.usernameEntry = customtkinter.CTkEntry(master=self.repoConfigFrame, placeholder_text=f'{self.externalWorkitemInterface.name} username')
        if defaultUsername:
            self.usernameEntry.insert(0, defaultUsername)

        passwordLabel = customtkinter.CTkLabel(master=self.repoConfigFrame, text='Password', padx=15, pady=20)
        self.passwordEntry = customtkinter.CTkEntry(master=self.repoConfigFrame, placeholder_text=f'{self.externalWorkitemInterface.name} password', show="*")
        if defaultPassword:
            self.passwordEntry.insert(0, defaultPassword)

        organizationLabel = customtkinter.CTkLabel(master=self.repoConfigFrame, text='Orgranization', padx=15, pady=20)
        self.organizationEntry = customtkinter.CTkEntry(master=self.repoConfigFrame)
        if defaultOrg:
            self.organizationEntry.insert(0, defaultOrg)

        buttonRow = 3
        if self.externalRepoInterface in [ExternalRepoInterface.ADO]:
            buttonRow += 1
            projectLabel = customtkinter.CTkLabel(master=self.repoConfigFrame, text="Project", padx=15, pady=20)
            self.projectEntry = customtkinter.CTkEntry(master=self.repoConfigFrame)
            if defaultProject:
                self.projectEntry.insert(0, defaultProject)

        if self.externalWorkitemInterface == ExternalWorkitemInterface.ADO:
            projectLabel = customtkinter.CTkLabel(master=self.repoConfigFrame, text='Project', padx=15, pady=20)
            self.projectEntry = customtkinter.CTkEntry(master=self.repoConfigFrame)
            if defaultProject:
                self.projectEntry.insert(0, defaultProject)
                
        submitButton = customtkinter.CTkButton(master=self.repoConfigFrame, text='Submit', command=lambda:[self.__Gather_And_Remove_Config(repoFrame=self.repoConfigFrame)], padx=15, pady=20)

        usernameLabel.grid(row=0, column=0)
        self.usernameEntry.grid(row=0, column=1)
        passwordLabel.grid(row=1, column=0)
        self.passwordEntry.grid(row=1, column=1)
        organizationLabel.grid(row=2, column=0)
        self.organizationEntry.grid(row=2, column=1)
        if self.externalRepoInterface in [ExternalRepoInterface.ADO]:
            projectLabel.grid(row=3, column=0)
            self.projectEntry.grid(row=3, column=1)
            submitButton.grid(row=buttonRow, column=0)
        else:
            submitButton.grid(row=buttonRow, column=0)

    def Show_Workitem_Config_Frame(self):
        self.workitemConfigFrame = customtkinter.CTkFrame(master=self.app)
        self.workitemConfigFrame.grid()
        defaultUsername = None
        defaultPassword = None
        defaultOrg = None
        defaultProject = None

        if self.externalWorkitemInterface == ExternalWorkitemInterface.ADO:
            defaultUsername = os.getenv("ado_username")
            defaultPassword = os.getenv("ado_PAT")
            defaultOrg = os.getenv("ado_org")
            defaultProject = os.getenv("ado_project")
        elif self.externalWorkitemInterface == ExternalWorkitemInterface.JIRA:
            defaultUsername = os.getenv("jira_username")
            defaultPassword = os.getenv("jira_PAT")
            defaultOrg = os.getenv("jira_org")
            defaultProject = os.getenv("jira_project")

        usernameLabel = customtkinter.CTkLabel(master=self.workitemConfigFrame, text='Username', padx=15, pady=20)
        self.usernameEntry = customtkinter.CTkEntry(master=self.workitemConfigFrame, placeholder_text=f'{self.externalWorkitemInterface.name} username')
        if defaultUsername:
            self.usernameEntry.insert(0, defaultUsername)

        passwordLabel = customtkinter.CTkLabel(master=self.workitemConfigFrame, text='Password', padx=15, pady=20)
        self.passwordEntry = customtkinter.CTkEntry(master=self.workitemConfigFrame, placeholder_text=f'{self.externalWorkitemInterface.name} password', show="*")
        if defaultPassword:
            self.passwordEntry.insert(0, defaultPassword)

        organizationLabel = customtkinter.CTkLabel(master=self.workitemConfigFrame, text='Orgranization', padx=15, pady=20)
        self.organizationEntry = customtkinter.CTkEntry(master=self.workitemConfigFrame)
        if defaultOrg:
            self.organizationEntry.insert(0, defaultOrg)

        if self.externalWorkitemInterface == ExternalWorkitemInterface.ADO:
            projectLabel = customtkinter.CTkLabel(master=self.workitemConfigFrame, text='Project', padx=15, pady=20)
            self.projectEntry = customtkinter.CTkEntry(master=self.workitemConfigFrame)
            if defaultProject:
                self.projectEntry.insert(0, defaultProject)
                
        submitButton = customtkinter.CTkButton(master=self.workitemConfigFrame, text='Submit', command=lambda:[self.__Gather_And_Remove_Config(workitemFrame=self.workitemConfigFrame)], padx=15, pady=20)

        usernameLabel.grid(row=0, column=0)
        self.usernameEntry.grid(row=0, column=1)
        passwordLabel.grid(row=1, column=0)
        self.passwordEntry.grid(row=1, column=1)
        organizationLabel.grid(row=2, column=0)
        self.organizationEntry.grid(row=2, column=1)
        if self.externalWorkitemInterface == ExternalWorkitemInterface.ADO:
            projectLabel.grid(row=3, column=0)
            self.projectEntry.grid(row=3, column=1)
            submitButton.grid(row=4, column=0)
        else:
            submitButton.grid(row=3, column=0)

    def Show_Repo_Frame(self):
        self.frame.grid_remove()
        self.frame = customtkinter.CTkFrame(master=self.app, width=1200)

        repoLabel = customtkinter.CTkLabel(master=self.frame, text="Repo", padx=15, pady=20)
        repoDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=self.repoAdapter.Get_Repos())
        fromDateLabel = customtkinter.CTkLabel(master=self.frame, text="From", padx=15, pady=20)
        fromDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        toDateLabel = customtkinter.CTkLabel(master=self.frame, text="To", padx=15, pady=20)
        toDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        repoImage = customtkinter.CTkButton(master=self.frame, text="Repo Metrics Chart", width=900, fg_color=('gray92', 'gray16'), pady=20)
        commitsButton = customtkinter.CTkButton(
            master=self.frame, text="Commits",
            command=lambda:[
                self.graphGenerator.Generate_Commit_Bar_Graph(
                    repo=repoDropbox.get(),
                    fromDate=self.repoAdapter.Str_To_Datetime(fromDateEntry.get()) if len(fromDateEntry.get()) > 0 else None,
                    toDate=self.repoAdapter.Str_To_Datetime(toDateEntry.get()) if len(toDateEntry.get()) > 0 else None
                ), self.Update_Image(repoImage, "repo_commits.jpg")
            ],
            pady=20, padx=15
        )

        commitsButton.grid(row=0, column=0)
        repoLabel.grid(row=1, column=0)
        repoDropbox.grid(row=2, column=0)
        fromDateLabel.grid(row=1, column=1)
        fromDateEntry.grid(row=2, column=1)
        toDateLabel.grid(row=1, column=2)
        toDateEntry.grid(row=2, column=2)
        repoImage.grid(row=3, column=0, columnspan=4)

        self.frame.grid()

    def Show_Feature_Frame(self):
        self.frame.grid_remove()
        self.frame = customtkinter.CTkFrame(master=self.app, width=1200)

        boardTeamNameList = []
        boardTeamIdList = []
        for name, id in self.workitemAdapter.Get_Board_or_Teams():
            boardTeamNameList.append(name)
            boardTeamIdList.append(id)

        projectLabel = customtkinter.CTkLabel(master=self.frame, text="Project", padx=15, pady=20)
        projectDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=self.workitemAdapter.Get_Projects())
        featureLabel = customtkinter.CTkLabel(master=self.frame, text="Feature", padx=15, pady=20)
        featureDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=self.workitemAdapter.Get_Features())
        boardTeamLabel = customtkinter.CTkLabel(master=self.frame, text="Board" if self.workitemAdapter.connectionType == ExternalWorkitemInterface.JIRA else "Team", padx=15, pady=20)
        boardTeamDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=boardTeamNameList)
        fromDateLabel = customtkinter.CTkLabel(master=self.frame, text="From", padx=15, pady=20)
        fromDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        toDateLabel = customtkinter.CTkLabel(master=self.frame, text="To", padx=15, pady=20)
        toDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        featureProgressImage = customtkinter.CTkButton(master=self.frame, text="Feature Progress Chart", width=900, fg_color=('gray92', 'gray16'), pady=20)
        progressButton = customtkinter.CTkButton(
            master=self.frame, text="Progress",
            command=lambda:[
                self.graphGenerator.Generate_State_Stacked_Area_Chart(
                    featureID=featureDropbox.get(),
                    fromDate=self.workitemAdapter.Str_To_Datetime(fromDateEntry.get()) if len(fromDateEntry.get()) > 0 else None,
                    toDate=self.workitemAdapter.Str_To_Datetime(toDateEntry.get()) if len(toDateEntry.get()) > 0 else None
                ),
                self.Update_Image(featureProgressImage, "current_feature_progress.jpg")
            ],
            pady=20, padx=15
        )
        ganttButton = customtkinter.CTkButton(
            master=self.frame, text="Gantt",
            command=lambda:[
                self.graphGenerator.Generate_Gantt_Chart(
                    workitemID=featureDropbox.get(),
                    sprintScope=boardTeamIdList[boardTeamNameList.index(boardTeamDropbox.get())]
                ),
                self.Update_Image(featureProgressImage, "feature_gantt.jpg")
            ],
            pady=20, padx=15
        )

        progressButton.grid(row=0, column=0)
        ganttButton.grid(row=0, column=1)
        projectLabel.grid(row=1, column=0)
        projectDropbox.grid(row=2, column=0)
        featureLabel.grid(row=1, column=1)
        featureDropbox.grid(row=2, column=1)
        boardTeamLabel.grid(row=1, column=2)
        boardTeamDropbox.grid(row=2, column=2)
        fromDateLabel.grid(row=1, column=3)
        fromDateEntry.grid(row=2, column=3)
        toDateLabel.grid(row=1, column=4)
        toDateEntry.grid(row=2, column=4)
        featureProgressImage.grid(row=3, column=0, columnspan=4)

        self.frame.grid()
    
    def Show_Employee_Frame(self):
        self.frame.grid_remove()
        self.frame = customtkinter.CTkFrame(master=self.app, width=1200)

        employeeLabel = customtkinter.CTkLabel(master=self.frame, text="Employee", padx=15, pady=20)
        employeeTupleList = self.workitemAdapter.Get_Employees()
        employeeList = list(map(operator.itemgetter(0), employeeTupleList))
        employeeDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=employeeList)
        fromDateLabel = customtkinter.CTkLabel(master=self.frame, text="From", padx=15, pady=20)
        fromDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        toDateLabel = customtkinter.CTkLabel(master=self.frame, text="To", padx=15, pady=20)
        toDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        employeeImage = customtkinter.CTkButton(master=self.frame, text="Employee Chart", width=900, fg_color=('gray92', 'gray16'), pady=20)
        contributionsButton = customtkinter.CTkButton(
            master=self.frame, text="Contributions",
            command=lambda:[
                self.graphGenerator.Generate_Contribution_Bar_Chart(
                    employee=employeeDropbox.get(),
                    fromDate=self.repoAdapter.Str_To_Datetime(fromDateEntry.get()) if len(fromDateEntry.get()) > 0 else None,
                    toDate=self.repoAdapter.Str_To_Datetime(toDateEntry.get()) if len(toDateEntry.get()) > 0 else None
                ),
                self.Update_Image(employeeImage, "employee_contributions.jpg")
            ],
            pady=20, padx=15
        )

        contributionsButton.grid(row=0, column=0)
        employeeLabel.grid(row=1, column=0)
        employeeDropbox.grid(row=2, column=0)
        fromDateLabel.grid(row=1, column=1)
        fromDateEntry.grid(row=2, column=1)
        toDateLabel.grid(row=1, column=2)
        toDateEntry.grid(row=2, column=2)
        employeeImage.grid(row=3, column=0, columnspan=4)

        self.frame.grid()

    def Update_Image(self, imageButton: customtkinter.CTkButton, fileName: str):
        commitBaseImage = Image.open(f"{fileName}")
        commitBaseImage = commitBaseImage.resize((1200,700))
        commitImage = ImageTk.PhotoImage(commitBaseImage, master=self.frame)
        self.featureImageList.append(commitImage)
        imageButton.configure(image=self.featureImageList[-1], text="")
        imageButton.image = self.featureImageList[-1]

    def Show_Config_Frame(self) -> None:
        if self.frame:
            self.frame.grid_remove()

        self.frame = customtkinter.CTkFrame(master=self.app)
        self.frame.grid()

        self.externalDropdownVal = None

        externalWorkitemDropdown = customtkinter.CTkOptionMenu(master=self.frame, values=["Jira", "ADO"], command=self.__Set_External_Workitem_Interface)
        self.externalworkitemListBox = externalWorkitemDropdown
        externalRepoDropdown = customtkinter.CTkOptionMenu(master=self.frame, values=["BitBucket", "ADO", "GitHub "], command=self.__Set_External_Repo_Interface)
        self.externalRepoListBox = externalRepoDropdown
        # TODO: Preset with current value
        externalWorkitemLabel = customtkinter.CTkLabel(master=self.frame, text='External Work Item Source', padx=15, pady=20)
        externalRepoLabel = customtkinter.CTkLabel(master=self.frame, text='External Repo Source', padx=15, pady=20)
        self.featureTestStatusLabel = customtkinter.CTkLabel(master=self.frame, text='', text_color="green")
        self.repoTestStatusLabel = customtkinter.CTkLabel(master=self.frame, text='', text_color="green")

        self.featureSelectButton = customtkinter.CTkButton(master=self.frame, text='Feature Metrics', command=self.Show_Feature_Frame, padx=15, pady=20, state="disabled", fg_color="gray")
        self.repoSelectButton = customtkinter.CTkButton(master=self.frame, text='Repo Metrics', command=self.Show_Repo_Frame, padx=15, pady=20, state="disabled", fg_color="gray")
        self.employeeSelectButton = customtkinter.CTkButton(master=self.frame, text='Employee Metrics', command=self.Show_Employee_Frame, padx=15, pady=20, state="disabled", fg_color="gray")

        externalWorkitemLabel.grid(row=0, column=0)
        externalWorkitemDropdown.grid(row=0, column=1)
        self.featureTestStatusLabel.grid(row=0, column=2)
        externalRepoLabel.grid(row=1, column=0)
        externalRepoDropdown.grid(row=1, column=1)
        self.repoTestStatusLabel.grid(row=1, column=2)
        self.featureSelectButton.grid(row=0, column=3)
        self.repoSelectButton.grid(row=1, column=3)
        self.employeeSelectButton.grid(row=2, column=3)

        # Start Program
        self.app.mainloop()

currentDesktopApplication = desktopApplication()
currentDesktopApplication.Show_Config_Frame()