VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_ForceAssign"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub CanBut_Click()
   gGroupNumber = 0
   DoCmd.Close
End Sub

Private Sub OkBut_Click()

   If Not IsNull([zGroupNumber]) Then
      If ([zGroupNumber] < 1) Or _
         ([zGroupNumber] > Nz(DFirst("nGroups", "Projects", "ProjectNumber=" & gProjectNumber), 0)) Then
         Alert "Invalid treatment group number."
      Else
         gGroupNumber = zGroupNumber
         DoCmd.Close
      End If
   End If
   
End Sub
