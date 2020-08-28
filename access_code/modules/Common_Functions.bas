Attribute VB_Name = "Common_Functions"
Option Compare Database
Option Explicit

Const APPNAME = "gRand"

Function PadR(ByVal St As String, ByVal N As Integer, ByVal Ch As String) As String
   Dim i As Integer, L As Integer
   PadR = Trim$(St)
   L = Len(PadR)
   While L < N
      PadR = PadR & Ch
      L = L + 1
   Wend
End Function

Function PadL(ByVal St As String, ByVal N As Integer, ByVal Ch As String) As String
   Dim i As Integer, L As Integer
   PadL = Trim$(St)
   L = Len(PadL)
   While L < N
      PadL = Ch & PadL
      L = L + 1
   Wend
End Function

Function Twips(ByVal X As Single) As Single
   Twips = X * 1440#
End Function

Function SetMask(X As Long, i As Integer) As Long
   SetMask = X Or 2 ^ (i - 1)
End Function

Function ResetMask(X As Long, i As Integer) As Long
   ResetMask = X And (Not 2 ^ (i - 1))
End Function

Function BitSet(X As Long, i As Integer) As Boolean
   BitSet = ((X And 2 ^ (i - 1)) > 0)
End Function

Function AgeNow(bdate As Variant, RefDate As Variant) As Variant
   Dim bmd As Integer, bY As Integer
   Dim cmd As Integer, cy As Integer
   If IsNull(bdate) Then
      AgeNow = Null
      Exit Function
   End If
   If IsNull(RefDate) Then
      AgeNow = Null
      Exit Function
   End If
   bmd = Month(bdate) * 100 + Day(bdate)
   bY = Year(bdate)
   cmd = Month(RefDate) * 100 + Day(RefDate)
   cy = Year(RefDate)
   If cmd < bmd Then
      AgeNow = cy - bY - 1
   Else
      AgeNow = cy - bY
   End If
End Function

Function FullName(pTitle As Variant, _
    pFirstname As Variant, _
    pMiddlename As Variant, _
    pLastname As Variant, _
    pJr As Variant) As Variant
   
   Dim St As String
   
   St = ""
   
   If Not IsNull(pTitle) Then St = pTitle & " "
   If Not IsNull(pFirstname) Then St = St & pFirstname & " "
   If Not IsNull(pMiddlename) Then St = St & pMiddlename & " "
   If Not IsNull(pLastname) Then St = St & pLastname
   If Not IsNull(pJr) Then St = St & ", " & pJr
   
   If Len(St) > 0 Then
      FullName = St
   Else
      FullName = Null
   End If
   
End Function

Function FullAddressAndTelephone( _
    pInstitution As Variant, _
    pStreet As Variant, _
    pCity As Variant, _
    pState As Variant, _
    pZip As Variant, _
    pTelephone As Variant) As Variant
   
   Dim St As String
   
   St = ""
   If Not IsNull(pInstitution) Then St = pInstitution & vbCrLf
   If Not IsNull(pStreet) Then St = St & pStreet & vbCrLf
   If Not IsNull(pCity) Then St = St & pCity
   If Not IsNull(pState) Then St = St & ", " & pState
   If Not IsNull(pZip) Then St = St & "  " & pZip
   If Not IsNull(pTelephone) Then
      If Len(St) = 0 Then
         St = pTelephone
      Else
         St = St & vbCrLf & pTelephone
      End If
   End If
    
   If Len(St) > 0 Then
      FullAddressAndTelephone = St
   Else
      FullAddressAndTelephone = Null
   End If

   End Function
   
Function FullAddress( _
    pInstitution As Variant, _
    pStreet As Variant, _
    pCity As Variant, _
    pState As Variant, _
    pZip As Variant _
   ) As Variant
   
   Dim St As String
   
   St = ""
   If Not IsNull(pInstitution) Then St = pInstitution & vbCrLf
   If Not IsNull(pStreet) Then St = St & pStreet & vbCrLf
   If Not IsNull(pCity) Then St = St & pCity
   If Not IsNull(pState) Then St = St & ", " & pState
   If Not IsNull(pZip) Then St = St & "  " & pZip
    
   If Len(St) > 0 Then
      FullAddress = St
   Else
      FullAddress = Null
   End If

   End Function


Function ReplaceSt(pSt As String, PS As String, pR As String) As String
   Dim i As Integer, j As Integer, L As Integer, St As String, pSrc As String
   Dim Z As String
   
   If PS = pR Then
      ReplaceSt = pSt
      Exit Function
   End If
   
   St = ""
   Z = PS
   pSrc = pSt
   L = Len(pSrc)
   i = InStr(1, pSrc, Z)
   If i = 0 Then
      ReplaceSt = pSt
      Exit Function
   End If
   
   Do While i > 0
      If i = 1 Then
         St = pR & Mid$(pSrc, Len(Z) + 1)
      Else
         If i >= 1 + Len(pSrc) - Len(Z) Then
            pSrc = Left$(pSrc, i - 1) & pR
         Else
            pSrc = Left$(pSrc, i - 1) & pR & Mid$(pSrc, i + Len(Z))
         End If
      End If
      i = InStr(pSrc, Z)
   Loop
   
   ReplaceSt = pSrc
