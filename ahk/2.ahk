#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
#IfWinActive  		; this will be active in any window, but I recommend adding the name of your game that is visible with the Window Spy tool by right clicking on the Autohotkey script toolbar icon
#MaxThreadsPerHotkey 255

$XButton1::
	while GetKeyState("XButton1", "p")
	{
		Send {WheelUp}
		Sleep, 10
	}
	Return

