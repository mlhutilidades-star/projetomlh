Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & WScript.ScriptFullName & "\..\Iniciar_Hub_Financeiro.bat" & Chr(34), 0
Set WshShell = Nothing
