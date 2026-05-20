' ============================================================
'  Steel Connections - Standalone Bootstrapper
' ============================================================
'  Double-click this file on any Windows PC to:
'    1. Choose install folder
'    2. Clone repo (or download ZIP if Git is missing)
'    3. Run install.bat for automated setup
' ============================================================

Option Explicit

Dim objShell, objFSO
Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

Const REPO_URL = "https://github.com/ebrahimraeyat/steel-connections.git"
Const ZIP_URL  = "https://github.com/ebrahimraeyat/steel-connections/archive/refs/heads/master.zip"
Const FOLDER   = "steel-connections"

Dim defaultPath
defaultPath = objShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Documents"

Dim psTempFile
psTempFile = objShell.ExpandEnvironmentStrings("%TEMP%") & "\steel_connections_folder_picker.ps1"

Dim psFile
Set psFile = objFSO.CreateTextFile(psTempFile, True)
psFile.WriteLine "Add-Type -AssemblyName System.Windows.Forms"
psFile.WriteLine "Add-Type -AssemblyName System.Drawing"
psFile.WriteLine "[System.Windows.Forms.Application]::EnableVisualStyles()"
psFile.WriteLine "$form = New-Object System.Windows.Forms.Form"
psFile.WriteLine "$form.Text = 'Steel Connections Installer'"
psFile.WriteLine "$form.Size = New-Object System.Drawing.Size(560, 210)"
psFile.WriteLine "$form.StartPosition = 'CenterScreen'"
psFile.WriteLine "$form.FormBorderStyle = 'FixedDialog'"
psFile.WriteLine "$form.MaximizeBox = $false"
psFile.WriteLine "$form.MinimizeBox = $false"
psFile.WriteLine "$form.TopMost = $true"
psFile.WriteLine "$lbl = New-Object System.Windows.Forms.Label"
psFile.WriteLine "$lbl.Text = 'Select folder to install Steel Connections:'"
psFile.WriteLine "$lbl.Location = New-Object System.Drawing.Point(12, 15)"
psFile.WriteLine "$lbl.AutoSize = $true"
psFile.WriteLine "$form.Controls.Add($lbl)"
psFile.WriteLine "$lbl2 = New-Object System.Windows.Forms.Label"
psFile.WriteLine "$lbl2.Text = '(A subfolder named ""steel-connections"" will be created inside it)'"
psFile.WriteLine "$lbl2.Location = New-Object System.Drawing.Point(12, 38)"
psFile.WriteLine "$lbl2.AutoSize = $true"
psFile.WriteLine "$lbl2.ForeColor = [System.Drawing.Color]::Gray"
psFile.WriteLine "$form.Controls.Add($lbl2)"
psFile.WriteLine "$txt = New-Object System.Windows.Forms.TextBox"
psFile.WriteLine "$txt.Text = '" & defaultPath & "'"
psFile.WriteLine "$txt.Location = New-Object System.Drawing.Point(12, 65)"
psFile.WriteLine "$txt.Size = New-Object System.Drawing.Size(430, 24)"
psFile.WriteLine "$form.Controls.Add($txt)"
psFile.WriteLine "$btnBrowse = New-Object System.Windows.Forms.Button"
psFile.WriteLine "$btnBrowse.Text = 'Browse...'"
psFile.WriteLine "$btnBrowse.Location = New-Object System.Drawing.Point(448, 63)"
psFile.WriteLine "$btnBrowse.Size = New-Object System.Drawing.Size(90, 27)"
psFile.WriteLine "$btnBrowse.Add_Click({"
psFile.WriteLine "  $fbd = New-Object System.Windows.Forms.FolderBrowserDialog"
psFile.WriteLine "  $fbd.Description = 'Select installation folder'"
psFile.WriteLine "  $fbd.SelectedPath = $txt.Text"
psFile.WriteLine "  $fbd.ShowNewFolderButton = $true"
psFile.WriteLine "  if ($fbd.ShowDialog() -eq 'OK') { $txt.Text = $fbd.SelectedPath }"
psFile.WriteLine "})"
psFile.WriteLine "$form.Controls.Add($btnBrowse)"
psFile.WriteLine "$btnOK = New-Object System.Windows.Forms.Button"
psFile.WriteLine "$btnOK.Text = 'Install'"
psFile.WriteLine "$btnOK.Location = New-Object System.Drawing.Point(300, 115)"
psFile.WriteLine "$btnOK.Size = New-Object System.Drawing.Size(110, 32)"
psFile.WriteLine "$btnOK.DialogResult = [System.Windows.Forms.DialogResult]::OK"
psFile.WriteLine "$form.Controls.Add($btnOK)"
psFile.WriteLine "$form.AcceptButton = $btnOK"
psFile.WriteLine "$btnCancel = New-Object System.Windows.Forms.Button"
psFile.WriteLine "$btnCancel.Text = 'Cancel'"
psFile.WriteLine "$btnCancel.Location = New-Object System.Drawing.Point(420, 115)"
psFile.WriteLine "$btnCancel.Size = New-Object System.Drawing.Size(110, 32)"
psFile.WriteLine "$btnCancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel"
psFile.WriteLine "$form.Controls.Add($btnCancel)"
psFile.WriteLine "$form.CancelButton = $btnCancel"
psFile.WriteLine "$result = $form.ShowDialog()"
psFile.WriteLine "if ($result -eq 'OK') { Write-Host $txt.Text } else { Write-Host '::CANCEL::' }"
psFile.Close
Set psFile = Nothing

