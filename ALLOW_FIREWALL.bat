@echo off
title EventLink Local Firewall Setup
echo This needs Administrator permission.
netsh advfirewall firewall add rule name="EventLink Local TCP 8765" dir=in action=allow protocol=TCP localport=8765 profile=private
echo.
echo Firewall rule created.
pause
