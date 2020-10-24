VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Signin"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub bClose_Click()
   DoCmd.Close acForm, "Signin"
End Sub

Private Sub Form_Close()
   SaveState
End Sub

Private Sub Form_Load()
   [zUserName] = gUserName
End Sub

Private Sub Form_Open(Cancel As Integer)
   LoadState
End Sub

Private Sub zUserName_AfterUpdate()
   If Not IsNull([zUserName]) Then
      gUserName = [zUserName]
   Else
      gUserName = "gRandUser"
   End If
End Sub
