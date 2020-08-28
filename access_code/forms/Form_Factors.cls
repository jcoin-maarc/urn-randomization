VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Factors"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub FactorName_AfterUpdate()
   gChanged = True
End Sub

Private Sub LevelOBut_Click()
   SaveCurrentRecord
   DoCmd.OpenForm "Levels", , , "ProjectNumber=" & ProjectNumber & " And FactorNumber=" & FactorNumber, , acDialog
End Sub

Private Sub nLevels_AfterUpdate()
   Dim St As String, Rst As Recordset, i As Integer
   SaveCurrentRecord
   gChanged = True
   MakeLevels Me!ProjectNumber, Me!FactorNumber, Me!nLevels
End Sub
