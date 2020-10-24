VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Setup"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub CanBut_Click()
   gCanceled = True
   DoCmd.Close
End Sub

Private Sub Form_Load()
   Me!zProjectNumber = gProjectNumber
End Sub

Private Sub GoBut_Click()
   Dim Rst As Recordset, i As Integer
   If NewProject Then
   
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
         LoadProject gProjectNumber
         gCanceled = False
         DoCmd.Close
         
      End If
   
   Else
   
      If Not IsNull(Me!zProjectNumber) Then
         gProjectNumber = Me!zProjectNumber
         gCanceled = False
         DoCmd.Close
      End If
      
   End If

End Sub

Private Sub NewProject_AfterUpdate()
   If NewProject Then
      zProjectNumber = 0
   End If
End Sub

Private Sub zProjectNumber_AfterUpdate()
   If zProjectNumber > 0 Then
      NewProject = False
   End If
End Sub
