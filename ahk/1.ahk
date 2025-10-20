#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
#IfWinActive  		; this will be active in any window, but I recommend adding the name of your game that is visible with the Window Spy tool by right clicking on the Autohotkey script toolbar icon
#MaxThreadsPerHotkey 2


+WheelDown::WheelRight
+WHeelUp::WHeelLeft

;VOLUME faster
^Down::Send {Volume_Down 2}
^Up::Send {Volume_Up 2}

;VOLUME precise
;^Down::Send {Volume_Down}
;^Up::Send {Volume_Up}

CapsLock::Enter
$XButton2::
	while GetKeyState("XButton2", "p")
	{
		Send {WheelDown}
		Sleep, 1
	}
	Return
vkE2::Backspace ;bubble
!vkE2::XButton1

!`::Send {Backspace}
;!vkC0::BackSpace ; tilde
;!vkC0::XButton1
; !1::XButton1
; !2::XButton2

!1::Send, #1  ; Alt+1 → Win+1
!2::Send, #2  ; Alt+2 → Win+2
!3::Send, #3
!4::Send, #4
!5::Send, #5
!6::Send, #6
!7::Send, #7
!8::Send, #8
!9::Send, #9
!e::Send, #6
!+s::Send, #+s  ; Alt+Shift+S sends Win+Shift+S
;!Up::Send, #{Up}    ; Alt+Up → Win+Up (maximize)
;!Down::Send, #{Down}  ; Alt+Down → Win+Down (restore/minimize)

