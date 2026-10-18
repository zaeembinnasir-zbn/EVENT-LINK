@echo off
title EventLink Firewall Setup
netsh advfirewall firewall add rule name="EventLink Local 8765" dir=in action=allow protocol=TCP localport=8765 profile=private
pause
