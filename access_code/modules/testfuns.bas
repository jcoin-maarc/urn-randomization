Attribute VB_Name = "testfuns"
Option Compare Database
Option Explicit

Public gMethod As Integer

Function RunTests()
   Dim i As Integer, w As Integer
   
   DoCmd.RunSQL "DELETE * FROM SimResults"
   
   For i = 1 To 1
      'TestUrn 200, False, 1, 0
      'TestUrn 200, False, 1, 1
      TestUrn 34, False, 1, 32767
      'TestPermuted 200, False
   Next
   
End Function

Function TestUrn(HowMany As Integer, pTrace As Boolean, Alpha As Integer, Beta As Integer)
   Dim P As DAO.Recordset, PF As DAO.Recordset, SR As DAO.Recordset
   Dim ProjectID As String
   Dim i As Integer, j As Integer, K As Integer, m As Integer
   Dim F(3, 3) As Single, L(3) As Integer, R As Single, TF As Single
   
   gUserName = "TestUrn"
   
   Trace = pTrace
   
   ' levels for 3 factors
   L(1) = 2
   L(2) = 3
   L(3) = 2
   
   ' sampling fractions for 3 factors
   F(1, 1) = 101# / 166#
   F(1, 2) = 65# / 166#
   F(2, 1) = 95# / 166#
   F(2, 2) = 43# / 166#
   F(2, 3) = 28# / 166#
   F(3, 1) = 4# / 166#
   F(3, 2) = 162# / 166#
   
   DoCmd.RunSQL "DELETE * FROM Participants WHERE simulated=True"
   DoCmd.RunSQL "DELETE * FROM ParticipantFactorLevels WHERE simulated=True"
   
   Randomize
      
   Set PF = CurrentDb.OpenRecordset("ParticipantFactorLevels", dbOpenDynaset)
   Set P = CurrentDb.OpenRecordset("SELECT * FROM Participants WHERE ProjectNumber=100", dbOpenDynaset)
   ProjectID = CLng(Nz(DMax("ProjectID", "Participants", "ProjectNumber=100"), "0000"))
   For i = 1 To HowMany
      ProjectID = Format$(CLng(ProjectID) + 1, "0000")
      P.AddNew
      P!ProjectNumber = 100
      P!ProjectID = ProjectID
      P!simulated = True
      P.Update
      For j = 1 To 3
         PF.AddNew
         PF!ProjectNumber = 100
         PF!ProjectID = Format$(ProjectID, "0000")
         PF!FactorNumber = j
         PF!simulated = True
         TF = 0#
         R = Rnd()
         For m = 1 To L(j)
            TF = TF + F(j, m)
            If TF >= R Then
               PF!LevelNumber = m
               Exit For
            End If
         Next
         PF.Update
      Next
   Next
   PF.Close
   P.Requery
   P.MoveFirst
   While Not P.EOF
      If Nz(P!GroupNumber, 0) = 0 Then
         URandomize 100, P!ProjectID, Alpha, Beta
      End If
      P.MoveNext
   Wend
   P.Close
   
   ' save the sim results
   Set SR = CurrentDb.OpenRecordset("SimResults", dbOpenDynaset)
   SR.AddNew
   SR!Alpha = Alpha
   SR!Beta = Beta
   SR!n1 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=1"), 0)
   SR!n2 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=2"), 0)
   SR!n3 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=3"), 0)
   SR!n4 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=4"), 0)
   m = (SR!n1 + SR!n2 + SR!n3 + SR!n4) / 4
   SR!Imbalance = Abs(SR!n1 - m) + Abs(SR!n2 - m) + Abs(SR!n3 - m) + Abs(SR!n4 - m)
   SR.Update
   SR.Close
   
End Function

Function TestPermuted(HowMany As Integer, pTrace As Boolean)
   Dim P As DAO.Recordset, PF As DAO.Recordset, SR As DAO.Recordset
   Dim ProjectID As String
   Dim i As Integer, j As Integer, K As Integer, m As Integer
   Dim F(3, 3) As Single, L(3) As Integer, R As Single, TF As Single
   Dim rCode As Integer
   
   gUserName = "Zelen"
   
   Trace = pTrace
   
   ' levels for 3 factors
   L(1) = 2
   L(2) = 3
   L(3) = 2
   
   ' sampling fractions for 3 factors
   F(1, 1) = 101# / 166#
   F(1, 2) = 65# / 166#
   F(2, 1) = 95# / 166#
   F(2, 2) = 43# / 166#
   F(2, 3) = 28# / 166#
   F(3, 1) = 4# / 166#
   F(3, 2) = 162# / 166#
   
   'F(1, 1) = 0#
   'F(1, 2) = 1#
   'F(2, 1) = 0#
   'F(2, 2) = 0#
   'F(2, 3) = 1#
   'F(3, 1) = 1#
   'F(3, 2) = 0#
   
   DoCmd.RunSQL "DELETE * FROM Participants WHERE simulated=True"
   DoCmd.RunSQL "DELETE * FROM ParticipantFactorLevels WHERE simulated=True"
   
   Randomize
      
   Set PF = CurrentDb.OpenRecordset("ParticipantFactorLevels", dbOpenDynaset)
   Set P = CurrentDb.OpenRecordset("SELECT * FROM Participants WHERE ProjectNumber=100", dbOpenDynaset)
   ProjectID = CLng(Nz(DMax("ProjectID", "Participants", "ProjectNumber=100"), "0000"))
   For i = 1 To HowMany
      ProjectID = Format$(CLng(ProjectID) + 1, "0000")
      P.AddNew
      P!ProjectNumber = 100
      P!ProjectID = ProjectID
      P!simulated = True
      P.Update
      For j = 1 To 3
         PF.AddNew
         PF!ProjectNumber = 100
         PF!ProjectID = Format$(ProjectID, "0000")
         PF!FactorNumber = j
         PF!simulated = True
         TF = 0#
         R = Rnd()
         For m = 1 To L(j)
            TF = TF + F(j, m)
            If TF >= R Then
               PF!LevelNumber = m
               Exit For
            End If
         Next
         PF.Update
      Next
   Next
   PF.Close
   P.Requery
   P.MoveFirst
   While Not P.EOF
      If Nz(P!GroupNumber, 0) = 0 Then
         rCode = PRandomize(100, P!ProjectID)
         If Trace Then _
            Debug.Print "ID #" & P!ProjectID & ", Result=" & rCode
      End If
      If Trace Then _
         Debug.Print "ID #" & P!ProjectID & ", Group=" & P!GroupNumber
      P.MoveNext
   Wend
   P.Close
   
   ' save the sim results
   Set SR = CurrentDb.OpenRecordset("SimResults", dbOpenDynaset)
   SR.AddNew
   SR!Alpha = 0
   SR!Beta = 0
   SR!n1 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=1"), 0)
   SR!n2 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=2"), 0)
   SR!n3 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=3"), 0)
   SR!n4 = Nz(DCount("ProjectID", "Participants", "ProjectNumber=100 And GroupNumber=4"), 0)
   m = (SR!n1 + SR!n2 + SR!n3 + SR!n4) / 4
   SR!Imbalance = Abs(SR!n1 - m) + Abs(SR!n2 - m) + Abs(SR!n3 - m) + Abs(SR!n4 - m)
   SR.Update
   SR.Close
   
End Function

