Attribute VB_Name = "gRfunctions"
' 1.10 12-29-2003 Urn and PBR routines rewritten, now self-adjusting
' needing no external tables
' 1.09 12-22-2003 ReBAlUrns called before each urn assignment
' 1.08 4-3-1999 AppStartup() fixed to link from correct folder(!)
' 1.07 3-30-1999 Unsecured, split into front/back
' 1.06a 1-3-99 DELETE button added to Participants
'              ListReportQuery fixed
' 1.06 First implementation

Public Trace As Boolean

Const MINC = 1

Option Compare Database
Option Explicit

Global Const gAppVersion = "1.10"
Global Const gAppVerDate = "December 29, 2003"
Global Const gAppName = "gRand.mdb"

Global Const cAlgPermuted = 1
Global Const cAlgUrn = 2
Global Const cAlgUrnStrong = 32767
Global Const cUrnMax = 256
Global Const cGroupMax = 10

Global WordObj As Object

Global gHomeFolder As String
Global gDataFolder As String

Global gReportTitle1 As String
Global gReportTitle2 As String
Global gReportTitle3 As String
Global gReportFilter As String
Global gReportOrderBy As String

Global ReturnCode As Integer

Global gChanged As Integer
Global gCanceled As Integer

Global gProjectNumber As Integer
Global gProjectName As String
Global gUserName As String
Global gRAlg As Integer
Global gBlockSize As Integer
Global gnFactors As Integer
Global gSLevels As Integer
Global gPLevels As Integer
Global gProjectIDWidth As Integer
Global gProjectIDType As Integer
Global gSuperUser As Integer
Global gnGroups As Integer

' Permissions
Global gCanRead As Integer
Global gCanWrite As Integer
Global gCanRandomize As Integer
Global gCanAddSubjects As Integer

' Randomization fields
Global gRandDate As Date
Global gRandUser As String
Global gGroupNumber As Integer
Global gRandStratum As Integer
Global gRandSeq As Long
Global gUrnFlags(cUrnMax) As Boolean

Global tProjectNumber As Integer
Global tUserName As String

Global gProjectID As String

Global gWsp As Workspace

Global Const cNUMERIC = 0
Global Const cALPHA = 1

Global Const err_Startup = 1024
Global Const err_Setup_Urn = 2048


Const MAXFACTORS = 16
Const MAXLEVELS = 64

Public Enum RanErrCodes
   Metadata_Project = 1
   Metadata_Factors = 2
   Metadata_Levels = 3
   Participant_Not_Found = 4
   Incomplete_Data = 5
   Already_Randomized = 6
   Participant_Factor = 7
   Participant_Factor_Level = 8
End Enum

Function RanErrCodeMessage(ByVal E As Integer) As String
   Select Case E
   Case RanErrCodes.Already_Randomized
      RanErrCodeMessage = "Patient is already assigned to a treatment group."
   Case RanErrCodes.Incomplete_Data
      RanErrCodeMessage = "Insufficient data to randomize."
   Case RanErrCodes.Metadata_Factors
      RanErrCodeMessage = "Error in the factor definitions."
   Case RanErrCodes.Metadata_Levels
      RanErrCodeMessage = "Error in the factor-level definitions."
   Case RanErrCodes.Metadata_Project
      RanErrCodeMessage = "Error in the basic project setup definitions."
   Case RanErrCodes.Participant_Factor
      RanErrCodeMessage = "Factor data missing or invalid."
   Case RanErrCodes.Participant_Factor_Level
      RanErrCodeMessage = "Invalid factor level."
   Case RanErrCodes.Participant_Not_Found
      RanErrCodeMessage = "Participant not found"
   Case Else
      RanErrCodeMessage = "Unhandled error: code = " & E
   End Select
End Function

Function StrongCorrection(ByVal pProjectNumber As Integer) As Boolean
   Dim Z As String
   Z = Nz(DFirst("Label_OptField1", "Projects", "ProjectNumber=" & pProjectNumber), "")
   If (Z = "STRONGCORRECTION") Or (Z = "STRONG CORRECTION") Or (Z = "STRONGURN") Or (Z = "STRONG URN") Then
      StrongCorrection = True
   Else
      StrongCorrection = False
   End If
End Function

Function LoadState()
   gProjectNumber = Nz(DFirst("ProjectNumber", "State"), 0)
   gUserName = Nz(DFirst("UserName", "State"), "gRandUser")
   gProjectID = Nz(DFirst("ProjectID", "State"), "")
   If gUserName = "" Then gUserName = "gRandUser"
End Function

Function SaveState()
   Dim S As DAO.Recordset
   If gProjectNumber > 0 Then
      Set S = CurrentDb.OpenRecordset("State", dbOpenDynaset)
      S.Edit
      S!ProjectNumber = gProjectNumber
      S!UserName = gUserName
      S!ProjectID = gProjectID
      S!datetimestamp = Now()
      S.Update
      S.Close
   End If
End Function

