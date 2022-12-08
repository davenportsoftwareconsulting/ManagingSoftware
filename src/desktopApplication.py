import customtkinter
from workitemAdapter import ExternalWorkitemInterface, WorkitemAdapter
from repoAdapter import ExternalRepoInterface
import os
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
        self.graphGenerator = None

        self.usernameEntry = None
        self.passwordEntry = None
        self.organizationEntry = None
        self.projectEntry = None

        self.frame = None
        self.workitemConfigFrame = None
        self.externalWorkitemInterface = ExternalWorkitemInterface.JIRA
        self.externalRepoInterface = ExternalRepoInterface.BITBUCKET
        self.externalworkitemListBox = None
        self.externalRepoListBox = None
        self.testStatusLabel = None
        self.featureSelectButton = None
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

    def __Set_External_Repo_Interface(self, externalInterface: str):
        if externalInterface.lower() == "bitbucket":
            self.externalRepoInterface = ExternalRepoInterface.BITBUCKET
        elif externalInterface.lower() == "ado":
            self.externalRepoInterface = ExternalRepoInterface.ADO
        elif externalInterface.lower() == "git":
            self.externalRepoInterface = ExternalRepoInterface.GIT

    def Gather_All_Inputs(self):
        pass

    def __Gather_And_Remove_Config(self):
        try:
            self.workitemAdapter = WorkitemAdapter(self.externalWorkitemInterface, self.usernameEntry.get(), self.passwordEntry.get(), self.organizationEntry.get(), self.projectEntry.get() if self.projectEntry else None)
            testPass = self.workitemAdapter.connection_test()
            self.graphGenerator = GraphGenerator(self.workitemAdapter)
        except Exception as e:
            testPass = False

        if testPass:
            self.testStatusLabel.configure(text_color="green")
            self.testStatusLabel.configure(text="Connected")
            self.featureSelectButton.configure(state="normal", fg_color=("#608BD5","#395E96"))
        else:
            self.testStatusLabel.configure(text_color="red")
            self.testStatusLabel.configure(text="Failed Connection")

        self.workitemConfigFrame.grid_remove()

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
        self.passwordEntry = customtkinter.CTkEntry(master=self.workitemConfigFrame, placeholder_text=f'{self.externalWorkitemInterface.name} password')
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
                
        submitButton = customtkinter.CTkButton(master=self.workitemConfigFrame, text='Submit', command=lambda:[self.__Gather_And_Remove_Config()], padx=15, pady=20)

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

    def Show_Feature_Frame(self):
        self.frame.grid_remove()
        self.frame = customtkinter.CTkFrame(master=self.app, width=1200)

        projectLabel = customtkinter.CTkLabel(master=self.frame, text="Project", padx=15, pady=20)
        projectDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=self.workitemAdapter.Get_Projects())
        featureLabel = customtkinter.CTkLabel(master=self.frame, text="Feature", padx=15, pady=20)
        featureDropbox = customtkinter.CTkOptionMenu(master=self.frame, values=self.workitemAdapter.Get_Features())
        fromDateLabel = customtkinter.CTkLabel(master=self.frame, text="From", padx=15, pady=20)
        fromDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        toDateLabel = customtkinter.CTkLabel(master=self.frame, text="To", padx=15, pady=20)
        toDateEntry = customtkinter.CTkEntry(master=self.frame, placeholder_text="01/01/2020")
        featureProgressImage = customtkinter.CTkButton(master=self.frame, text="Feature Progress Chart", width=900, fg_color=('gray92', 'gray16'), pady=20)
        featureSubmitButton = customtkinter.CTkButton(
            master=self.frame, text="Generate",
            command=lambda:[
                self.graphGenerator.Generate_State_Stacked_Area_Chart(
                    featureID=featureDropbox.get(),
                    fromDate=self.workitemAdapter.Str_To_Datetime(fromDateEntry.get()) if len(fromDateEntry.get()) > 0 else None,
                    toDate=self.workitemAdapter.Str_To_Datetime(toDateEntry.get()) if len(toDateEntry.get()) > 0 else None
                ),
                self.Update_Feature_Image(featureProgressImage)
            ],
            pady=20
        )
        # featureProgressImage['image'] = featureImage
        # featureProgressImage = customtkinter.CTkCanvas(master=self.frame, height=250, width=500, )

        projectLabel.grid(row=0, column=0)
        projectDropbox.grid(row=1, column=0)
        featureLabel.grid(row=0, column=1)
        featureDropbox.grid(row=1, column=1)
        fromDateLabel.grid(row=0, column=2)
        fromDateEntry.grid(row=1, column=2)
        toDateLabel.grid(row=0, column=3)
        toDateEntry.grid(row=1, column=3)
        featureSubmitButton.grid(row=2, column=1)
        featureProgressImage.grid(row=3, column=0, columnspan=4)

        self.frame.grid()
    
    def Update_Feature_Image(self, imageButton: customtkinter.CTkButton):
        featureBaseImage = Image.open("current_feature_progress.jpg")
        featureBaseImage = featureBaseImage.resize((1200,700))
        featureImage = ImageTk.PhotoImage(featureBaseImage, master=self.frame)
        self.featureImageList.append(featureImage)
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
        externalRepoDropdown = customtkinter.CTkOptionMenu(master=self.frame, values=["BitBucket", "ADO", "Git"], command=self.__Set_External_Repo_Interface)
        self.externalRepoListBox = externalRepoDropdown
        # TODO: Preset with current value
        externalWorkitemLabel = customtkinter.CTkLabel(master=self.frame, text='External Work Item Source', padx=15, pady=20)
        externalRepoLabel = customtkinter.CTkLabel(master=self.frame, text='External Repo Source', padx=15, pady=20)
        self.testStatusLabel = customtkinter.CTkLabel(master=self.frame, text='', text_color="green")
        configureButton = customtkinter.CTkButton(master=self.frame, text='Configure', command=self.Show_Workitem_Config_Frame, padx=15, pady=20)

        self.featureSelectButton = customtkinter.CTkButton(master=self.frame, text='Feature Metrics', command=self.Show_Feature_Frame, padx=15, pady=20, state="disabled", fg_color="gray")

        externalWorkitemLabel.grid(row=0,column=0)
        externalWorkitemDropdown.grid(row=0,column=1)
        self.testStatusLabel.grid(row=0, column=2)
        externalRepoLabel.grid(row=1,column=0)
        externalRepoDropdown.grid(row=1,column=1)
        configureButton.grid(row=2,column=1)
        self.featureSelectButton.grid(row=0,column=3)

        # Start Program
        self.app.mainloop()

currentDesktopApplication = desktopApplication()
currentDesktopApplication.Show_Config_Frame()