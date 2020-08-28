VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Levels"
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

Private Sub IsGender_AfterUpdate()
   Dim Rst As Recordset
   If IsGender Then
      Set Rst = Me.RecordsetClone
      
      Rst.FindFirst "[levelnumber]=1"
      If Rst.NoMatch Then
         Rst.AddNew
      Else
         Rst.Edit
      End If
      Rst!ProjectNumber = Me!ProjectNumber
      Rst!FactorNumber = Me!FactorNumber
      Rst!LevelNumber = 1
      Rst!LevelName = "Male"
      Rst.Update
      
      Rst.FindFirst "[levelnumber]=2"
      If Rst.NoMatch Then
         Rst.AddNew
      Else
         Rst.Edit
      End If
      Rst!ProjectNumber = Me!ProjectNumber
      Rst!FactorNumber = Me!FactorNumber
      Rst!LevelNumber = 2
      Rst!LevelName = "Female"
      Rst.Update
      
      Rst.Close
      
      Me.Requery
         
   End If
End Sub

Private Sub LevelName_AfterUpdate()
   gChanged = True
End Sub