' Zelen permuted-block
Function PRandomize(ByVal pProjectNumber As Integer, _
   ByVal pProjectID As String) As Integer
   Dim P As DAO.Recordset, PFL As DAO.Recordset, F As Integer, L As Integer
   Dim Project As DAO.Recordset
   Dim Levels As DAO.Recordset, Factors As DAO.Recordset, qSt As String
   Dim Dbs As Database
   Dim NF As Integer, NG As Integer, BS As Integer, GBS As Integer, maxL As Integer
   Dim a_Levels(MAXFACTORS) As Integer
   Dim a_PFL(MAXFACTORS) As Integer
   Dim i As Integer, j As Integer, K As Integer, m As Integer
   Dim Stratum As Integer
   Dim G As Integer, R As Single, pSelection As Single, cumP As Single
   Dim a_BlockCount(cGroupMax) As Integer, a_Remaining(cGroupMax) As Integer
   Dim FilledBlocks As Integer, MinFilledBlocks As Integer, TotRemaining As Integer

   If Trace Then _
      Debug.Print "Permuted-Block randomization for ID #" & pProjectID
   
   ' # factors
   NF = Nz(DFirst("nFactors", "Projects", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If NF = 0 Or NF > MAXFACTORS Then
      PRandomize = RanErrCodes.Metadata_Project
      Exit Function
   End If
   
   ' # groups
   NG = Nz(DFirst("nGroups", "Projects", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If NG = 0 Or NG > cGroupMax Then
      PRandomize = RanErrCodes.Metadata_Project
      Exit Function
   End If
   
   ' block size
   BS = Nz(DFirst("BlockSize", "Projects", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If BS < NG Then
      PRandomize = RanErrCodes.Metadata_Project
      Exit Function
   End If
   
   ' group-block size
   GBS = BS \ NG
   
   ' max #levels across all factors
   maxL = Nz(DMax("nLevels", "Factors", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If maxL = 0 Or maxL > MAXLEVELS Then
      PRandomize = RanErrCodes.Metadata_Factors
      Exit Function
   End If
   
   Set Dbs = CurrentDb
   
   ' retrieve factor information
   qSt = "SELECT ParticipantFactorLevels.*," & _
      " Factors.FactorName, Factors.nLevels, Factors.IsGender" & _
      " FROM ParticipantFactorLevels" & _
      " INNER JOIN Factors" & _
      " ON (ParticipantFactorLevels.FactorNumber = Factors.FactorNumber)" & _
      " AND (ParticipantFactorLevels.ProjectNumber = Factors.ProjectNumber)" & _
      " WHERE ((ParticipantFactorLevels.ProjectNumber = " & CStr(pProjectNumber) & ")" & _
      " And (ParticipantFactorLevels.ProjectID = '" & pProjectID & "'))" & _
      " ORDER BY ParticipantFactorLevels.FactorNumber;"
   Set PFL = Dbs.OpenRecordset(qSt, dbOpenSnapshot)
   
   m = 1
   Stratum = 1
   i = 0
   While Not PFL.EOF
      i = i + 1
      If i <> Nz(PFL!FactorNumber, 0) Then
         PRandomize = RanErrCodes.Participant_Factor
         PFL.Close
         Exit Function
      End If
      If Nz(PFL!nLevels, 0) < 1 Then
         PRandomize = RanErrCodes.Metadata_Levels
         PFL.Close
         Exit Function
      End If
      L = Nz(PFL!LevelNumber, 0)
      If L < 1 Or L > PFL!nLevels Then
         PRandomize = RanErrCodes.Participant_Factor_Level
         PFL.Close
         Exit Function
      End If
         
      Stratum = Stratum + m * (L - 1)
      m = m * PFL!nLevels
      
      If Trace Then
         Debug.Print "--> Factor #" & i & "=" & L & ", nLevels=" & PFL!nLevels & ", Stratum=" & Stratum
      End If
      
      PFL.MoveNext
   Wend
   
   PFL.Close
   
   ' retrieve the participant record
   Set P = Dbs.OpenRecordset( _
      "SELECT * FROM Participants" & _
         " WHERE ProjectNumber=" & pProjectNumber & _
         " AND ProjectID='" & pProjectID & "'", _
      dbOpenDynaset)
   If P.EOF Then
      PRandomize = RanErrCodes.Participant_Not_Found
      P.Close
      Exit Function
   End If
   
   If Nz(P!GroupNumber, 0) > 0 Then
      PRandomize = RanErrCodes.Already_Randomized
      P.Close
      Exit Function
   End If
   
   ' HOW IT WORKS
   
   ' NG - Number of treatment groups
   ' BS - Block size
   ' GBS - Number of allocations per group per block
   '
   ' The block sequence for the stratum is derived from the data table.
   ' A completed block is one that has the full complement of allocations
   ' for each group.
   '
   ' The a_BlockCount() array stores the number of filled blocks for
   ' each treatment group. The number of filled blocks, therefore, is
   ' the minimum value for a_BlockCount() across all groups. This value
   ' is stored in MinFilledBlocks.
   '
   ' The number of filled blocks (=MinFilledBlocks) is then
   ' subtracted off each element in a_BlockCount(), to yield
   ' the current block allocations.
   '
   ' The array a_Remaining() is then determined. This stores the number
   ' of allocations remaining in each treatment group to fill out the block.
   ' Sampling fractions are based on these values divided by the total
   ' number remaining. Through various misadventures, eg external or
   ' forced randomizations, a given allocation may exceed the
   ' design max (GBS), in which case the number remaining is set to zero.
   
   
   ' count how many randomized into each group for this stratum
   MinFilledBlocks = 32767
   For i = 1 To NG
      a_BlockCount(i) = Nz(DCount("ProjectID", "Participants", _
         "ProjectNumber=" & pProjectNumber & " AND RandStratum=" & Stratum & " AND GroupNumber=" & i), 0)
      If Trace Then _
         Debug.Print "--> Stratum=" & Stratum & ", GroupNumber=" & i & ", Count=" & a_BlockCount(i)
      FilledBlocks = a_BlockCount(i) \ GBS
      If FilledBlocks < MinFilledBlocks Then
         MinFilledBlocks = FilledBlocks
      End If
   Next
   
   If Trace Then _
      Debug.Print "--> #filled blocks=" & MinFilledBlocks
      
   ' now remainder-down to construct the current block
   TotRemaining = 0
   For i = 1 To NG
      a_BlockCount(i) = a_BlockCount(i) - MinFilledBlocks * GBS
      If a_BlockCount(i) > GBS Then
         a_Remaining(i) = 0
      Else
         a_Remaining(i) = GBS - a_BlockCount(i)
      End If
      TotRemaining = TotRemaining + a_Remaining(i)
      If Trace Then _
         Debug.Print "--> GroupNumber=" & i & ", Count=" & a_BlockCount(i) & ", Remaining=" & a_Remaining(i)
   Next
   
   ' calculate sampling fractions
   ' and select group
   Randomize
   R = Rnd()
   If Trace Then _
      Debug.Print "--> R=" & R
   cumP = 0#
   G = 0
   For i = 1 To NG
      pSelection = CSng(a_Remaining(i)) / CSng(TotRemaining)
      cumP = cumP + pSelection
      If Trace Then _
         Debug.Print "--> GroupNumber=" & i & ", Selection probability=" & pSelection & ", Cum=" & cumP
      If R <= cumP Then
         G = i
         If Trace Then _
            Debug.Print "---> Group " & G & " selected."
         Exit For
      End If
   Next
   
   ' update the globals
   gGroupNumber = G
   
   P.Edit
   P!GroupNumber = G
   P!RandMethod = cAlgPermuted
   P!RandStratum = Stratum
   P!RandDate = Now()
   P!RandUser = Left$(gUserName, 24)
   P.Update
   
   P.Close
      
   EnterAudit "Permuted-Block: " & pProjectID & " randomized into group #" & G & "."
   
   PRandomize = 0
   
End Function

' Urn randomization
' Currently, the standard parms are used (Alpha=Beta=1)
' Although Beta>>Alpha supposedly increases balance adjustment
' in practice value of Beta does not seem to matter much.
' Note: Alpha=1, Beta=0 is simple random sampling
Function URandomize(ByVal pProjectNumber As Integer, ByVal pProjectID As String, ByVal Alpha As Integer, ByVal Beta As Integer) As Integer
   Dim P As DAO.Recordset, PFL As DAO.Recordset, F As Integer, L As Integer
   Dim Project As DAO.Recordset
   Dim Levels As DAO.Recordset, Factors As DAO.Recordset, qSt As String
   Dim Dbs As Database
   Dim NF As Integer, NG As Integer, maxL As Integer
   Dim a_Levels(MAXFACTORS) As Integer
   Dim a_PFL(MAXFACTORS) As Integer
   Dim i As Integer, j As Integer, K As Integer, m As Integer
   Dim a_Marbles(MAXFACTORS, cGroupMax) As Integer
   Dim a_Urn(MAXFACTORS) As Integer, a_Urn_Group(MAXFACTORS, cGroupMax) As Integer
   Dim u As Integer, nU As Integer, urnData As DAO.Recordset
   Dim N As Integer
   Dim WorstBal As Single, a_WorstUrn(MAXFACTORS) As Integer, _
      nWorstBal As Integer, a_Bal(MAXFACTORS) As Single, WorstUrn As Integer
   Dim E As Single, T As Single, w As Single, Wj(cGroupMax) As Single, R As Single, X As Single
   Dim G As Integer
   Dim pBeta As Integer
   
   If Beta = 32767 Then
      pBeta = 1
   Else
      pBeta = Beta
   End If

   If Trace Then _
      Debug.Print "Urn randomization for ID #" & pProjectID
   
   ' # factors
   NF = Nz(DFirst("nFactors", "Projects", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If NF = 0 Or NF > MAXFACTORS Then
      URandomize = RanErrCodes.Metadata_Project
      Exit Function
   End If
   
   ' # groups
   NG = Nz(DFirst("nGroups", "Projects", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If NG = 0 Or NG > cGroupMax Then
      URandomize = RanErrCodes.Metadata_Project
      Exit Function
   End If
   
   ' max #levels across all factors
   maxL = Nz(DMax("nLevels", "Factors", "ProjectNumber=" & CStr(pProjectNumber)), 0)
   If maxL = 0 Or maxL > MAXLEVELS Then
      URandomize = RanErrCodes.Metadata_Factors
      Exit Function
   End If
   
   Set Dbs = CurrentDb
   
   ' retrieve factor information
   qSt = "SELECT ParticipantFactorLevels.*," & _
      " Factors.FactorName, Factors.nLevels, Factors.IsGender" & _
      " FROM ParticipantFactorLevels" & _
      " INNER JOIN Factors" & _
      " ON (ParticipantFactorLevels.FactorNumber = Factors.FactorNumber)" & _
      " AND (ParticipantFactorLevels.ProjectNumber = Factors.ProjectNumber)" & _
      " WHERE ((ParticipantFactorLevels.ProjectNumber = " & CStr(pProjectNumber) & ")" & _
      " And (ParticipantFactorLevels.ProjectID = '" & pProjectID & "'))" & _
      " ORDER BY ParticipantFactorLevels.FactorNumber;"
   Set PFL = Dbs.OpenRecordset(qSt, dbOpenSnapshot)
   i = 0
   nU = 0 ' # urns
   While Not PFL.EOF
      i = i + 1
      If i <> Nz(PFL!FactorNumber, 0) Then
         URandomize = RanErrCodes.Participant_Factor
         PFL.Close
         Exit Function
      Else
         a_Levels(i) = Nz(PFL!nLevels, 0)
         If a_Levels(i) < 1 Or a_Levels(i) > MAXLEVELS Then
            URandomize = RanErrCodes.Metadata_Factors
            PFL.Close
            Exit Function
         Else
            j = Nz(PFL!LevelNumber, 0)
            If j < 1 Or j > a_Levels(i) Then
               URandomize = RanErrCodes.Participant_Factor_Level
               PFL.Close
               Exit Function
            Else
               a_PFL(i) = j
            End If
         End If
      End If
      PFL.MoveNext
   Wend
   PFL.Close
   If i <> NF Then
      URandomize = RanErrCodes.Metadata_Factors
      Exit Function
   End If
   
   ' retrieve the participant record
   Set P = Dbs.OpenRecordset( _
      "SELECT * FROM Participants" & _
         " WHERE ProjectNumber=" & pProjectNumber & _
         " AND ProjectID='" & pProjectID & "'", _
      dbOpenDynaset)
   If P.EOF Then
      URandomize = RanErrCodes.Participant_Not_Found
      P.Close
      Exit Function
   End If
   
   If Nz(P!GroupNumber, 0) > 0 Then
      URandomize = RanErrCodes.Already_Randomized
      P.Close
      Exit Function
   End If
   
   ' This query returns the current group assignments associated
   ' with the factor-levels observed for the participant being
   ' randomized.
   ' The prototype query is TestReflexiveJoinQuery
   
   qSt = "SELECT ParticipantFactorLevels.FactorNumber," & _
   " Participants.GroupNumber," & _
   " Count(Participants.GroupNumber) AS Nassigned" & _
   " FROM (ParticipantFactorLevels" & _
   " INNER JOIN ParticipantFactorLevels AS ParticipantFactorLevels_1" & _
   " ON (ParticipantFactorLevels.LevelNumber = ParticipantFactorLevels_1.LevelNumber)" & _
   " AND (ParticipantFactorLevels.FactorNumber = ParticipantFactorLevels_1.FactorNumber)" & _
   " AND (ParticipantFactorLevels.ProjectNumber = ParticipantFactorLevels_1.ProjectNumber))" & _
   " INNER JOIN Participants ON (ParticipantFactorLevels_1.ProjectID = Participants.ProjectID)" & _
   " AND (ParticipantFactorLevels_1.ProjectNumber = Participants.ProjectNumber)" & _
   " WHERE ((ParticipantFactorLevels.ProjectNumber=" & CStr(pProjectNumber) & ")" & _
   " AND (ParticipantFactorLevels.ProjectID = '" & pProjectID & "')" & _
   " AND (Participants.GroupNumber > 0))" & _
   " GROUP BY ParticipantFactorLevels.FactorNumber, Participants.GroupNumber;"
   Set urnData = Dbs.OpenRecordset(qSt, dbOpenSnapshot)
   
   ' first count the number of assignments for this factor/level pattern
   ' a_Urn(i) = marginal total for Factor/Level (=urn) i
   ' a_Urn_Group(i,j) = cell count for urn i, Group j
   For i = 1 To NF
      a_Urn(i) = 0
      For j = 1 To NG
         a_Urn_Group(i, j) = 0
      Next
   Next
   N = 0
   While Not urnData.EOF
   
      a_Urn(urnData!FactorNumber) = _
         a_Urn(urnData!FactorNumber) + urnData!nassigned
         
      a_Urn_Group(urnData!FactorNumber, urnData!GroupNumber) = _
         a_Urn_Group(urnData!FactorNumber, urnData!GroupNumber) + urnData!nassigned
         
      N = N + urnData!nassigned
      
      urnData.MoveNext
   Wend
   
   ' HOW IT WORKS
   '
   ' Each urn initialzed to Alpha.
   '
   ' After each assignment, each urn associated with an observed
   ' factor-level is adjusted by adding Beta to each group
   ' other than the one selected.
   '
   ' This is expressed as follows:
   '
   ' For each factor-level(=urn) i per group j
   '   #marbles = m(i,j) = alpha + beta*(n(i)-a(i,j))
   '
   ' Sampling probability is therefore
   '
   '          alpha + beta*(n(i) - a(i,j))
   '   p(j) = -----------------------
   '          t*alpha + beta*n(i)*(t-1)
   '
   ' t = #treatment groups
   ' a(i,j) = #allocated to treatment j for given factor-level i (urn)
   '      = a_Urn_Group(i, j)
   ' n(i) = total #allocated across all groups for given urn i
   '      = a_Urn(i)
   ' alpha = initial urn state (#marbles)
   ' beta = urn adjustment after each randomization
   
   For i = 1 To NF
      If Trace Then _
         Debug.Print "-> Factor=" & i & ", Observed Level = " & a_PFL(i)
      For j = 1 To NG
         a_Marbles(i, j) = Alpha + pBeta * (a_Urn(i) - a_Urn_Group(i, j))
         If Trace Then _
            Debug.Print "-> Factor=" & i & ", Group=" & j & ", Assigned=" & a_Urn_Group(i, j) & ", Marbles=" & a_Marbles(i, j)
      Next
   Next
   
   urnData.Close
   
   ' Calculate the balance function for each urn
   ' and determine the worst balance value.
   ' Balance is determined using a Chi-Square statistic
   ' So that proportional imbalances are compared.
   
   WorstBal = 0#
   For i = 1 To NF
      a_Bal(i) = 0#
      T = CSng(a_Urn(i))
      If T > 0# Then
         E = T / CSng(NG) ' #expected in each group
         For j = 1 To NG
            a_Bal(i) = a_Bal(i) + ((CSng(a_Urn_Group(i, j)) - E) ^ 2) / E
         Next
      End If
      If a_Bal(i) >= WorstBal Then
         WorstBal = a_Bal(i)
      End If
      If Trace Then _
         Debug.Print "-> Factor=" & i & ", Balance = " & a_Bal(i)
   Next

   ' Build a list a_WorstUrn() of urn(s) having
   ' the worst imbalance found.
   nWorstBal = 0
   For i = 1 To NF
      If a_Bal(i) = WorstBal Then
         nWorstBal = nWorstBal + 1
         a_WorstUrn(nWorstBal) = i
      End If
   Next

   Randomize

   ' select the least-balanced urn
   ' easy if only one worst
   ' otherwise, select random from list
   If nWorstBal = 1 Then
      i = 1
   Else
      R = Rnd()
      i = 1 + Int(CSng(nWorstBal) * R)
   End If
   WorstUrn = a_WorstUrn(i)
   
   If Trace Then Debug.Print "--> Selected urn = " & WorstUrn
   
   ' Calculate weights for each group assignment.
   ' A large value of beta signals request for strong balance adjustment:
   ' Weight is rescaled by subtracting off the minimum (m), then  squared.
   ' This option is available only by special request, cannot be configured
   ' through gRand interface.
   
   m = 32767
   For j = 1 To NG
      If a_Marbles(WorstUrn, j) < m Then m = a_Marbles(WorstUrn, j)
   Next
   
   w = 0#
   For j = 1 To NG
      If Beta <> 32767 Then
         Wj(j) = CSng(a_Marbles(WorstUrn, j))
      Else
         Wj(j) = CSng(Alpha) + CSng(a_Marbles(WorstUrn, j) - m) ^ 2
      End If
      w = w + Wj(j)
   Next
   
   ' normalize weights to sum to 1
   For j = 1 To NG
      If w <= 0# Then
         Wj(j) = 1# / CSng(NG)
      Else
         Wj(j) = Wj(j) / w
      End If
      If Trace Then Debug.Print "--> Weight for group " & j & " is " & Wj(j)
   Next
   
   ' Finally, select the group
   R = Rnd()
   w = 0#
   G = 0
   For j = 1 To NG
      w = w + Wj(j)
      If Trace Then Debug.Print "---> R=" & R & ", cumW=" & w
      If w >= R Then
         G = j
         If Trace Then Debug.Print "----> Selected group is " & G
         Exit For
      End If
   Next
   
   ' update the global
   ' although I don't think the system uses it anymore
   gGroupNumber = G
   
   ' Save the allocation
   P.Edit
   P!GroupNumber = G
   P!RandMethod = cAlgUrn
   P!RandDate = Now()
   P!RandUser = Left$(gUserName, 24)
   P.Update
   
   P.Close
   
   ' Audit entry
   
   If Beta = 32767 Then
      EnterAudit "Urn (strong correction): " & pProjectID & " randomized into group #" & G & "."
      Alert "Note: Strong imbalance correction applied."
   Else
      EnterAudit "Urn: " & pProjectID & " randomized into group #" & G & "."
   End If
   
   URandomize = 0
   
End Function

Function RanAssign(ByVal pProjectNumber As Integer, ByVal pProjectID As String, ByVal pGroupNumber As Integer) As Integer
   Dim St As String
   Dim F As Integer, G As Integer
   Dim ErrCnt As Integer
   Dim Rst As DAO.Recordset
   Dim Alpha As Integer, Beta As Integer
   
   RanAssign = 0
   
   St = "SELECT ParticipantFactorLevels.*, Factors.nLevels" & _
   " FROM ParticipantFactorLevels INNER JOIN Factors ON" & _
   " (ParticipantFactorLevels.FactorNumber = Factors.FactorNumber) AND" & _
   " (ParticipantFactorLevels.ProjectNumber = Factors.ProjectNumber)" & _
   " WHERE (((ParticipantFactorLevels.ProjectNumber) = " & pProjectNumber & ") And" & _
   " ((ParticipantFactorLevels.ProjectID) = '" & pProjectID & "'))" & _
   " ORDER BY ParticipantFactorLevels.FactorNumber;"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   
   ErrCnt = 0
   gRandStratum = 1
   If Trace Then Debug.Print "** RanAssign **"
   For F = 1 To gnFactors
      If Nz(Rst!LevelNumber, 0) < 1 Or Nz(Rst!LevelNumber) > Rst!nLevels Then
         ErrCnt = ErrCnt + 1
      End If
      Rst.MoveNext
   Next F
   Rst.Close
   
   If ErrCnt > 0 Then
      RanAssign = RanErrCodes.Participant_Factor
      GoTo Handled_Err_RanAssign
   End If
   
   ' make sure not already assigned
   G = Nz(DFirst("GroupNumber", "Participants", "ProjectNumber=" & pProjectNumber & " AND ProjectID='" & pProjectID & "'"), 0)
   If G > 0 Then
      RanAssign = RanErrCodes.Already_Randomized
      GoTo Handled_Err_RanAssign
   End If
      
   If pGroupNumber > 0 Then
   
      ' Force-randomize
      St = "UPDATE Participants SET" & _
      " Participants.RandDate = #" & Format$(Date, "mm/dd/yyyy hh:nn") & "#," & _
      " Participants.RandUser = '" & gUserName & "'," & _
      " Participants.GroupNumber = " & pGroupNumber & "," & _
      " Participants.RandMethod = 0" & _
      " WHERE ((ProjectNumber=" & pProjectNumber & ")" & _
      " AND (ProjectID='" & pProjectID & "'));"
   
      DoCmd.RunSQL St
      
      EnterAudit pProjectID & " forced into group #" & pGroupNumber & "."
      
   Else
   
      Select Case gRAlg
      Case cAlgPermuted
         RanAssign = PRandomize(gProjectNumber, pProjectID)
      Case cAlgUrn
         Alpha = 1
         If StrongCorrection(pProjectNumber) = False Then
            Beta = 1
         Else
            Beta = 32767
         End If
         RanAssign = URandomize(gProjectNumber, pProjectID, Alpha, Beta)
      Case Else
         RanAssign = 32767
      End Select
      
   End If
   
   If RanAssign <> 0 Then
   
      GoTo Handled_Err_RanAssign
      
   Else
   
      ' Fix the factor levels at randomization
      St = "UPDATE ParticipantFactorLevels SET" & _
      " ParticipantFactorLevels.RanLevel = [ParticipantFactorLevels].[levelnumber]" & _
      " WHERE (((ParticipantFactorLevels.ProjectNumber)=" & gProjectNumber & ") AND" & _
      " ((ParticipantFactorLevels.ProjectID)='" & pProjectID & "'));"
      
      DoCmd.RunSQL St
   
   End If
   
End_RanAssign:
   Exit Function
   
Handled_Err_RanAssign:
      Alert RanErrCodeMessage(RanAssign)
      GoTo End_RanAssign

End Function

Function GetPerms() As Integer
   Dim Rst As Recordset, St As String
   
   gCanRead = True
   gCanWrite = True
   gCanRandomize = True
   gCanAddSubjects = True
   gSuperUser = True
   
   Exit Function
      
   St = "SELECT * FROM UserProjectBridge WHERE" & _
      " UserProjectBridge.UserName='" & gUserName & "' And" & _
      " UserProjectBridge.ProjectNumber=" & gProjectNumber & ";"
      
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   
   If Rst.BOF Then
      gCanRead = False
      gCanWrite = False
      gCanRandomize = False
      gCanAddSubjects = False
   Else
      gCanRead = Rst!CanRead
      gCanWrite = Rst!Canwrite
      gCanRandomize = Rst!CanRandomize
      gCanAddSubjects = Rst!Canaddsubjects
   End If
   
   Rst.Close
End Function
Function LoadProject(ByVal pProjectNumber As Integer)
   Dim Rst As Recordset
   Set Rst = CurrentDb.OpenRecordset( _
      "SELECT * FROM Projects WHERE Projects.ProjectNumber=" & pProjectNumber, _
      dbOpenDynaset)
   If Rst.EOF Then
      gProjectNumber = 0
   Else
      gProjectNumber = pProjectNumber
      If Not IsNull(Rst!ProjectName) Then gProjectName = Rst!ProjectName Else gProjectName = ""
      If Not IsNull(Rst!RAlg) Then gRAlg = Rst!RAlg Else gRAlg = 0
      If Not IsNull(Rst!BlockSize) Then gBlockSize = Rst!BlockSize Else gBlockSize = 0
      If Not IsNull(Rst!nGroups) Then gnGroups = Rst!nGroups Else gnGroups = 0
      If Not IsNull(Rst!nFactors) Then gnFactors = Rst!nFactors Else gnFactors = 0
      If Not IsNull(Rst!SLevels) Then gSLevels = Rst!SLevels Else gSLevels = 0
      If Not IsNull(Rst!PLevels) Then gPLevels = Rst!PLevels Else gPLevels = 0
      If Not IsNull(Rst!ProjectIDType) Then gProjectIDType = Rst!ProjectIDType Else gProjectIDType = 0
      If Not IsNull(Rst!ProjectIDWidth) Then gProjectIDWidth = Rst!ProjectIDWidth Else gProjectIDWidth = 0
   End If
   Rst.Close
   SaveState
End Function

Function MakeFactorLevels(ByVal pProjectNumber As Integer, ByVal pProjectID As String)
   Dim St As String, Fac As Recordset, FacLev As Recordset, Prj As Recordset, i As Integer
   St = "SELECT * FROM Projects WHERE Projects.ProjectNumber=" & pProjectNumber & ";"
   Set Prj = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   St = "SELECT * FROM ParticipantFactorLevels WHERE" & _
      " ParticipantFactorLevels.ProjectNumber=" & pProjectNumber & " And" & _
      " ParticipantFactorLevels.ProjectID='" & pProjectID & "';"
   Set FacLev = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   For i = 1 To Prj!nFactors
      FacLev.FindFirst "FactorNumber=" & i
      If FacLev.NoMatch Then
         FacLev.AddNew
         FacLev!ProjectNumber = pProjectNumber
         FacLev!ProjectID = pProjectID
         FacLev!FactorNumber = i
         FacLev!LevelNumber = 0
         FacLev.Update
      End If
   Next i
   Prj.Close
   FacLev.Close
End Function

Function MakeLevelTables(ByVal pProjectNumber As Integer)
   Dim Rst As Recordset, PF As Integer, St As String
   St = "SELECT Levels.FactorNumber, Levels.LevelNumber, Levels.LevelName, Factors.LevelTable" & _
   " FROM Factors INNER JOIN Levels ON (Factors.FactorNumber = Levels.FactorNumber) AND" & _
   " (Factors.ProjectNumber = Levels.ProjectNumber)" & _
   " WHERE (((Levels.ProjectNumber) = " & pProjectNumber & "))" & _
   " ORDER BY Levels.FactorNumber, Levels.LevelNumber;"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   PF = -1
   Do While Not Rst.EOF
      Rst.Edit
      If PF <> Rst!FactorNumber Then
         Rst!LevelTable = ""
         PF = Rst!FactorNumber
      End If
      Rst!LevelTable = Left$(Rst!LevelTable & Rst!LevelNumber & "-" & Rst!LevelName & vbCrLf, 250)
      Rst.Update
      Rst.MoveNext
   Loop
   Rst.Close
End Function

Function ProjName(ByVal pProjectNumber As Integer) As String
   Dim Rst As Recordset
   Set Rst = CurrentDb.OpenRecordset("SELECT * FROM Projects WHERE Projects.ProjectNumber=" & pProjectNumber & ";", dbOpenDynaset)
   If Rst.BOF Then
      ProjName = ""
   Else
      ProjName = Rst!ProjectName
   End If
   Rst.Close
End Function

Function MakeLevels( _
   ByVal pProjectNumber As Integer, _
   ByVal pFactorNumber As Integer, _
   ByVal pnLevels As Integer)
   Dim St As String, Rst As Recordset, i As Integer
   DoCmd.SetWarnings False
   St = "DELETE * FROM Levels WHERE Levels.ProjectNumber=" & _
      pProjectNumber & " And Levels.FactorNumber=" & _
      pFactorNumber & " And Levels.LevelNumber > " & pnLevels & ";"
   DoCmd.RunSQL St
   St = "SELECT * FROM Levels WHERE Levels.ProjectNumber=" & _
      pProjectNumber & " And Levels.FactorNumber=" & _
      pFactorNumber & ";"
   Set Rst = CurrentDb.OpenRecordset(St, dbOpenDynaset)
   For i = 1 To pnLevels
      Rst.FindFirst "[LevelNumber]=" & i
      If Rst.NoMatch Then
         Rst.AddNew
         Rst!ProjectNumber = pProjectNumber
         Rst!FactorNumber = pFactorNumber
         Rst!LevelNumber = i
         Rst!LevelName = "Level " & Format$(i, "00")
         Rst.Update
      End If
   Next i
   DoCmd.SetWarnings True
End Function

Function MakeGroupNames( _
   ByVal pProjectNumber As Integer, _
   ByVal pnGroups As Integer)
   Dim St As String, Rst As Recordset, i As Integer
   DoCmd.SetWarnings False
   St = "DELETE * FROM GroupNames WHERE GroupNames.ProjectNumber=" & pProjectNumber & ";"
   DoCmd.SetWarnings True
   DoCmd.RunSQL St
   Set Rst = CurrentDb.OpenRecordset("GroupNames", dbOpenDynaset)
   For i = 1 To pnGroups
      Rst.AddNew
      Rst!ProjectNumber = pProjectNumber
      Rst!GroupNumber = i
      Rst!GroupName = "Treatment Group " & Format$(i, "00")
      Rst.Update
   Next i
End Function

Function EnterAudit(ByVal pAuditEntryMessage As String) As Integer
   Dim St As String, VarRc As Variant
   St = "INSERT INTO AuditEntries ( ProjectNumber, AuditEntryMessage, AuditEntryDate )" & _
   " SELECT " & gProjectNumber & " AS Expr0, '" & pAuditEntryMessage & "' AS Expr1, Now() AS Expr2;"
   DoCmd.RunSQL St
   VarRc = SysCmd(acSysCmdSetStatus, "Audit entered: " & pAuditEntryMessage)
End Function

Function LinkTbl(ByVal Tbl As String) As Boolean
   On Error Resume Next
   DoCmd.RunSQL "DROP TABLE " & Tbl & ";"
   On Error GoTo errLinkTbl
   
   DoCmd.TransferDatabase A_ATTACH, "Microsoft Access", _
      gDataFolder & "gRdata.mdb", A_TABLE, Tbl, Tbl
      
   LinkTbl = True
   
endLinkTbl:
   Exit Function
   
errLinkTbl:
   LinkTbl = False
   Resume endLinkTbl

End Function

Function AppStartup() As Integer
   Dim i As Integer, perms As Long
   
   On Error GoTo error_Startup
   
   i = InStr(UCase$(CurrentDb.Name), gAppName)
   If i = 0 Then
      ReturnCode = err_Startup
      GoTo exit_Startup
   End If
   
   gHomeFolder = Left$(CurrentDb.Name, i - 1)
   
   gDataFolder = gHomeFolder
   
   Application.SetOption "Confirm Action Queries", False
   
   LinkTbl "AuditEntries"
   LinkTbl "Factors"
   LinkTbl "GroupNames"
   LinkTbl "Levels"
   LinkTbl "ParticipantFactorLevels"
   LinkTbl "Participants"
   LinkTbl "Projects"
   
   Randomize
        
exit_Startup:
   'If iPCP And iMembers And iHPQ And iAlertPostings And iAlertNumbers And _
   '   iStaff And iPIC_Calls And iCRS Then
   '   ReturnCode = 0
   'Else
      ReturnCode = err_Startup
   'End If
   AppStartup = ReturnCode
   Exit Function
   
error_Startup:
   Alert "ERROR IN APPLICATION STARTUP. Error message: " & Err.Description
   ReturnCode = err_Startup
   Resume exit_Startup
   
End Function

Function AppShutdown()
   
   On Error Resume Next
   DoCmd.RunSQL "DROP TABLE AuditEntries"
   DoCmd.RunSQL "DROP TABLE Factors"
   DoCmd.RunSQL "DROP TABLE GroupNames"
   DoCmd.RunSQL "DROP TABLE Levels"
   DoCmd.RunSQL "DROP TABLE ParticipantFactorLevels"
   DoCmd.RunSQL "DROP TABLE Participants"
   DoCmd.RunSQL "DROP TABLE Projects"
   On Error GoTo 0
   
End Function
Function NameCase(ByVal pSt As String) As String
   Dim S As String, T As String, i As Integer, _
      L As Integer, _
      Ch As String * 1, pCh As String * 1
   
   S = Trim$(pSt)
   If Left$(S, 4) = "APT " Then
      NameCase = "Apt " & UCase$(Mid$(S, 5))
      Exit Function
   End If
      
   T = ""
   pCh = " "
   L = Len(S)
   
   For i = 1 To L
      Ch = Mid$(S, i, 1)
      If pCh = " " Or pCh = "," Then
         Ch = UCase$(Ch)
      Else
         Ch = LCase$(Ch)
      End If
      T = T & Ch
      pCh = Ch
   Next i
   
   NameCase = T
   
End Function
