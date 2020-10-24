VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_GroupNames"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub nLevels_AfterUpdate()
   Dim St As String, Rst As Recordset, i As Integer
   St = "SELECT * FROM Levels WHERE Levels.ProjectNumber=" & _
      Me!ProjectNumber & " And Levels.FactorNumber=" & _
      Me!FactorNumber & ";"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   For i = 1 To Me!nLevels
      Rst.FindFirst "[LevelNumber]=" & i
      If Rst.NoMatch Then
         Rst.AddNew
         Rst!ProjectNumber = Me!ProjectNumber
         Rst!FactorNumber = Me!FactorNumber
         Rst!LevelNumber = i
         Rst!LevelName = "Level " & Format$(i, "00")
         Rst.Update
      End If
   Next i
End Sub

Private Sub ClosaBut_Click()
   DoCmd.Close
End Sub

Private Sub GroupName_AfterUpdate()
   gChanged = True
End Sub
