VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_SelectAproject"
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

   If gProjectNumber > 0 Then
      Me!zProjectNumber = gProjectNumber
   Else
      Me!zProjectNumber = 1
   End If
   
   'Me!zProjectNumber.RowSource = _
   '"SELECT Projects.ProjectName, Projects.ProjectNumber" & _
   '" FROM Projects INNER JOIN UserProjectBridge ON" & _
   '" Projects.ProjectNumber = UserProjectBridge.ProjectNumber" & _
   '" WHERE (((UserProjectBridge.UserName) = '" & gUserName & "') And" & _
   '" ((UserProjectBridge.CanRead) = True))" & _
   '" ORDER BY Projects.ProjectNumber;"
   
   'Alert Me!zProjectNumber.RowSource
   
   'Me!zProjectNumber.Requery
End Sub

Private Sub GoBut_Click()
   If Not IsNull(Me!zProjectNumber) Then
      gProjectNumber = Me!zProjectNumber
      LoadProject gProjectNumber
      gCanceled = False
   Else
      gCanceled = True
   End If
   DoCmd.Close
End Sub
