# PowerShell script to create ECHO desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\ECHO Radiology AI.lnk")
$Shortcut.TargetPath = "C:\Users\Patrick\radiology-ai-assistant\launch_echo.bat"
$Shortcut.WorkingDirectory = "C:\Users\Patrick\radiology-ai-assistant"
$Shortcut.Description = "ECHO - Radiology CORE AI Assistant"
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully!"
Write-Host "You can now right-click the shortcut and 'Pin to taskbar' or 'Pin to Start'"