End Function
Function IsNumOrAlpha(pCh As Variant) As Boolean
   If IsNull(pCh) Then
      IsNumOrAlpha = False
   Else
      IsNumOrAlpha = (InStr("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", UCase$(pCh)) > 0)
   End If
End Function

Function Sanitized(pSrc As Variant) As Variant
   Dim Tgt As String, i As Integer, Ch As String * 1
   If IsNull(pSrc) Then
      Sanitized = Null
      Exit Function
   End If
   Tgt = ""
   For i = 1 To Len(pSrc)
      Ch = Mid$(pSrc, i, 1)
      If Not IsNumOrAlpha(Ch) Then
         Tgt = Tgt & "_"
      Else
         Tgt = Tgt & Ch
      End If
   Next i
   Sanitized = Tgt
End Function

Function InsertString(S1 As Variant, s2 As String) As Variant
   Dim T As Variant
   T = S1
   If IsNull(T) Then
      T = s2
   Else
      If Len(S1) = 0 Then
         T = s2
      Else
         T = T & vbCrLf & s2
      End If
   End If
   InsertString = T
End Function

Function RemoveString(S1 As Variant, s2 As String) As Variant
   Dim i As Integer, T As Variant
   T = S1
   If Not IsNull(T) Then
      If Len(T) > 0 Then
         i = InStr(T, s2)
         If i > 0 Then
            If i = 1 Then
               T = Mid$(T, Len(s2) + 1)
            Else
               T = Left$(T, i - 1) & Mid$(T, i + Len(s2))
            End If
         End If
         i = Len(T)
         If i > 0 Then
            Do While i > 0 And Asc(Mid$(T, i, 1)) < Asc(" ")
               T = Left$(T, i - 1)
               i = i - 1
            Loop
         End If
         If Len(T) = 0 Then T = Null
      End If
   End If
   RemoveString = T
End Function

Function NameCase(pSt As String) As String
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
Public Function Alert(msg As String)
   MsgBox msg, vbOKOnly + vbExclamation, APPNAME
End Function
Public Function AlertBang(msg As String)
   MsgBox msg, vbOKOnly + vbExclamation, APPNAME
End Function
Public Function alertinfo(msg As String)
   MsgBox msg, vbOKOnly + vbInformation, APPNAME
End Function
Public Function Question(msg As String) As Integer
   Dim i As Integer, zTitle As String
   i = MsgBox(msg, vbOKCancel + vbQuestion, APPNAME)
   If i = vbOK Then
      Question = True
   Else
      Question = False
   End If
End Function
Public Function YesNo(msg As String) As Boolean
   Dim i As Integer
   i = MsgBox(msg, vbYesNo + vbQuestion, APPNAME)
   If i = vbYes Then
      YesNo = True
   Else
      YesNo = False
   End If
End Function
Public Function SaveCurrentRecord()
   On Error Resume Next
   DoCmd.DoMenuItem acFormBar, acRecordsMenu, acSaveRecord, , acMenuVer70
End Function
Function EQ(x1 As Variant, x2 As Variant) As Boolean
   If IsNull(x1) <> IsNull(x2) Then
      EQ = False
   Else
      If IsNull(x1) Then
         EQ = True
      Else
         If x1 = x2 Then
            EQ = True
         Else
            EQ = False
         End If
      End If
   End If
End Function
Function NEQ(x1 As Variant, x2 As Variant) As Boolean
   NEQ = Not EQ(x1, x2)
End Function
Function GT(x1 As Variant, x2 As Variant) As Boolean
   If IsNull(x1) And IsNull(x2) Then
      GT = False
      Exit Function
   End If
   If IsNull(x2) Then
      GT = True
      Exit Function
   End If
   If IsNull(x1) Then
      GT = False
      Exit Function
   End If
   GT = (x1 > x2)
End Function
Function GE(x1 As Variant, x2 As Variant) As Boolean
   If IsNull(x1) And IsNull(x2) Then
      GE = True
      Exit Function
   End If
   If IsNull(x2) Then
      GE = True
      Exit Function
   End If
   If IsNull(x1) Then
      GE = False
      Exit Function
   End If
   GE = (x1 >= x2)
End Function
Function FileOk(pFilename As String) As Boolean
   FileOk = (Dir(pFilename) <> "")
End Function

