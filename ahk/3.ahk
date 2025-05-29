#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

;+2::BackSpace ;tilde
;capslock::enter


+WheelDown::WheelRight
+WHeelUp::WHeelLeft

;XButton1::Send {WheelUp 5}	

;XButton2::Send {WheelDown 5}
#IfWinActive  		; this will be active in any window, but I recommend adding the name of your game that is visible with the Window Spy tool by right clicking on the Autohotkey script toolbar icon
#MaxThreadsPerHotkey 3


; !Down::Send {Volume_Down}
; !Up::Send {Volume_Up}

$PgDn::
  Loop
  { Send {WheelDown}
    sleep 10
    If (!GetKeyState("PgDn","p"))
      break
  }
  Return

$PgUp::
  Loop
  { Send {WheelUp}
    sleep 10
    If (!GetKeyState("PgUp","p"))
      break
  }
  Return
$XButton1::
	while GetKeyState("XButton1", "P")
	{
		Send {WheelUp}
		Sleep, 10
	}
	Return

$XButton2::
	while GetKeyState("XButton2", "P")
	{
		Send {WheelDown}
		Sleep, 10
	}
	Return

$NumpadPgUp::
  Loop
  { Send {WheelUp}
    sleep 10
    If (!GetKeyState("NumpadPgUp","p"))
      break
  }
  Return
$NumpadHome::
  Loop
  { Send {WheelDown}
    sleep 10
    If (!GetKeyState("NumpadHome","p"))
      break
  }
  Return

$NumpadUp::
	while GetKeyState("NumpadUp", "P")
	{
		Send {Up}
		Sleep, 30
	}
	Return

$NumpadClear::
	while GetKeyState("NumpadClear", "P")
	{
		Send {Down}
		Sleep, 30
	}
	Return

$NumpadDown::
	while GetKeyState("NumpadDown", "P")
	{
		Send {Down}
		Sleep, 30
	}
	Return
$NumpadLeft::
	while GetKeyState("NumpadLeft", "P")
	{
		Send {Left}
		Sleep, 30
	}
	Return
$NumpadRight::
	while GetKeyState("NumpadRight", "P")
	{
		Send {Right}
		Sleep, 30
	}
	Return