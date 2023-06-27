#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

GetActiveExplorerPath()
{
    explorerHwnd := WinActive("ahk_class CabinetWClass")
    if (explorerHwnd)
    {
        for window in ComObjCreate("Shell.Application").Windows
        {
            if (window.hwnd==explorerHwnd)
            {
                return window.Document.Folder.Self.Path
            }
        }
    }
}

#IfWinActive ahk_exe Explorer.exe
.::
path := GetActiveExplorerPath()
run, "C:\Users\USERNAME\AppData\Local\Programs\Microsoft VS Code\bin\code" "%path%"
return