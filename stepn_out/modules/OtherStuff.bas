Attribute VB_Name = "OtherStuff"
Option Compare Database
Option Explicit
Function ChangeOwnership()
   On Error GoTo Err_ChangeOwnership
   Dim Dbs As Database, ctr As Container, doc As Document
   Dim intDocCount As Integer, intCtrCount As Integer
   Const conErrNoPermissions = 3033
   ' Assign the current database to the database variable.
   Set Dbs = CurrentDb
   ' Loop through all the objects in the database,
   ' changing their ownership to the OrdersOwner account.
   For intDocCount = 0 To Dbs.Containers.Count - 1
      Set ctr = Dbs.Containers(intDocCount)
      For intCtrCount = 0 To ctr.Documents.Count - 1
         Set doc = ctr.Documents(intCtrCount)

         doc.Owner = "Admin"
      Next intCtrCount
   Next intDocCount
Bye_ChangeOwnership:
   Exit Function
Err_ChangeOwnership:
   If Err = conErrNoPermissions Then
      Resume Next
   Else
      MsgBox Err.Description
      Resume Bye_ChangeOwnership
   End If
End Function
Function QuikDraw()
   Dim Rst As Recordset
   Dim i As Integer, Blue As Integer, Green As Integer, S As Long
   Dim F As Single, R As Single
   DoCmd.SetWarnings False
   DoCmd.RunSQL "DELETE * FROM Draws;"
   Set Rst = CurrentDb.OpenRecordset("Draws", dbOpenTable)
   Randomize
   For S = 1 To 10000
      Blue = 2
      Green = 6
      i = 0
      Do While Green > 0
         i = i + 1
         Rst.AddNew
         Rst!sample = S
         Rst!draw = i
         Rst!Blue = Blue
         Rst!Green = Green
         Rst.Update
         R = Rnd
         F = CSng(Blue) / CSng(Blue + Green)
         If R >= F Then
            Green = Green - 1
         End If
      Loop
      Rst.AddNew
      Rst!sample = S
      Rst!draw = i + 1
      Rst!Blue = Blue
      Rst!Green = Green
      Rst.Update
   Next S
   Rst.Close
   DoCmd.SetWarnings True
End Function
