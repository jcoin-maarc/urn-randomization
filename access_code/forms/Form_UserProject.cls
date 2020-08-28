VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_UserProject"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Function LoadRecord()
   Dim Rst As Recordset, St As String
   
   If IsNull(zUserName) Then
      Exit Function
   End If
   
   St = "SELECT * FROM Users WHERE Users.UserName='" & zUserName & "';"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   
   If Rst.BOF Then
      If Question("'" & zUserName & "' is not in the user table. Ok to add this username?") Then
         Rst.AddNew
         Rst!UserName = zUserName
         Rst.Update
         Rst.Close
         tUserName = zUserName
         zUserName.Requery
         zUserName = tUserName
         tUserName = ""
      Else
         Rst.Close
         zUserName = ""
         Exit Function
      End If
   End If
   
   St = "SELECT * FROM UserProjectBridge WHERE" & _
      " UserProjectBridge.UserName='" & zUserName & "' And" & _
      " UserProjectBridge.ProjectNumber=" & gProjectNumber & ";"
      
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   
   If Rst.BOF Then
      zRead = True
      zWrite = False
      zRandomize = False
      zAddSubjects = False
      tUserName = zUserName
   Else
      zRead = Rst!CanRead
      zWrite = Rst!Canwrite
      zRandomize = Rst!CanRandomize
      zAddSubjects = Rst!Canaddsubjects
      tUserName = ""
   End If
   Rst.Close
   
   zRead.Enabled = True
   zWrite.Enabled = True
   zRandomize.Enabled = True
   zAddSubjects.Enabled = True
   
End Function
Private Function SaveRecord(ByVal pUserName As String, ByVal pProjectNumber As Integer)
   Dim Rst As Recordset, St As String
   If IsNull(zUserName) Then
      Exit Function
   End If
   
   St = "SELECT * FROM UserProjectBridge WHERE" & _
      " UserProjectBridge.UserName='" & pUserName & "' And" & _
      " UserProjectBridge.ProjectNumber=" & pProjectNumber & ";"
      
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   
   If Rst.BOF Then
      Rst.AddNew
      Rst!UserName = pUserName
      Rst!ProjectNumber = pProjectNumber
   Else
      Rst.Edit
   End If
      
   Rst!CanRead = zRead
   Rst!Canwrite = zWrite
   Rst!CanRandomize = zRandomize
   Rst!Canaddsubjects = zAddSubjects
      
   Rst.Update
   Rst.Close
End Function
Private Sub CheckSave()
   If tUserName <> "" And tProjectNumber > 0 Then
      If Question("Ok to save current changes?") Then
         SaveRecord tUserName, tProjectNumber
      End If
   End If
End Sub

Private Sub CloseBut_Click()
   DoCmd.Close
End Sub

Private Sub Form_Load()
   zProj = gProjectNumber & ". " & ProjName(gProjectNumber)
   tUserName = ""
End Sub

Private Sub SaveBut_Click()
   SaveRecord zUserName, gProjectNumber
   tUserName = ""
   tProjectNumber = 0
End Sub

Private Sub zAddSubjects_AfterUpdate()
   tUserName = zUserName
End Sub

Private Sub zProjectNumber_AfterUpdate()
   CheckSave
   LoadRecord
End Sub

Private Sub zRandomize_AfterUpdate()
   tUserName = zUserName
End Sub

Private Sub zRead_AfterUpdate()
   tUserName = zUserName
End Sub

Private Sub zUserName_AfterUpdate()
   CheckSave
   LoadRecord
End Sub

Private Sub zWrite_AfterUpdate()
   tUserName = zUserName
End Sub
