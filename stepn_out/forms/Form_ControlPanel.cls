VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_ControlPanel"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub CountEm_Click()
   DoCmd.OpenReport "CountsByProjectReport", acViewPreview, , "[ProjectNumber]=" & gProjectNumber
   DoCmd.OpenReport "CountsByFactorReport", acViewPreview, , "[ProjectNumber]=" & gProjectNumber
End Sub

Private Sub ExitBut_Click()
   DoCmd.Quit
End Sub

Private Sub Form_Close()
   SaveState
   AppShutdown
End Sub

Private Sub Form_Current()
   If gProjectNumber = 0 Then
      Me!CurProj = "(no project selected)"
   Else
      Me!CurProj = "Project " & gProjectNumber & ". " & ProjName(gProjectNumber)
   End If
   Me!PartiBut.Enabled = gProjectNumber > 0 And gCanRead
   Me!SetupBut.Enabled = gProjectNumber > 0 And gSuperUser
   Me!CountEm.Enabled = gProjectNumber > 0 And gCanRead
   Me!ListObut.Enabled = gProjectNumber > 0 And gCanRead
   Me!NewProjOBut.Enabled = gSuperUser
End Sub

Private Sub Form_Load()
   AppStartup
   GetPerms
   VersionMessage = "gRand version " & gAppVersion & Space$(5) & gAppVerDate
   LoadState
   If gProjectNumber > 0 Then
      LoadProject gProjectNumber
   End If
   zUserName = gUserName
   Form_Current
End Sub

Private Sub Form_Open(Cancel As Integer)
   DoCmd.OpenForm "Signin", , , , , acDialog
End Sub

Private Sub ListObut_Click()
   DoCmd.OpenReport "ListReport", acViewPreview, , "[ParticipantFactorLevels].[ProjectNumber]=" & gProjectNumber
End Sub

Private Sub NewProjOBut_Click()
   Dim Rst As Recordset
   
   If Question("Ok to add a new project?") Then
             
      If Not IsNull(DMax("ProjectNumber", "Projects")) Then
         gProjectNumber = DMax("ProjectNumber", "Projects") + 1
      Else
         gProjectNumber = 1
      End If
      
      Set Rst = CurrentDb.OpenRecordset("Projects", dbOpenDynaset)
      Rst.AddNew
      Rst!ProjectNumber = gProjectNumber
      Rst!ProjectName = "NEW PROJECT"
      Rst!DateCreated = Date
      Rst!UserCreated = gUserName
      Rst.Update
      Rst.Close
      
      SetupBut_Click
         
   End If

End Sub

Private Sub PartiBut_Click()
   DoCmd.OpenForm "Participants", , , "[ProjectNumber]=" & gProjectNumber
End Sub

Private Sub SelProj_Click()
   DoCmd.OpenForm "SelectAproject", , , , , acDialog
   SaveState
   GetPerms
   Form_Current
End Sub

Private Sub SetupBut_Click()
   DoCmd.OpenForm "Project", , , "[ProjectNumber]=" & gProjectNumber, , acDialog
   LoadProject gProjectNumber
   GetPerms
   Form_Current
End Sub

Private Sub UserProjBut_Click()
   DoCmd.OpenForm "UserProject", , , , , acDialog
   GetPerms
   Form_Current
End Sub