Dim psPath
psPath = objShell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"

Dim installDir, psExec
Set psExec = objShell.Exec("""" & psPath & """ -NoProfile -ExecutionPolicy Bypass -File """ & psTempFile & """")
installDir = psExec.StdOut.ReadAll
Set psExec = Nothing

installDir = Replace(installDir, vbCrLf, "")
installDir = Replace(installDir, vbCr, "")
installDir = Replace(installDir, vbLf, "")
installDir = Trim(installDir)

On Error Resume Next
objFSO.DeleteFile psTempFile, True
On Error GoTo 0

If installDir = "" Or installDir = "::CANCEL::" Then WScript.Quit

If Not objFSO.FolderExists(installDir) Then
    MsgBox "The folder """ & installDir & """ does not exist.", vbExclamation, "Error"
    WScript.Quit
End If

Dim targetPath
targetPath = installDir & "\" & FOLDER

If objFSO.FolderExists(targetPath) Then
    Dim overwrite
    overwrite = MsgBox( _
        "The folder """ & targetPath & """ already exists." & vbCrLf & _
        "Do you want to update it instead of downloading again?", _
        vbYesNoCancel + vbQuestion, "Folder Exists")

    If overwrite = vbCancel Then WScript.Quit

    If overwrite = vbYes Then
        Dim updateBat
        updateBat = targetPath & "\update.bat"
        If objFSO.FileExists(updateBat) Then
            objShell.CurrentDirectory = targetPath
            objShell.Run "cmd /k """ & updateBat & """", 1, False
        Else
            MsgBox "update.bat not found in " & targetPath, vbExclamation, "Error"
        End If
        WScript.Quit
    End If

    objFSO.DeleteFolder targetPath, True
End If

Dim hasGit, cloneOK
hasGit = False
cloneOK = False

On Error Resume Next
Dim gitTestResult
gitTestResult = objShell.Run("cmd /c git --version", 0, True)
If Err.Number = 0 And gitTestResult = 0 Then hasGit = True
Err.Clear
On Error GoTo 0

If hasGit Then
    Dim cloneCmd, cloneResult
    cloneCmd = "cmd /c cd /d """ & installDir & """ && git clone --depth=1 " & REPO_URL
    cloneResult = objShell.Run(cloneCmd, 1, True)
    If cloneResult = 0 And objFSO.FolderExists(targetPath) Then cloneOK = True
End If

If Not cloneOK Then
    Dim zipPath
    zipPath = objShell.ExpandEnvironmentStrings("%TEMP%") & "\steel-connections.zip"

    Dim dlMsg, dlResult
    dlMsg = "Downloading Steel Connections as ZIP ..."
    If Not hasGit Then
        dlMsg = "Git not found. " & dlMsg
    End If

    dlResult = MsgBox(dlMsg & vbCrLf & vbCrLf & "Click OK to continue.", _
        vbOKCancel + vbInformation, "Downloading")
    If dlResult = vbCancel Then WScript.Quit

    Dim psDownload
    psDownload = """" & psPath & """ -NoProfile -Command ""& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '" & ZIP_URL & "' -OutFile '" & zipPath & "' }"""
    objShell.Run psDownload, 0, True

    If Not objFSO.FileExists(zipPath) Then
        MsgBox "Download failed. Please check your internet connection.", vbCritical, "Error"
        WScript.Quit
    End If

    Dim extractDir
    extractDir = objShell.ExpandEnvironmentStrings("%TEMP%") & "\steel-connections-extract"
    If objFSO.FolderExists(extractDir) Then objFSO.DeleteFolder extractDir, True

    Dim psExtract
    psExtract = """" & psPath & """ -NoProfile -Command ""Expand-Archive -Path '" & zipPath & "' -DestinationPath '" & extractDir & "' -Force"""
    objShell.Run psExtract, 0, True

    Dim subFolder, f
    subFolder = ""
    For Each f In objFSO.GetFolder(extractDir).SubFolders
        subFolder = f.Path
        Exit For
    Next

    If subFolder = "" Or Not objFSO.FolderExists(subFolder) Then
        MsgBox "Failed to extract the downloaded ZIP file.", vbCritical, "Error"
        WScript.Quit
    End If

    objFSO.MoveFolder subFolder, targetPath

    On Error Resume Next
    objFSO.DeleteFile zipPath, True
    objFSO.DeleteFolder extractDir, True
    On Error GoTo 0
End If

Dim installBat
installBat = targetPath & "\install.bat"

If Not objFSO.FileExists(installBat) Then
    MsgBox "install.bat not found in " & targetPath & vbCrLf & _
           "Download may be incomplete.", vbCritical, "Error"
    WScript.Quit
End If

MsgBox "Download complete!" & vbCrLf & vbCrLf & _
    "Click OK to start automated setup." & vbCrLf & _
    "A terminal window will open - this is normal.", _
    vbInformation, "Steel Connections"

objShell.CurrentDirectory = targetPath
objShell.Run "cmd /k """ & installBat & """", 1, False

Set objFSO   = Nothing
Set objShell = Nothing
