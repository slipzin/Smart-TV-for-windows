@echo off
rem Smart TV para Windows: abre a tela inicial de TV em tela cheia.
rem Sair: segure View + Menu no controle, ou aperte Alt+F4.
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0sistema\tv.ps1"
