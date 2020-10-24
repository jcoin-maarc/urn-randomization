VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_NewParti"
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
   Me.Caption = gProjectName
   Me!zProjectID = ""
   Me!zTypMsg = "type:" & IIf(gProjectIDType = cNUMERIC, "numeric", "alpha") & _
      "  width:" & gProjectIDWidth
End Sub

Private Sub OkBut_Click()
   Dim Rst As Recordset, St As String
   If IsNull(Me!zProjectID) Then
      Alert "Cannot create a record with a null Project ID."
      Exit Sub
   End If
   If Me!zProjectID = "" Then
      Alert "Cannot create a record with a blank Project ID."
      Exit Sub
   End If
   If gProjectIDType = cNUMERIC And Not (IsNumeric(Me!zProjectID)) Then
      Alert "Project ID must be numeric."
      Exit Sub
   End If
   If gProjectIDType = cNUMERIC And CLng(Me!zProjectID) <= 0 Then
      Alert "Project ID must be a positive number."
      Exit Sub
   End If
   St = "SELECT * FROM Participants WHERE" & _
      " Participants.ProjectNumber=" & gProjectNumber & " AND " & _
      " Participants.ProjectID='" & Me!zProjectID & "';"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   If Not Rst.BOF Then
      Rst.Close
      Alert "The Project ID you entered is already in use!"
      Exit Sub
   End If
   
   Rst.AddNew
   Rst!ProjectNumber = gProjectNumber
   Rst!ProjectID = Me!zProjectID
   Rst!DateCreated = Now()
   Rst!UserCreated = gUserName
   Rst.Update
   Rst.Close
   
   gCanceled = False
   gProjectID = Me!zProjectID
   DoCmd.Close
   
End Sub

Private Sub zProjectID_AfterUpdate()
   If Not IsNull(zProjectID) Then
      If gProjectIDType = cNUMERIC Then
         If Not IsNumeric(zProjectID) Then
            Alert "Project ID must be a number."
            zProjectID = ""
         Else
            zProjectID = Right$(String$(gProjectIDWidth, "0") & CStr(CLng(zProjectID)), gProjectIDWidth)
         End If
      Else
         zProjectID = UCase$(Trim$(zProjectID))
      End If
   End If
End Sub
