VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Participants"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub ClosaBut_Click()
   DoCmd.Close
End Sub

Private Sub DeleteObut_Click()
   Dim St As String, pID As String, pProject As Integer
   
   If Nz(Me!GroupNumber) > 0 Then
      Alert "You must de-randomize before deleting!"
      Exit Sub
   End If
   
   If Not Question("CONFIRM: Delete all data for this patient?") Then
      Exit Sub
   End If
   
   pProject = Me!ProjectNumber
   pID = Me!ProjectID
   
   DoCmd.SetWarnings False
   St = "DELETE * FROM Participants" & _
   " WHERE Participants.ProjectNumber=" & pProject & _
   " AND Participants.Projectid='" & pID & "';"
   DoCmd.RunSQL St
   
   St = "DELETE * FROM ParticipantFactorLevels" & _
   " WHERE ParticipantFactorLevels.ProjectNumber=" & pProject & _
   " AND ParticipantFactorLevels.Projectid='" & pID & "';"
   DoCmd.RunSQL St
   DoCmd.SetWarnings True
   
   Alert "Data deleted."
   Me.Requery
   
End Sub

Private Sub FirstaBut_Click()
On Error GoTo Err_FirstaBut_Click


    DoCmd.GoToRecord , , acFirst

Exit_FirstaBut_Click:
    Exit Sub

Err_FirstaBut_Click:
    MsgBox Err.Description
    Resume Exit_FirstaBut_Click
    
End Sub

Private Sub Form_Current()
   If IsNull(Me!ProjectID) Then
      gProjectID = ""
      Me!RandObut.Enabled = False
      [ProjectID_List] = Null
   Else
      gProjectID = Me!ProjectID
      Me!RandObut.Enabled = True
      [ProjectID_List] = [ProjectID]
   End If
End Sub

Private Sub Form_Load()
   Me.AllowEdits = gCanWrite
   Me!NewBut.Enabled = gCanAddSubjects
   Me!RandObut.Visible = gCanRandomize
   Me!ShowConfidential.Enabled = gCanAddSubjects
   Me!zProjectNumber = gProjectNumber
   Me!zProjName = ProjName(gProjectNumber)
   MeShow
End Sub

Private Sub NewBut_Click()
   Dim RClone As Recordset, HoldID As String
   DoCmd.OpenForm "NewParti", , , , , acDialog
   If gProjectID <> "" Then
      ' form_current will change gProjectID
      HoldID = gProjectID
      Me.Requery
      gProjectID = HoldID
      Set RClone = Me.RecordsetClone
      RClone.FindFirst "ProjectID='" & gProjectID & "'"
      If Not RClone.NoMatch Then
         Me.Bookmark = RClone.Bookmark
         Me!RandObut.SetFocus
      End If
      Set RClone = Nothing
   End If
End Sub

Private Sub PrevaBut_Click()
On Error GoTo Err_PrevaBut_Click


    DoCmd.GoToRecord , , acPrevious

Exit_PrevaBut_Click:
    Exit Sub

Err_PrevaBut_Click:
    MsgBox Err.Description
    Resume Exit_PrevaBut_Click
    
End Sub
Private Sub Nextabut_Click()
On Error GoTo Err_Nextabut_Click


    DoCmd.GoToRecord , , acNext

Exit_Nextabut_Click:
    Exit Sub

Err_Nextabut_Click:
    MsgBox Err.Description
    Resume Exit_Nextabut_Click
    
End Sub
Private Sub LastaBut_Click()
On Error GoTo Err_LastaBut_Click


    DoCmd.GoToRecord , , acLast

Exit_LastaBut_Click:
    Exit Sub

Err_LastaBut_Click:
    MsgBox Err.Description
    Resume Exit_LastaBut_Click
    
End Sub
Private Sub FindBut_Click()
On Error GoTo Err_FindBut_Click


    Screen.PreviousControl.SetFocus
    DoCmd.DoMenuItem acFormBar, acEditMenu, 10, , acMenuVer70

Exit_FindBut_Click:
    Exit Sub

Err_FindBut_Click:
    MsgBox Err.Description
    Resume Exit_FindBut_Click
    
End Sub
Private Sub Command52_Click()
On Error GoTo Err_Command52_Click


    Screen.PreviousControl.SetFocus
    DoCmd.FindNext

Exit_Command52_Click:
    Exit Sub

Err_Command52_Click:
    MsgBox Err.Description
    Resume Exit_Command52_Click
    
End Sub

Private Sub ProjectID_List_AfterUpdate()
   Me.RecordsetClone.FindFirst "ProjectID='" & [ProjectID_List] & "'"
   Me.Bookmark = Me.RecordsetClone.Bookmark
End Sub

Private Sub RandObut_Click()
   Dim St As String
   SaveCurrentRecord
   MakeFactorLevels Me!ProjectNumber, Me!ProjectID
   If Not IsNull(Me!Gender) Then
      St = "UPDATE ParticipantFactorLevels" & _
      " INNER JOIN Factors" & _
      " ON (ParticipantFactorLevels.FactorNumber = Factors.FactorNumber)" & _
      " AND (ParticipantFactorLevels.ProjectNumber = Factors.ProjectNumber)" & _
      " SET ParticipantFactorLevels.LevelNumber = " & Me!Gender & _
      " WHERE (((ParticipantFactorLevels.ProjectNumber)=" & Me!ProjectNumber & ")" & _
      " AND ((ParticipantFactorLevels.ProjectID)='" & Me!ProjectID & "')" & _
      " AND ((Factors.IsGender)=True));"
      DoCmd.RunSQL St
   End If
   DoCmd.OpenForm "FactorLevels", , , "ProjectNumber=" & Me!ProjectNumber & " And ProjectID='" & Me!ProjectID & "'"
End Sub

Private Sub MeShow()
   Dim Ctl As Control
   For Each Ctl In Me.Controls
      Select Case Ctl.Tag
      Case "C"
         Ctl.Visible = [ShowConfidential]
      End Select
   Next
End Sub
Private Sub ShowConfidential_AfterUpdate()
   MeShow
End Sub
