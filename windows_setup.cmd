python -m venv venv
call "venv\Scripts\activate.bat"
echo should be in venv here
cd .
python -m pip install --upgrade pip

pip install json
pip install shutil
pip install unidecode


GOTO :eof



:ERROR
echo Something blew up. Make sure Pyton 3.10.x is installed and in your PATH.

:eof
ECHO done
pause
