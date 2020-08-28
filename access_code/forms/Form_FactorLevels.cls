VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_FactorLevels"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub ClosaBut_Click()
   DoCmd.Close
End Sub

Private Sub DeRandObut_Click()
   If Question("ARE YOU SURE YOU WANT TO REMOVE THE TREATMENT ASSIGNMENT??") Then
      EnterAudit ProjectID & " UN-randomized. Was in group #" & GroupNumber & "."
      [GroupNumber] = Null
      [RandDate] = Null
      SaveCurrentRecord
      Buttons
   End If
End Sub

Private Sub ForceBut_Click()
   Dim St As String, F As Integer
   
   SaveCurrentRecord
   
   St = "ProjectNumber=" & gProjectNumber & " And ProjectID='" & ProjectID & "'"
   F = DCount("LevelNumber > 0", "ParticipantFactorLevels", St)
   If F <> gnFactors Then
      Alert "CANNOT ASSIGN TREATMENT: Only " & F & " factors have been entered, but " & gnFactors & " are required."
      Exit Sub
   End If
   
   If Question("ARE YOU SURE YOU WANT TO FORCE THE TREATMENT ASSIGNMENT??") Then
      gGroupNumber = 0
      DoCmd.OpenForm "ForceAssign", , , , , acDialog
      If gGroupNumber > 0 Then
         RanAssign gProjectNumber, ProjectID, gGroupNumber
         Me.Requery
      End If
      Buttons
   End If
End Sub

Private Sub Form_Current()
   Me!LevelNumber.ValidationRule = "Is Null Or Between 1 And " & Me!nLevels
   Me!LevelNumber.ValidationText = "BAD VALUE: Enter a number between 1 and " & Me!nLevels & _
      ", or leave blank."
   If Me!nLevels > 9 Then
      Me!LevelNumber.InputMask = "99"
   Else
      Me!LevelNumber.InputMask = "99"
   End If
End Sub

Private Sub Form_Load()
   ' null, not zero, used for missing
   If Not IsNull(GroupNumber) Then
      If GroupNumber <= 0 Then
         GroupNumber = Null
      End If
   End If
   Buttons
End Sub
Private Sub Buttons()
   ClosaBut.SetFocus
   RandObut.Enabled = gCanRandomize And IsNull(GroupNumber)
   ForceBut.Enabled = gCanRandomize And IsNull(GroupNumber)
   DeRandObut.Enabled = gCanRandomize And Not IsNull(GroupNumber)
End Sub
Private Sub LevelNumber_AfterUpdate()
   
   If Not IsNull([LevelNumber]) Then
      If ([LevelNumber] > nLevels) Or ([LevelNumber] < 0) Then
         Alert "Invalid entry. Must be in the range 0 through " & [nLevels] & "."
         [LevelNumber] = Null
         SaveCurrentRecord
         Exit Sub
      End If
   End If
   
   SaveCurrentRecord
   
   If Nz([GroupNumber], 0) > 0 Then
      If NEQ([LevelNumber], [RanLevel]) Then
         Alert "NOTE! You have modified a risk factor AFTER treatment assignment!"
         EnterAudit _
            "Post-Assignment factor change: ID=" & [ProjectID] & _
               ", Factor=" & [FactorNumber] & _
               ", New value=" & [LevelNumber] & _
               "; Randomized value=" & [RanLevel]
            
      End If
   End If
   
   If [IsGender] Then
      [Gender] = [LevelNumber]
      SaveCurrentRecord
   End If
   
End Sub

Private Sub RandObut_Click()

   Dim St As String, F As Integer
   
   SaveCurrentRecord
   
   St = "ProjectNumber=" & [ProjectNumber] & " And ProjectID='" & [ProjectID] & "' And LevelNumber>0"
   F = Nz(DCount("LevelNumber", "ParticipantFactorLevels", St), 0)
   If F <> gnFactors Then
      Alert "CANNOT RANDOMIZE: Only " & F & " factors have been entered, but " & gnFactors & " are required."
      Exit Sub
   End If
   
   If Question("Ok to randomize this participant?") Then
      RanAssign [ProjectNumber], [ProjectID], 0
      Me.Requery
      Buttons
   End If
   
End Sub
