VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_Project"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database
Option Explicit

Private Sub BlockSize_AfterUpdate()
   If [BlockSize] Mod Nz([nGroups], 0) <> 0 Then
      Alert "Blocksize must be a multiple of the number of treatment groups."
      [BlockSize] = [BlockSize].OldValue
   Else
      gChanged = True
      MeEnabler
   End If
End Sub


Private Sub ClosaBut_Click()
   Dim St As String
   ' Audit entry
   If gChanged Then
      
      SaveCurrentRecord
      
      SumLevels
   
      MakeLevelTables ProjectNumber
      
      St = "[Project Specs]"
      St = St & " PROJECTNUMBER:" & ProjectNumber
      St = St & " PROJECTNAME:""" & ProjectName & """"
      St = St & " RALG:" & RAlg
      If RAlg = cAlgPermuted Then
         St = St & " BLOCKSIZE:" & BlockSize
      End If
      St = St & " NGROUPS:" & nGroups
      St = St & " NFACTORS:" & nFactors
      St = St & " SLEVELS:" & SLevels
      St = St & " PLEVELS:" & PLevels
      EnterAudit St
      
      LoadProject gProjectNumber
   End If
   
   ' END TRANSACTION
   'gWsp.CommitTrans dbFlushOSCacheWrites
   'Set gWsp = Nothing
   
   DoCmd.Close
End Sub
Private Sub MeEnabler()
   If RAlg = cAlgPermuted Then
      Me!BlockLenLabel.Visible = True
      Me!BlockSize.Visible = True
      Me!BlockSize.Enabled = True
   Else
      Me!BlockLenLabel.Visible = False
      Me!BlockSize.Visible = False
      Me!BlockSize.Enabled = False
   End If
   If gChanged Then
      Me!ClosaBut.Caption = "Save && Exit"
   Else
      Me!ClosaBut.Caption = "Close"
   End If
End Sub

Private Sub Command29_Click()
   DoCmd.OpenForm "GroupNames", , , "[ProjectNumber]=" & ProjectNumber, , acDialog
   If gChanged Then
      MeEnabler
   End If
End Sub

Private Sub FactorSubform_Exit(Cancel As Integer)
   If gChanged Then
      SumLevels
      MeEnabler
   End If
End Sub
Sub SumLevels()
   Dim St As String, Rst As Recordset
   St = "SELECT * FROM Factors WHERE Factors.ProjectNumber=" & ProjectNumber
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   SLevels = 0
   PLevels = 1
   Do While Not Rst.EOF
      SLevels = SLevels + Rst!nLevels
      PLevels = PLevels * Rst!nLevels
      Rst.MoveNext
   Loop
   Rst.Close
   'Alert pSLevels & ":" & pPLevels
End Sub

Private Sub Form_Load()
   
   ' BEGIN TRANSACTION
   'Set gWsp = DBEngine.Workspaces(0)
   'gWsp.BeginTrans
   
   SumLevels
   MeEnabler
   gChanged = False
End Sub

Private Sub nFactors_AfterUpdate()
   Dim St As String, Rst As Recordset, i As Integer, j As Integer
   SaveCurrentRecord
   DoCmd.SetWarnings False
   St = "DELETE * FROM Factors WHERE" & _
      " Factors.ProjectNumber=" & Me!ProjectNumber & " And" & _
      " Factors.FactorNumber > " & Me!nFactors & " ;"
   DoCmd.RunSQL St
   St = "SELECT * FROM Factors WHERE Factors.ProjectNumber=" & Me!ProjectNumber & ";"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   For i = 1 To Me!nFactors
      Rst.FindFirst "[FactorNumber]=" & i
      If Rst.NoMatch Then
         Rst.AddNew
         Rst!ProjectNumber = Me!ProjectNumber
         Rst!FactorNumber = i
         Rst!FactorName = "Factor " & Format$(i, "00")
         Rst!nLevels = 2
         Rst.Update
         Rst.FindFirst "[FactorNumber]=" & i
      End If
      MakeLevels Me!ProjectNumber, i, Rst!nLevels
   Next i
   DoCmd.SetWarnings True
   Me!FactorSubform.Requery
   gChanged = True
   SumLevels
   MeEnabler
End Sub

Private Sub nGroups_AfterUpdate()
   SaveCurrentRecord
   If Not IsNull([nGroups]) Then
      MakeGroupNames ProjectNumber, nGroups
   End If
   gChanged = True
   MeEnabler
End Sub

Private Sub ProjectName_AfterUpdate()
   gChanged = True
   MeEnabler
End Sub

Private Sub RAlg_AfterUpdate()
   Select Case Me!RAlg
   Case 1
      If IsNull(Me!BlockSize) Then
         Me!BlockSize = 4
      End If
   Case 2
      Me!BlockSize = Null
   Case 3
      Me!BlockSize = Null
   End Select
   gChanged = True
   MeEnabler
End Sub
